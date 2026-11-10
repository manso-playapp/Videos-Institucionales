#!/usr/bin/env python3
"""
qc.py — Control de calidad de un master antes de entregarlo. Sale con código 1 si falla.

Chequea contra el perfil de entrega (docs/estandar.md):
  · specs: resolución, fps, códec, pix_fmt, etiquetas bt709, audio 48 kHz estéreo
  · loudness integrado y true peak (EBU R128 / ITU-R BS.1770)
  · negros no intencionales (>0.5 s fuera de inicio/fin), cuadros congelados (>1 s),
    silencios (>2 s) y duración esperada

Uso:
  python3 tools/qc.py render/master.mp4                    # perfil web (-14 LUFS)
  python3 tools/qc.py render/master.mp4 --perfil broadcast # -23 LUFS
  python3 tools/qc.py render/master.mp4 --res 2048x640 --fps 24  # pantallas LED / formatos especiales
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

PERFILES = {
    "web": {"I": -14.0, "I_tol": 1.0, "TP": -1.0},
    "broadcast": {"I": -23.0, "I_tol": 0.5, "TP": -1.0},
    "evento": {"I": -16.0, "I_tol": 1.5, "TP": -1.0},
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--perfil", default="web", choices=PERFILES)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--fps", type=float, default=None, help="fps esperado (default: no se chequea)")
    ap.add_argument("--duracion", type=float, default=None, help="duración esperada en s (±0.5)")
    a = ap.parse_args()
    P = PERFILES[a.perfil]
    fails, warns, oks = [], [], []

    d = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,codec_name,profile,width,height,r_frame_rate,"
                        "pix_fmt,color_primaries,color_transfer,color_space,sample_rate,channels",
                        "-of", "json", a.video]).stdout or "{}")
    if not d:
        sys.exit("No se pudo leer el archivo.")
    dur = float(d["format"]["duration"])
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)

    res = f"{v['width']}x{v['height']}"
    (oks if res == a.res else fails).append(f"Resolución {res} (esperado {a.res})")
    n, dn = v["r_frame_rate"].split("/")
    fps = int(n) / int(dn)
    if a.fps:
        (oks if abs(fps - a.fps) < 0.01 else fails).append(f"fps {fps:.3f} (esperado {a.fps})")
    else:
        oks.append(f"fps {fps:.3f}")
    (oks if v["codec_name"] in ("h264", "hevc", "prores") else warns).append(f"Códec {v['codec_name']} {v.get('profile','')}")
    (oks if v.get("pix_fmt") in ("yuv420p", "yuv422p10le", "yuv422p") else fails).append(f"pix_fmt {v.get('pix_fmt')}")
    tags = (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"))
    (oks if all(t == "bt709" for t in tags) else warns).append(
        f"Etiquetas de color {tags} (sin bt709 los players pueden desplazar colores)")
    if a.duracion:
        (oks if abs(dur - a.duracion) <= 0.5 else fails).append(f"Duración {dur:.2f}s (esperado {a.duracion})")

    if au:
        (oks if au.get("sample_rate") == "48000" else warns).append(f"Audio {au['codec_name']} {au.get('sample_rate')} Hz")
        (oks if au.get("channels") == 2 else warns).append(f"Canales: {au.get('channels')}")
        r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn", "-af", "ebur128=peak=true",
                 "-f", "null", "-"]).stderr
        t = r[r.rfind("Summary:"):]
        I = float(re.search(r"I:\s+(-?[0-9.]+)", t).group(1))
        tp_m = re.search(r"Peak:\s+(-?[0-9.]+|-inf)", t)
        TP = float(tp_m.group(1)) if tp_m and tp_m.group(1) != "-inf" else -99
        (oks if abs(I - P["I"]) <= P["I_tol"] else fails).append(f"Loudness {I} LUFS (objetivo {P['I']}±{P['I_tol']})")
        (oks if TP <= P["TP"] + 0.05 else fails).append(f"True peak {TP} dBTP (máx {P['TP']})")
        s = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn", "-af",
                 "silencedetect=n=-50dB:d=2", "-f", "null", "-"]).stderr
        sil = [(float(x), float(y)) for x, y in zip(re.findall(r"silence_start: ([0-9.]+)", s),
                                                    re.findall(r"silence_end: ([0-9.]+)", s))]
        sil = [x for x in sil if x[0] > 0.5 and x[1] < dur - 0.5]
        (warns if sil else oks).append(f"Silencios >2s en medio: {[(round(a_,1), round(b,1)) for a_, b in sil] or 'ninguno'}")
    else:
        warns.append("Sin pista de audio")

    vf = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-an", "-vf",
              "blackdetect=d=0.5:pix_th=0.10,freezedetect=n=0.001:d=1.0", "-f", "null", "-"]).stderr
    blacks = [(float(x), float(y)) for x, y in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", vf)]
    blacks = [b for b in blacks if b[0] > 0.1 and b[1] < dur - 0.1]
    (fails if blacks else oks).append(f"Negros en medio: {blacks or 'ninguno'}")
    fz = re.findall(r"freeze_start: ([0-9.]+)", vf)
    fe = re.findall(r"freeze_end: ([0-9.]+)", vf)
    freezes = [(round(float(x), 2), round(float(y), 2)) for x, y in zip(fz, fe)]
    (warns if freezes else oks).append(
        f"Cuadros congelados >1s: {freezes or 'ninguno'} (OK si son placas/logo intencionales)")

    print(f"QC · {a.video} · {dur:.2f}s · perfil {a.perfil}\n")
    for x in oks:
        print(f"  ✅ {x}")
    for x in warns:
        print(f"  ⚠️  {x}")
    for x in fails:
        print(f"  ❌ {x}")
    print(f"\nResultado: {'FALLA' if fails else 'APROBADO'} ({len(fails)} fallas, {len(warns)} avisos)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
