#!/usr/bin/env python3
"""
motion.py — Motion graphics y transiciones de GPU renderizadas con Chromium (tools/motion/).

  python3 tools/motion.py lista
      Plantillas disponibles y las 215 transiciones GL (con descripción).

  python3 tools/motion.py plantilla dato -p '{"valor":"240.000","prefijo":"+","etiqueta":"kg mensuales"}' \
          -o render/dato.mov [--alpha] [--size 1920x1080] [--fps 25]
      Renderiza una plantilla (dato, zocalo, titulo, cierre, lottie, luz) a video.
      --alpha → ProRes 4444 con transparencia, para superponer.

  python3 tools/motion.py transicion A.mov B.mov --shader DirectionalWarp --dur 1.0 \
          [--ease cubic-in-out] [--uniforms '{"smoothness":0.3}'] -o render/t.mov
      Renderiza la transición entre el final de A y el comienzo de B.

  python3 tools/motion.py muestrario -o docs/transiciones.jpg [--filtro wipe]
      Hoja con el cuadro al 50 % de cada transición GL, para elegir a ojo.

render_edl.py usa estas funciones directamente: en la EDL alcanza con
  "transition_in": {"type": "gl:DirectionalWarp", "dur": 0.8, "ease": "cubic-in-out"}
  "overlays": [{"template": "dato", "params": {...}, "start": 12.0}]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOTION = REPO / "tools" / "motion"
TEMPLATES = MOTION / "templates"
GLDIR = REPO / "assets" / "transitions" / "gl"
CACHE = REPO / ".cache" / "motion"
EASES = ["linear", "sine-in-out", "quad-in-out", "cubic-in-out", "quart-in-out", "quint-in-out",
         "expo-in-out", "cubic-out", "quint-out", "cubic-in"]


def _node_render(page: Path, params: dict, out: Path, w: int, h: int, fps, alpha: bool, draft=False) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    pf = Path(tempfile.mkstemp(suffix=".json")[1])
    pf.write_text(json.dumps(params, ensure_ascii=False), encoding="utf-8")
    cmd = ["node", str(MOTION / "render.cjs"), "--page", str(page), "--params-file", str(pf),
           "--out", str(out), "--width", str(w), "--height", str(h), "--fps", str(fps)]
    if alpha:
        cmd.append("--alpha")
    if draft:
        cmd.append("--draft")
    try:
        r = subprocess.run(cmd, cwd=REPO)
        if r.returncode != 0:
            raise RuntimeError(f"Falló el render de {page.name}")
    finally:
        pf.unlink(missing_ok=True)


def _key(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def render_template(name: str, params: dict, w=1920, h=1080, fps=25, alpha=True, out: Path | None = None,
                    draft=False) -> Path:
    page = TEMPLATES / f"{name}.html"
    if not page.exists():
        raise SystemExit(f"No existe la plantilla '{name}'. Ver: python3 tools/motion.py lista")
    # el cache depende de la plantilla, sus parámetros y los archivos que referencia
    deps = [page.read_text(), (TEMPLATES / "_base.js").read_text(), (MOTION / "render.cjs").read_text()]
    for k in ("logo", "src"):
        if params.get(k):
            p = Path(params[k]) if Path(params[k]).is_absolute() else REPO / params[k]
            deps.append(p.stat().st_mtime if p.exists() else "?")
    key = _key(name, params, w, h, fps, alpha, deps)
    target = CACHE / f"{name}_{key}.mov"
    if not target.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".part.mov")
        _node_render(page, params, tmp, w, h, fps, alpha, draft)
        tmp.rename(target)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(target, out)
        return out
    return target


def _extract(src: str, start: float, dur: float, w: int, h: int, fps, pattern: str) -> int:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(start,0):.3f}", "-i", src,
                    "-t", f"{dur:.3f}", "-vf", f"fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,"
                    f"crop={w}:{h}", "-q:v", "2", pattern], check=True)
    return len(list(Path(pattern).parent.glob(Path(pattern).name.split("%")[0] + "*")))


def duration(path: str) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 path], capture_output=True, text=True).stdout.strip())


def render_transition(a: str, b: str, shader: str, dur=1.0, ease="cubic-in-out", uniforms: dict | None = None,
                      w=1920, h=1080, fps=25, a_end: float | None = None, b_start=0.0,
                      out: Path | None = None) -> Path:
    """Transición GL entre [a_end-dur, a_end] de A y [b_start, b_start+dur] de B."""
    if not (GLDIR / f"{shader}.glsl").exists():
        raise SystemExit(f"No existe la transición '{shader}'. Ver: python3 tools/motion.py lista")
    a_end = duration(a) if a_end is None else a_end
    key = _key((TEMPLATES / "transicion.html").read_text(), (MOTION / "render.cjs").read_text(),
               (GLDIR / f"{shader}.glsl").read_text(), shader, a, os.path.getmtime(a), b, os.path.getmtime(b), a_end, b_start, dur, ease, uniforms, w, h, fps)
    target = CACHE / f"gl_{shader}_{key}.mov"
    if not target.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmpd = Path(tempfile.mkdtemp(prefix="gltr_"))
        try:
            na = _extract(a, a_end - dur, dur, w, h, fps, str(tmpd / "a_%04d.jpg"))
            nb = _extract(b, b_start, dur, w, h, fps, str(tmpd / "b_%04d.jpg"))
            n = min(na, nb)
            if n < 2:
                raise RuntimeError("Clips demasiado cortos para la transición")
            params = {"shader": shader, "from": str(tmpd / "a_%04d.jpg"), "to": str(tmpd / "b_%04d.jpg"),
                      "n": n, "ease": ease, "uniforms": uniforms or {}}
            tmp = target.with_suffix(".part.mov")
            _node_render(TEMPLATES / "transicion.html", params, tmp, w, h, fps, alpha=False)
            tmp.rename(target)
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(target, out)
        return out
    return target


def gl_catalog() -> list[dict]:
    items = []
    for f in sorted(GLDIR.glob("*.glsl")):
        head = f.read_text(errors="ignore")[:800]
        g = lambda k: (re.search(rf"//\s*{k}:\s*(.+)", head) or [None, ""])[1].strip()
        items.append({"name": f.stem, "desc": g("Description"), "tags": g("Tags"), "license": g("License")})
    return items


def cmd_lista() -> None:
    print("PLANTILLAS (tools/motion/templates):")
    for t in sorted(TEMPLATES.glob("*.html")):
        if t.stem == "transicion":
            continue
        m = re.search(r"<!--\s*\n\s*(.+?)\n", t.read_text())
        print(f"  {t.stem:<10} {m.group(1).strip() if m else ''}")
    print(f"\nCURVAS (ease): {', '.join(EASES)}")
    cat = gl_catalog()
    print(f"\nTRANSICIONES GL ({len(cat)}) — usar como \"gl:<nombre>\" en transition_in:")
    for c in cat:
        print(f"  {c['name']:<28} {c['desc'][:70]}" + (f"  [{c['tags']}]" if c["tags"] else ""))
    print("\nRecomendadas para institucionales (sobrias): Fade, FadeColor, DirectionalWarp, DirectionalWipe, "
          "Directional, DirectionalEased, CrossZoom, SimpleZoom, ZoomInOut, DreamyZoom, DefocusBlur, "
          "TangentMotionBlur, LightWipe, LuminanceMelt, CrossWarp, LumaWipe")


def cmd_muestrario(out: Path, filtro: str | None) -> None:
    import math
    cat = [c for c in gl_catalog() if not filtro or filtro.lower() in (c["name"] + c["tags"]).lower()]
    tmpd = Path(tempfile.mkdtemp(prefix="muestra_"))
    try:
        w, h = 384, 216
        a, b = tmpd / "a.mp4", tmpd / "b.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"gradients=s={w}x{h}:c0=0x1E6E6E:c1=0xEEF3F2:x0=0:y0=0:x1={w}:y1={h}:d=1:r=25",
                        "-vf", "drawtext=fontfile=assets/fonts/BarlowCondensed-Bold.ttf:text=A:fontsize=120:"
                        "fontcolor=white:x=(w-tw)/2:y=(h-th)/2", str(a)], check=True, cwd=REPO)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"gradients=s={w}x{h}:c0=0xE8553A:c1=0x2A2A2A:x0=0:y0={h}:x1={w}:y1=0:d=1:r=25",
                        "-vf", "drawtext=fontfile=assets/fonts/BarlowCondensed-Bold.ttf:text=B:fontsize=120:"
                        "fontcolor=white:x=(w-tw)/2:y=(h-th)/2", str(b)], check=True, cwd=REPO)
        shots = []
        for i, c in enumerate(cat):
            try:
                t = render_transition(str(a), str(b), c["name"], dur=0.4, ease="linear", w=w, h=h, fps=25)
                png = tmpd / f"{i:03d}.png"
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(t), "-vf",
                                f"select=eq(n\\,5),drawbox=y=ih-24:w=iw:h=24:color=black@0.7:t=fill,"
                                f"drawtext=fontfile=assets/fonts/Inter-Medium.ttf:text='{c['name']}':fontsize=15:"
                                f"fontcolor=white:x=6:y=h-19", "-frames:v", "1", str(png)], check=True, cwd=REPO)
                shots.append(png)
                print(f"\r  {i+1}/{len(cat)} {c['name']:<30}", end="", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"\n  ✗ {c['name']}: {e}", file=sys.stderr)
        cols = 8
        rows = math.ceil(len(shots) / cols)
        lst = tmpd / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in shots))
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                        f"tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", "-q:v", "3", str(out)], check=True)
        print(f"\n→ {out} ({len(shots)} transiciones)")
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lista")
    p = sub.add_parser("plantilla")
    p.add_argument("nombre"); p.add_argument("-p", "--params", default="{}"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--alpha", action="store_true"); p.add_argument("--size", default="1920x1080")
    p.add_argument("--fps", default="25"); p.add_argument("--draft", action="store_true")
    t = sub.add_parser("transicion")
    t.add_argument("a"); t.add_argument("b"); t.add_argument("--shader", required=True)
    t.add_argument("--dur", type=float, default=1.0); t.add_argument("--ease", default="cubic-in-out", choices=EASES)
    t.add_argument("--uniforms", default="{}"); t.add_argument("-o", "--out", required=True)
    t.add_argument("--size", default="1920x1080"); t.add_argument("--fps", default="25")
    m = sub.add_parser("muestrario")
    m.add_argument("-o", "--out", default="docs/transiciones.jpg"); m.add_argument("--filtro")
    a = ap.parse_args()
    if a.cmd == "lista":
        cmd_lista()
    elif a.cmd == "plantilla":
        w, h = map(int, a.size.split("x"))
        params = json.loads(Path(a.params).read_text() if a.params.endswith(".json") else a.params)
        print(render_template(a.nombre, params, w, h, a.fps, a.alpha, Path(a.out), a.draft))
    elif a.cmd == "transicion":
        w, h = map(int, a.size.split("x"))
        print(render_transition(a.a, a.b, a.shader, a.dur, a.ease, json.loads(a.uniforms), w, h, a.fps, out=Path(a.out)))
    else:
        cmd_muestrario(Path(a.out), a.filtro)


if __name__ == "__main__":
    main()
