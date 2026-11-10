#!/usr/bin/env python3
"""
render_edl.py — Arma un video horizontal a partir de una EDL en JSON usando FFmpeg.

La EDL (edit decision list) es la "línea de tiempo en texto": qué planos, en qué
orden, con qué transición, qué textos, qué música/locución y cómo se masteriza.
Ver docs/edl-schema.md y examples/edl-ejemplo.json.

Uso:
    python3 tools/render_edl.py proyecto/edl.json            # master final
    python3 tools/render_edl.py proyecto/edl.json --draft    # preview rápido 960x540
    python3 tools/render_edl.py proyecto/edl.json --print    # muestra el comando ffmpeg

Rutas relativas dentro de la EDL se resuelven contra la carpeta de la EDL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"

# ---------------------------------------------------------------------------
# Estilos tipográficos derivados de las referencias (ver docs/estandar.md).
# Valores en px para un lienzo de 1080 de alto; se escalan al alto real.
# ---------------------------------------------------------------------------
STYLES = {
    # Subtítulo de locución: sans regular, blanco, centrado abajo, sombra suave.
    "subtitulo": dict(font="Inter-Regular", size=40, color="white", x="center",
                      y=1010, anchor="bottom", shadow=2, shadow_alpha=0.55,
                      fade=0.18, line_spacing=8),
    # Dato / claim: condensada, mayúsculas, a la izquierda en el tercio inferior.
    "dato": dict(font="BarlowCondensed-SemiBold", size=74, color="white", x=190,
                 y=760, anchor="top", shadow=3, shadow_alpha=0.45, fade=0.25,
                 slide=40, upper=True, line_spacing=4),
    # Zócalo de entrevista: nombre (bold) — se usa junto con "zocalo_cargo".
    "zocalo_nombre": dict(font="BarlowCondensed-Bold", size=56, color="white",
                          x=190, y=850, anchor="top", shadow=2, shadow_alpha=0.5,
                          fade=0.25, slide=30, upper=True),
    "zocalo_cargo": dict(font="Inter-Light", size=32, color="white@0.92", x=192,
                         y=915, anchor="top", shadow=2, shadow_alpha=0.5,
                         fade=0.25, slide=30),
    # Título centrado (apertura / capítulo).
    "titulo": dict(font="Inter-SemiBold", size=84, color="white", x="center",
                   y="center", anchor="middle", shadow=3, shadow_alpha=0.4,
                   fade=0.4, line_spacing=6),
    # Texto sobre placa clara (cierre), oscuro.
    "cierre": dict(font="Inter-Medium", size=44, color="0x1E1E1E", x="center",
                   y=700, anchor="top", shadow=0, fade=0.4),
}

FONT_FILES = {
    "Inter-Regular": ["Inter-Regular.ttf", "Inter-Regular.otf", "Inter.ttf", "Inter"],
    "Inter-Light": ["Inter-Light.ttf", "Inter-Light.otf", "Inter:style=Light"],
    "Inter-Medium": ["Inter-Medium.ttf", "Inter-Medium.otf", "Inter:style=Medium"],
    "Inter-SemiBold": ["Inter-SemiBold.ttf", "Inter-SemiBold.otf", "Inter:style=SemiBold"],
    "BarlowCondensed-Regular": ["BarlowCondensed-Regular.ttf"],
    "BarlowCondensed-Medium": ["BarlowCondensed-Medium.ttf"],
    "BarlowCondensed-SemiBold": ["BarlowCondensed-SemiBold.ttf"],
    "BarlowCondensed-Bold": ["BarlowCondensed-Bold.ttf"],
}

XFADE_TYPES = {
    "dissolve": "fade", "fade": "fade", "fadeblack": "fadeblack",
    "fadewhite": "fadewhite", "wipeleft": "wipeleft", "wiperight": "wiperight",
    "slideleft": "slideleft", "slideright": "slideright", "smoothleft": "smoothleft",
    "smoothright": "smoothright", "circleopen": "circleopen", "zoomin": "zoomin",
    "hblur": "hblur", "dissolve_grain": "dissolve",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def resolve_font(name: str) -> str:
    """Devuelve ruta a un archivo de fuente. Busca en assets/fonts y luego en fontconfig."""
    if os.path.isfile(name):
        return name
    for cand in FONT_FILES.get(name, [name]):
        p = FONTS / cand
        if p.is_file():
            return str(p)
    # fontconfig
    family = FONT_FILES.get(name, [name])[-1]
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", family],
                             capture_output=True, text=True, check=True).stdout.strip()
        if out:
            return out
    except (OSError, subprocess.CalledProcessError):
        pass
    die(f"No encuentro la fuente '{name}'. Copiala a assets/fonts/.")
    return ""


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,r_frame_rate",
         "-of", "json", path], capture_output=True, text=True)
    if out.returncode != 0:
        die(f"ffprobe no pudo leer {path}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def has_audio(info: dict) -> bool:
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))


def parse_srt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.strip())
    items = []
    ts = r"(\d+):(\d+):(\d+)[,.](\d+)"
    for b in blocks:
        lines = [l for l in b.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        idx = 1 if "-->" in lines[1] else 0
        m = re.findall(ts, lines[idx])
        if len(m) != 2:
            continue
        def sec(t):
            h, mi, s, ms = t
            return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / (10 ** len(ms))
        items.append({"text": "\n".join(lines[idx + 1:]), "start": sec(m[0]), "end": sec(m[1])})
    return items


class Builder:
    def __init__(self, edl: dict, base: Path, draft: bool, tmp: Path):
        self.edl = edl
        self.base = base
        self.draft = draft
        self.tmp = tmp
        canvas = edl.get("canvas", {})
        self.W = int(canvas.get("width", 1920))
        self.H = int(canvas.get("height", 1080))
        self.fps = canvas.get("fps", 25)
        if draft:
            scale = 540 / self.H
            self.W = int(round(self.W * scale / 2) * 2)
            self.H = 540
        self.k = self.H / 1080.0  # factor de escala tipográfica
        self.inputs: list[list[str]] = []
        self.filters: list[str] = []
        self.timeline: list[tuple[float, float]] = []  # (start, dur) de cada clip
        self.cache = base / ".cache" / "conform"
        self.cache.mkdir(parents=True, exist_ok=True)

    def path(self, p: str) -> str:
        q = Path(p)
        if not q.is_absolute():
            q = self.base / q
        if not q.exists():
            die(f"No existe el archivo: {q}")
        return str(q)

    def add_input(self, args: list[str]) -> int:
        self.inputs.append(args)
        return len(self.inputs) - 1

    # ------------------------------------------------------------------ video
    def conform(self, i: int, clip: dict) -> tuple[str, float, bool]:
        """Etapa 1: normaliza un plano (recorte, velocidad, encuadre, movimiento,
        grade por plano, fps) a un intermedio cacheado. Devuelve (ruta, dur, tiene_audio)."""
        src = self.path(clip["src"])
        is_image = Path(src).suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
        speed = float(clip.get("speed", 1.0))
        want_audio = bool(clip.get("audio")) and not is_image
        if is_image:
            dur = float(clip.get("dur", 3.0))
            inp = ["-loop", "1", "-framerate", str(self.fps), "-t", f"{dur:.3f}", "-i", src]
            src_audio = False
        else:
            tin = float(clip.get("in", 0.0))
            if "out" in clip:
                src_dur = float(clip["out"]) - tin
            elif "dur" in clip:
                src_dur = float(clip["dur"]) * speed
            else:
                src_dur = float(probe(src)["format"]["duration"]) - tin
            if src_dur <= 0:
                die(f"Plano {i}: duración inválida (in/out).")
            dur = src_dur / speed
            inp = ["-ss", f"{tin:.3f}", "-t", f"{src_dur:.3f}", "-i", src]
            src_audio = want_audio and has_audio(probe(src))
        W, H = self.W, self.H
        f = [f"setpts=(PTS-STARTPTS)/{speed}" if speed != 1.0 else "setpts=PTS-STARTPTS",
             f"fps={self.fps}"]
        fit = clip.get("fit", "cover")
        move = clip.get("move")
        if fit == "contain":
            bg = clip.get("bg", "black")
            f.append(f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos")
            f.append(f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={bg}")
        elif move:
            # Movimiento de cámara sintético (push-in / pull-out / paneo), con
            # sobremuestreo x2 para evitar el "temblor" típico de zoompan.
            amt = float(move.get("amount", 0.06))
            kind = move.get("type", "push_in")
            n = max(int(round(dur * float(self.fps))), 1)
            f.append(f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase:flags=lanczos")
            f.append(f"crop={W*2}:{H*2}")
            ease = f"(0.5-0.5*cos(PI*on/{n}))" if move.get("ease", True) else f"(on/{n})"
            if kind == "push_in":
                z = f"1+{amt}*{ease}"
                x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
            elif kind == "pull_out":
                z = f"1+{amt}-{amt}*{ease}"
                x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
            elif kind in ("pan_left", "pan_right"):
                z = f"1+{amt}"
                x = f"(iw-iw/zoom)*{ease}" if kind == "pan_right" else f"(iw-iw/zoom)*(1-{ease})"
                y = "ih/2-(ih/zoom/2)"
            else:
                die(f"Movimiento desconocido: {kind}")
            f.append(f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={self.fps}")
        else:
            f.append(f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos")
            f.append(f"crop={W}:{H}")
        if clip.get("grade"):
            f.extend(self.grade_filters(clip["grade"]))
        # Grade global por plano; las placas/imágenes lo omiten salvo que se pida.
        if self.edl.get("grade") and clip.get("global_grade", not is_image):
            f.extend(self.grade_filters(self.edl["grade"]))
        f += ["setsar=1", "format=yuv422p10le" if not self.draft else "format=yuv420p"]
        vf = ",".join(f)
        af = None
        if src_audio:
            af = "asetpts=PTS-STARTPTS"
            if speed != 1.0:
                af += f",atempo={speed}"
            af += ",aresample=48000,aformat=channel_layouts=stereo"
        # cache por contenido: misma fuente + mismos parámetros = no se re-renderiza
        key = json.dumps([src, os.path.getmtime(src), inp, vf, af, self.draft], sort_keys=True)
        h = hashlib.sha1(key.encode()).hexdigest()[:16]
        out = self.cache / f"{h}.mov"
        if not out.exists():
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inp, "-vf", vf,
                   "-t", f"{dur:.3f}"]
            if self.draft:
                cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "16"]
            else:
                cmd += ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0"]
            cmd += (["-af", af, "-c:a", "pcm_s16le"] if af else ["-an"])
            tmp_out = out.with_suffix(".part.mov")
            r = subprocess.run(cmd + [str(tmp_out)], capture_output=True, text=True)
            if r.returncode != 0:
                die(f"Conform del plano {i} ({clip['src']}) falló:\n{r.stderr[-2000:]}")
            tmp_out.rename(out)
            print(f"  · plano {i+1:>2}: conformado {Path(src).name} [{dur:.2f}s]")
        else:
            print(f"  · plano {i+1:>2}: cache {Path(src).name} [{dur:.2f}s]")
        return str(out), dur, bool(af)

    def clip_chain(self, i: int, clip: dict) -> tuple[str, float]:
        path, dur, aud = self.conform(i, clip)
        idx = self.add_input(["-i", path])
        self.filters.append(f"[{idx}:v]setpts=PTS-STARTPTS,format=yuv420p,settb=AVTB[v{i}]")
        clip["_idx"] = idx
        clip["_has_audio"] = aud
        return f"v{i}", dur

    def grade_filters(self, g: dict) -> list[str]:
        out = []
        if g.get("lut"):
            lut = self.path(g["lut"]).replace(":", "\\:")
            out.append(f"lut3d=file='{lut}':interp=tetrahedral")
        eq = []
        for k in ("contrast", "brightness", "saturation", "gamma"):
            if k in g:
                eq.append(f"{k}={g[k]}")
        if eq:
            out.append("eq=" + ":".join(eq))
        if g.get("temperature"):
            # >0 cálido, <0 frío (aprox. vía colorbalance en medios)
            t = max(-1.0, min(1.0, float(g["temperature"])))
            out.append(f"colorbalance=rm={0.08*t:.3f}:bm={-0.08*t:.3f}:rh={0.05*t:.3f}:bh={-0.05*t:.3f}")
        if g.get("sharpen"):
            out.append(f"unsharp=5:5:{float(g['sharpen']):.2f}:5:5:0")
        if g.get("vignette"):
            out.append("vignette=angle=PI/5")
        if g.get("grain"):
            out.append(f"noise=alls={int(g['grain'])}:allf=t")
        return out

    def assemble(self) -> tuple[str, float]:
        clips = self.edl.get("clips", [])
        if not clips:
            die("La EDL no tiene clips.")
        cur, total = None, 0.0
        for i, clip in enumerate(clips):
            label, dur = self.clip_chain(i, clip)
            tr = clip.get("transition_in", {"type": "cut"})
            ttype = tr.get("type", "cut")
            if cur is None:
                self.timeline.append((0.0, dur))
                cur, total = label, dur
                continue
            out = f"x{i}"
            if ttype == "cut":
                self.filters.append(f"[{cur}][{label}]concat=n=2:v=1:a=0[{out}]")
                self.timeline.append((total, dur))
                total += dur
            else:
                td = float(tr.get("dur", 0.5))
                td = min(td, dur * 0.9, total * 0.9)
                xt = XFADE_TYPES.get(ttype)
                if not xt:
                    die(f"Transición desconocida: {ttype}")
                offset = total - td
                self.filters.append(
                    f"[{cur}][{label}]xfade=transition={xt}:duration={td:.3f}:offset={offset:.3f}[{out}]")
                self.timeline.append((offset, dur))
                total = offset + dur
            cur = out
        return cur, total

    # ------------------------------------------------------------------ texto
    def text_filters(self, total: float) -> list[str]:
        items = list(self.edl.get("texts", []))
        sub = self.edl.get("subtitles")
        if sub:
            src = sub if isinstance(sub, str) else sub["src"]
            offset = 0.0 if isinstance(sub, str) else float(sub.get("offset", 0.0))
            style = "subtitulo" if isinstance(sub, str) else sub.get("style", "subtitulo")
            for it in parse_srt(Path(self.path(src))):
                it["start"] += offset
                it["end"] += offset
                it["style"] = style
                items.append(it)
        out = []
        for n, t in enumerate(items):
            st = dict(STYLES.get(t.get("style", "subtitulo"), STYLES["subtitulo"]))
            st.update({k: v for k, v in t.items() if k in st or k in ("font", "size", "color", "x", "y")})
            text = t["text"].upper() if st.get("upper") else t["text"]
            tf = self.tmp / f"text_{n}.txt"
            tf.write_text(text, encoding="utf-8")
            s, e = float(t["start"]), float(t["end"])
            if s >= total:
                continue
            e = min(e, total)
            fade = float(st.get("fade", 0.2))
            size = int(round(float(st["size"]) * self.k))
            font = resolve_font(st["font"]).replace(":", "\\:")
            alpha = (f"if(lt(t,{s}+{fade}),(t-{s})/{fade},"
                     f"if(gt(t,{e}-{fade}),({e}-t)/{fade},1))")
            # posición
            x = st["x"]
            if x == "center":
                xexpr = "(w-text_w)/2"
            else:
                xexpr = f"{float(x)*self.k:.1f}"
                if st.get("slide"):
                    sl = float(st["slide"]) * self.k
                    # entra deslizando desde la izquierda con ease-out cúbico
                    xexpr = (f"{xexpr}-{sl:.1f}*pow(1-min(max((t-{s})/{fade*2.2},0),1),3)")
            y = st["y"]
            if y == "center":
                yexpr = "(h-text_h)/2"
            else:
                yv = float(y) * self.k
                anchor = st.get("anchor", "top")
                yexpr = {"top": f"{yv:.1f}", "bottom": f"{yv:.1f}-text_h",
                         "middle": f"{yv:.1f}-text_h/2"}[anchor]
            parts = [
                f"fontfile='{font}'", f"textfile='{tf}'", f"fontsize={size}",
                f"fontcolor={st['color']}", f"x='{xexpr}'", f"y='{yexpr}'",
                f"alpha='{alpha}'", f"enable='between(t,{s},{e})'",
                f"line_spacing={int(st.get('line_spacing', 6)*self.k)}",
                "text_align=C" if x == "center" else "text_align=L",
                "fix_bounds=1",
            ]
            if st.get("shadow"):
                sh = max(1, int(round(st["shadow"] * self.k)))
                parts += [f"shadowx={sh}", f"shadowy={sh}",
                          f"shadowcolor=black@{st.get('shadow_alpha', 0.5)}"]
            out.append("drawtext=" + ":".join(parts))
        return out

    # ------------------------------------------------------------------ audio
    def audio_graph(self, total: float) -> str | None:
        a = self.edl.get("audio", {})
        mix = []
        # Sonido directo de los clips (nat sound / testimonios)
        clips = self.edl.get("clips", [])
        for i, clip in enumerate(clips):
            if not clip.get("audio") or not clip.get("_has_audio"):
                continue
            start, dur = self.timeline[i]
            gain = float(clip.get("audio_gain_db", 0))
            f = [f"[{clip['_idx']}:a]asetpts=PTS-STARTPTS", f"atrim=0:{dur:.3f}"]
            f.append("aresample=48000,aformat=channel_layouts=stereo")
            fa = min(0.08, dur / 4)
            f.append(f"afade=t=in:d={fa:.3f},afade=t=out:st={max(dur-fa,0):.3f}:d={fa:.3f}")
            f.append(f"volume={gain}dB")
            f.append(f"adelay={int(start*1000)}|{int(start*1000)}")
            self.filters.append(",".join(f) + f"[ca{i}]")
            mix.append(f"[ca{i}]")
        vo = a.get("vo")
        vo_lbl = None
        if vo:
            vi = self.add_input(["-i", self.path(vo["src"])])
            st = float(vo.get("start", 0.0))
            g = float(vo.get("gain_db", 0))
            chain = (f"[{vi}:a]aresample=48000,aformat=channel_layouts=stereo,"
                     f"highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,"
                     f"volume={g}dB,adelay={int(st*1000)}|{int(st*1000)}")
            if a.get("duck_music_under_vo", True) and a.get("music"):
                self.filters.append(chain + ",asplit=2[vo][vosc]")
                vo_lbl = "[vosc]"
            else:
                self.filters.append(chain + "[vo]")
            mix.append("[vo]")
        mu = a.get("music")
        if mu:
            mi = self.add_input(["-i", self.path(mu["src"])])
            tin = float(mu.get("in", 0.0))
            g = float(mu.get("gain_db", -6))
            fi = float(mu.get("fade_in", 0.0))
            fo = float(mu.get("fade_out", 2.0))
            end = float(mu.get("end", total))
            f = [f"[{mi}:a]atrim=start={tin}", "asetpts=PTS-STARTPTS",
                 "aresample=48000,aformat=channel_layouts=stereo", f"atrim=0:{end:.3f}"]
            if fi > 0:
                f.append(f"afade=t=in:d={fi}")
            if fo > 0:
                f.append(f"afade=t=out:st={max(end-fo,0):.3f}:d={fo}")
            f.append(f"volume={g}dB")
            if vo_lbl:
                self.filters.append(",".join(f) + "[mu0]")
                duck = a.get("duck", {})
                self.filters.append(
                    f"[mu0]{vo_lbl}sidechaincompress=threshold={duck.get('threshold', 0.03)}:"
                    f"ratio={duck.get('ratio', 6)}:attack={duck.get('attack', 80)}:"
                    f"release={duck.get('release', 600)}[mu]")
            else:
                self.filters.append(",".join(f) + "[mu]")
            mix.append("[mu]")
        for n, sfx in enumerate(a.get("sfx", [])):
            si = self.add_input(["-i", self.path(sfx["src"])])
            at = float(sfx["at"])
            self.filters.append(
                f"[{si}:a]aresample=48000,aformat=channel_layouts=stereo,volume={float(sfx.get('gain_db', -10))}dB,"
                f"adelay={int(at*1000)}|{int(at*1000)}[sfx{n}]")
            mix.append(f"[sfx{n}]")
        if not mix:
            return None
        self.filters.append(
            "".join(mix) + f"amix=inputs={len(mix)}:normalize=0:dropout_transition=0,"
            f"atrim=0:{total:.3f},apad=whole_dur={total:.3f}[amix]")
        return "[amix]"

    # ------------------------------------------------------------------ build
    def build(self, out: str) -> list[str]:
        vlabel, total = self.assemble()
        post = []
        fade = self.edl.get("fade", {})
        if fade.get("in", 0):
            post.append(f"fade=t=in:st=0:d={fade['in']}:color={fade.get('color', 'black')}")
        if fade.get("out", 0):
            post.append(f"fade=t=out:st={total-float(fade['out']):.3f}:d={fade['out']}:color={fade.get('color', 'black')}")
        post.extend(self.text_filters(total))
        logo = self.edl.get("logo_bug")
        if post:
            self.filters.append(f"[{vlabel}]" + ",".join(post) + "[vpost]")
            vlabel = "vpost"
        if logo:
            li = self.add_input(["-loop", "1", "-i", self.path(logo["src"])])
            w = int(float(logo.get("width", 160)) * self.k)
            m = int(float(logo.get("margin", 60)) * self.k)
            op = float(logo.get("opacity", 0.85))
            s = float(logo.get("start", 0)); e = float(logo.get("end", total))
            self.filters.append(f"[{li}:v]scale={w}:-1,format=rgba,colorchannelmixer=aa={op}[logo]")
            self.filters.append(
                f"[{vlabel}][logo]overlay=W-w-{m}:{m}:enable='between(t,{s},{e})':shortest=1[vlogo]")
            vlabel = "vlogo"
        alabel = self.audio_graph(total)
        cmd = ["ffmpeg", "-hide_banner", "-y"]
        for inp in self.inputs:
            cmd += inp
        fc = ";\n".join(self.filters)
        script = self.tmp / "filter_complex.txt"
        script.write_text(fc, encoding="utf-8")
        cmd += ["-filter_complex_script", str(script), "-map", f"[{vlabel}]"]
        if alabel:
            cmd += ["-map", alabel]
        cmd += ["-t", f"{total:.3f}"]
        enc = self.edl.get("encode", {})
        if self.draft:
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "24"]
        else:
            cmd += ["-c:v", "libx264", "-preset", enc.get("preset", "slow"),
                    "-crf", str(enc.get("crf", 16)), "-profile:v", "high",
                    "-maxrate", enc.get("maxrate", "30M"), "-bufsize", enc.get("bufsize", "60M"),
                    "-g", str(int(float(self.fps) * 2))]
        cmd += ["-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                "-color_trc", "bt709", "-color_range", "tv"]
        if alabel:
            cmd += ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
        cmd += ["-movflags", "+faststart", out]
        self.total = total
        return cmd


def loudnorm_pass(src: str, dst: str, target: dict) -> None:
    """Normalización de loudness en dos pasadas (EBU R128) copiando el video."""
    I, TP, LRA = target.get("I", -14), target.get("TP", -1.0), target.get("LRA", 11)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-vn", "-af",
                        f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m.stderr, re.S)
    if not js:
        die("No pude medir loudness:\n" + m.stderr[-2000:])
    d = json.loads(js.group(0))
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={d['input_i']}:measured_TP={d['input_tp']}:"
          f"measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:"
          f"offset={d['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-c:v", "copy",
                    "-af", af, "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                    "-movflags", "+faststart", dst], check=True)
    print(f"Loudness: medido I={d['input_i']} LUFS TP={d['input_tp']} dBTP → objetivo I={I} TP={TP}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("-o", "--output", help="ruta de salida (pisa la de la EDL)")
    ap.add_argument("--draft", action="store_true", help="preview rápido 540p")
    ap.add_argument("--print", action="store_true", help="solo imprime el comando y el grafo")
    ap.add_argument("--keep-tmp", action="store_true")
    args = ap.parse_args()

    edl_path = Path(args.edl).resolve()
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    base = edl_path.parent
    out = args.output or edl.get("output", "render/master.mp4")
    if args.draft:
        out = re.sub(r"(\.\w+)$", r"_draft\1", out)
    outp = Path(out) if Path(out).is_absolute() else base / out
    outp.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="edl_"))
    try:
        b = Builder(edl, base, args.draft, tmp)
        raw = str(outp.with_name(outp.stem + "_premix" + outp.suffix))
        cmd = b.build(raw)
        if args.print:
            print(" ".join(shlex.quote(c) for c in cmd))
            print("\n# filter_complex:\n" + (tmp / "filter_complex.txt").read_text())
            return
        print(f"Renderizando {b.W}x{b.H}@{b.fps} · {b.total:.2f}s · {len(edl['clips'])} planos → {outp}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-4000:], file=sys.stderr)
            print(f"\nGrafo en {tmp/'filter_complex.txt'}", file=sys.stderr)
            args.keep_tmp = True
            die("FFmpeg falló.")
        has_a = "-map" in cmd and cmd.count("-map") > 1
        if has_a and edl.get("loudness", {"I": -14}) is not None:
            loudnorm_pass(raw, str(outp), edl.get("loudness", {}))
            os.remove(raw)
        else:
            shutil.move(raw, outp)
        print(f"OK → {outp}")
    finally:
        if not args.keep_tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
