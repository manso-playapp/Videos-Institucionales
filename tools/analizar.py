#!/usr/bin/env python3
"""
analizar.py — Medir material en vez de suponer.

Modos:
  ref <video> [-o carpeta]      Analiza una pieza terminada (referencia o nuestro master):
                                specs, cortes, duración media de plano (ASL), loudness,
                                hoja de contacto y lista de cortes. → informe .md
  inventario <carpeta> [-o ..]  Inventario de material bruto: specs por archivo, una
                                hoja de contacto por clip y un índice inventario.md
                                para elegir planos sin abrir cada archivo.

Ejemplos:
  python3 tools/analizar.py ref referencias/Schneider.mp4
  python3 tools/analizar.py inventario proyectos/acme/media -o proyectos/acme/inventario
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".mxf", ".mts", ".m4v", ".avi", ".mkv", ".braw", ".r3d"}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def specs(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration,bit_rate:stream=codec_type,codec_name,profile,width,height,"
             "r_frame_rate,pix_fmt,color_primaries,color_transfer,sample_rate,channels:"
             "stream_tags=timecode:format_tags=creation_time,com.apple.quicktime.model",
             "-of", "json", str(path)])
    if r.returncode != 0:
        return {"error": r.stderr.strip()}
    d = json.loads(r.stdout)
    out = {"duracion": float(d["format"].get("duration", 0) or 0),
           "bitrate_mbps": round(int(d["format"].get("bit_rate", 0) or 0) / 1e6, 1)}
    for s in d.get("streams", []):
        if s["codec_type"] == "video" and "video" not in out:
            num, den = s.get("r_frame_rate", "0/1").split("/")
            out["video"] = {
                "codec": f"{s.get('codec_name')} {s.get('profile', '')}".strip(),
                "res": f"{s.get('width')}x{s.get('height')}",
                "fps": round(int(num) / max(int(den), 1), 3),
                "pix_fmt": s.get("pix_fmt"),
                "color": f"{s.get('color_primaries', '?')}/{s.get('color_transfer', '?')}",
                "timecode": (s.get("tags") or {}).get("timecode"),
            }
        elif s["codec_type"] == "audio" and "audio" not in out:
            out["audio"] = {"codec": s.get("codec_name"), "sr": s.get("sample_rate"),
                            "ch": s.get("channels")}
    tags = d["format"].get("tags") or {}
    out["camara"] = tags.get("com.apple.quicktime.model")
    out["fecha"] = tags.get("creation_time")
    return out


def cuts(path: Path, thr: float = 0.3) -> list[float]:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
             f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def loudness(path: Path) -> dict:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
             "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    g = lambda k: (re.search(k + r":\s+(-?[0-9.]+|-inf)", tail) or [None, None])[1]
    return {"I": g("I"), "LRA": g("LRA"), "TP": g("Peak")}


def contact_sheet(path: Path, out: Path, dur: float, cols=4, rows=6, width=480) -> None:
    n = cols * rows
    rate = n / max(dur, 0.1)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vf",
         f"fps={rate},scale={width}:-2,tile={cols}x{rows}:padding=4", "-frames:v", "1",
         "-q:v", "3", str(out)])


def fmt_tc(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def cmd_ref(video: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    stem = video.stem.split(".")[0]
    sp = specs(video)
    dur = sp["duracion"]
    print(f"Analizando {video.name} ({dur:.1f}s)…")
    cl = cuts(video)
    ld = loudness(video) if "audio" in sp else {}
    sheet = outdir / f"{stem}.contacto.jpg"
    contact_sheet(video, sheet, dur)
    bounds = [0.0] + cl + [dur]
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.04]
    asl = sum(shots) / len(shots) if shots else dur
    med = sorted(shots)[len(shots) // 2] if shots else dur
    v = sp.get("video", {})
    md = [f"# Análisis: {video.name}", "",
          "| Parámetro | Valor |", "|---|---|",
          f"| Duración | {dur:.2f} s |",
          f"| Video | {v.get('codec')} · {v.get('res')} · {v.get('fps')} fps · {v.get('pix_fmt')} · {v.get('color')} |",
          f"| Bitrate total | {sp['bitrate_mbps']} Mbps |",
          f"| Audio | {sp.get('audio')} |",
          f"| Cortes duros detectados | {len(cl)} (umbral 0.3; disolvencias no cuentan) |",
          f"| Duración media de plano (ASL) | {asl:.2f} s · mediana {med:.2f} s |",
          f"| Loudness integrado | {ld.get('I')} LUFS · LRA {ld.get('LRA')} LU · true peak {ld.get('TP')} dBTP |",
          "", f"![contacto]({sheet.name})", "", "## Cortes", "",
          ", ".join(fmt_tc(c) for c in cl) or "—"]
    try:
        tp = float(ld.get("TP")) if ld.get("TP") not in (None, "-inf") else None
        if tp is not None and tp > -1.0:
            md += ["", f"> ⚠️ True peak {tp} dBTP > -1: hay clipping/inter-sample peaks. No replicar."]
    except ValueError:
        pass
    rep = outdir / f"{stem}.analisis.md"
    rep.write_text("\n".join(md) + "\n", encoding="utf-8")
    (outdir / f"{stem}.cortes.json").write_text(json.dumps({"cuts": cl, "asl": asl}, indent=1))
    print("\n".join(md[2:11]))
    print(f"\n→ {rep}\n→ {sheet}")


def cmd_inventario(folder: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_EXT)
    if not files:
        sys.exit(f"No hay videos en {folder}")
    rows = ["# Inventario de material", "", f"Carpeta: `{folder}` · {len(files)} clips", "",
            "| # | Archivo | Dur | Res | fps | Codec | Color | Audio | Hoja |",
            "|---|---|---|---|---|---|---|---|---|"]
    total = 0.0
    data = []
    for i, f in enumerate(files, 1):
        sp = specs(f)
        if "error" in sp:
            rows.append(f"| {i} | {f.name} | ERROR | | | | | | |")
            continue
        dur = sp["duracion"]
        total += dur
        v = sp.get("video", {})
        sheet = outdir / f"{i:03d}_{f.stem}.jpg"
        cols = 6 if dur > 20 else 4
        contact_sheet(f, sheet, dur, cols=cols, rows=2, width=320)
        rows.append(f"| {i} | `{f.relative_to(folder)}` | {dur:.1f}s | {v.get('res')} | {v.get('fps')} | "
                    f"{v.get('codec')} | {v.get('color')} | {'sí' if 'audio' in sp else 'no'} | "
                    f"[ver]({sheet.name}) |")
        data.append({"n": i, "file": str(f), **sp})
        print(f"  {i:>3}/{len(files)} {f.name} {dur:.1f}s {v.get('res')}@{v.get('fps')}")
    rows += ["", f"Total material: {total/60:.1f} min"]
    fps_set = {d.get("video", {}).get("fps") for d in data}
    if len(fps_set) > 1:
        rows += ["", f"> ⚠️ Frame rates mezclados: {sorted(x for x in fps_set if x)}. "
                 "Definir fps del proyecto y planificar conformado (cámara lenta sólo desde fps altos)."]
    (outdir / "inventario.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (outdir / "inventario.json").write_text(json.dumps(data, indent=1, default=str))
    print(f"→ {outdir/'inventario.md'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("ref"); a.add_argument("video"); a.add_argument("-o", "--out")
    b = sub.add_parser("inventario"); b.add_argument("carpeta"); b.add_argument("-o", "--out")
    args = ap.parse_args()
    if args.mode == "ref":
        v = Path(args.video)
        cmd_ref(v, Path(args.out) if args.out else v.parent / "analisis")
    else:
        c = Path(args.carpeta)
        cmd_inventario(c, Path(args.out) if args.out else c.parent / "inventario")


if __name__ == "__main__":
    main()
