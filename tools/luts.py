#!/usr/bin/env python3
"""
luts.py — LUTs de look del estudio (.cube 33³) para usar en la EDL ("grade": {"lut": ...}).

  python3 tools/luts.py generar            # (re)genera assets/luts/*.cube
  python3 tools/luts.py muestra <img|video> [-t 5] -o docs/looks.jpg
                                           # aplica todos los looks a un cuadro, en grilla

Looks (sobre material ya en Rec.709 / display, NO sobre log — para log primero convertir
con el LUT del fabricante o con firsttake):

  estudio_industrial   sombras petróleo, blancos limpios levemente fríos, contraste medio (Alsafex/Schneider)
  estudio_calido       medios y altas cálidas, contraste suave; personas, oficinas, hospitalidad
  estudio_cine         teal & orange moderado con roll-off de altas tipo película
  estudio_limpio       solo curva S suave y roll-off de altas; corrige "video plano" sin cambiar color
  estudio_atardecer    aéreos de amanecer/atardecer: naranjas ricos, cielos profundos
  estudio_bn           blanco y negro de alto contraste con leve tono frío

Emulación de película real (Kodak 5207/2383, Fuji Eterna…): app `spectral-film-lut` en una compu de
escritorio, exportar el .cube a assets/luts/ (ver `python3 tools/luts.py pelicula`).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
LUTDIR = REPO / "assets" / "luts"
N = 33
LUMA = np.array([0.2126, 0.7152, 0.0722])


# ---------------------------------------------------------------- operaciones básicas (0..1, display)
def s_curve(x, amount=0.15, pivot=0.45):
    """Curva S suave alrededor de un pivote (contraste sin aplastar extremos)."""
    x = np.clip(x, 0, 1)
    lo = pivot * (x / pivot) ** (1 + amount)
    hi = 1 - (1 - pivot) * ((1 - x) / (1 - pivot)) ** (1 + amount)
    return np.where(x < pivot, lo, hi)


def rolloff(x, knee=0.8):
    """Compresión suave de altas luces (las altas "redondean" en vez de clipear)."""
    k = knee
    over = np.maximum(x - k, 0)
    return np.where(x > k, k + (1 - k) * (1 - np.exp(-over / (1 - k) * 1.6)) / (1 - np.exp(-1.6)), x)


def lift_toe(x, black=0.02):
    return black + (1 - black) * x


def luma(rgb):
    return (rgb @ LUMA)[..., None]


def saturation(rgb, s):
    y = luma(rgb)
    return y + (rgb - y) * s


def split_tone(rgb, shadows, highlights, amount_s=0.06, amount_h=0.05, balance=0.5):
    y = luma(rgb)
    ws = np.clip(1 - y / balance, 0, 1) ** 1.5
    wh = np.clip((y - balance) / (1 - balance), 0, 1) ** 1.5
    sh, hi = np.array(shadows, float), np.array(highlights, float)
    sh = sh - sh.mean(); hi = hi - hi.mean()
    return rgb + ws * sh * amount_s * 3 + wh * hi * amount_h * 3


def hue_sat(rgb, center_rgb, width=0.35, sat=1.2):
    """Sube/baja saturación de una familia de tonos (por similitud de croma)."""
    y = luma(rgb)
    c = rgb - y
    cn = c / (np.linalg.norm(c, axis=-1, keepdims=True) + 1e-6)
    t = np.array(center_rgb, float); t = t - t.mean(); t /= np.linalg.norm(t)
    w = np.clip((cn @ t)[..., None] - (1 - width), 0, None) / width
    return y + c * (1 + (sat - 1) * w)


def skin_protect(orig, graded, amount=0.6):
    """Devuelve parte del color original en tonos de piel (naranja/rosado de saturación media)."""
    y = luma(orig)
    c = orig - y
    t = np.array([0.55, 0.0, -0.55]); t /= np.linalg.norm(t)
    cn = c / (np.linalg.norm(c, axis=-1, keepdims=True) + 1e-6)
    w = np.clip((cn @ t)[..., None] - 0.75, 0, None) / 0.25 * amount
    return graded * (1 - w) + orig * w


# ---------------------------------------------------------------- looks
def look_industrial(rgb):
    o = rgb
    x = s_curve(rgb, 0.18)
    x = split_tone(x, shadows=[0.0, 0.55, 0.6], highlights=[0.9, 0.95, 1.0], amount_s=0.07, amount_h=0.03)
    x = hue_sat(x, [1, 0.5, 0], sat=0.85)          # naranjas/amarillos industriales un poco más sobrios
    x = hue_sat(x, [0, 0.6, 0.7], sat=1.12)        # petróleos/cian más ricos
    x = saturation(x, 0.95)
    x = skin_protect(o, x, 0.5)
    return lift_toe(rolloff(x, 0.82), 0.012)


def look_calido(rgb):
    o = rgb
    x = s_curve(rgb, 0.10)
    x = split_tone(x, shadows=[0.45, 0.4, 0.5], highlights=[1.0, 0.85, 0.65], amount_s=0.03, amount_h=0.07)
    x = saturation(x, 1.04)
    x = skin_protect(o, x, 0.35)
    return lift_toe(rolloff(x, 0.8), 0.018)


def look_cine(rgb):
    o = rgb
    x = s_curve(rgb, 0.22, 0.42)
    x = split_tone(x, shadows=[0.0, 0.5, 0.65], highlights=[1.0, 0.75, 0.45], amount_s=0.10, amount_h=0.08)
    x = hue_sat(x, [0, 0.2, 1], sat=0.85)          # azules saturados → hacia teal más sobrio
    x = saturation(x, 0.92)
    x = skin_protect(o, x, 0.45)
    return lift_toe(rolloff(x, 0.75), 0.02)


def look_limpio(rgb):
    return lift_toe(rolloff(s_curve(rgb, 0.12), 0.85), 0.008)


def look_atardecer(rgb):
    x = s_curve(rgb, 0.16)
    x = hue_sat(x, [1, 0.45, 0], sat=1.25)
    x = hue_sat(x, [0.1, 0.3, 1], sat=1.15)
    x = split_tone(x, shadows=[0.3, 0.3, 0.7], highlights=[1, 0.8, 0.5], amount_s=0.05, amount_h=0.06)
    return lift_toe(rolloff(x, 0.78), 0.01)


def look_bn(rgb):
    y = luma(rgb * np.array([1.05, 1.0, 0.85]))    # filtro amarillo suave: cielos más profundos
    y = s_curve(np.repeat(y, 3, axis=-1), 0.3)
    return lift_toe(rolloff(split_tone(y, [0.4, 0.5, 0.6], [0.55, 0.5, 0.45], 0.03, 0.02), 0.85), 0.015)


LOOKS = {
    "estudio_industrial": look_industrial, "estudio_calido": look_calido, "estudio_cine": look_cine,
    "estudio_limpio": look_limpio, "estudio_atardecer": look_atardecer, "estudio_bn": look_bn,
}


def write_cube(path: Path, fn, title: str) -> None:
    g = np.linspace(0, 1, N)
    # orden .cube: R varía más rápido
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([r, gg, b], -1).reshape(-1, 3)
    out = np.clip(fn(rgb), 0, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\n# Generado por tools/luts.py — Rec.709 display in/out\nLUT_3D_SIZE {N}\n'
                "DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n")
        np.savetxt(f, out, fmt="%.6f")


def cmd_generar() -> None:
    for name, fn in LOOKS.items():
        p = LUTDIR / f"{name}.cube"
        write_cube(p, fn, name)
        print(f"  ✅ {p.relative_to(REPO)}")


def cmd_muestra(src: str, t: float, out: Path) -> None:
    luts = sorted(LUTDIR.glob("*.cube"))
    tmp = Path(tempfile.mkdtemp())
    base = tmp / "base.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1",
                    "-vf", "scale=640:-2", str(base)], check=True)
    tiles = []
    for i, lut in enumerate([None] + luts):
        name = "original" if lut is None else lut.stem
        vf = (f"lut3d=file='{lut}':interp=tetrahedral," if lut else "") + \
             f"drawbox=y=ih-30:w=iw:h=30:color=black@0.6:t=fill,drawtext=fontfile={REPO}/assets/fonts/Inter-Medium.ttf:" \
             f"text='{name}':fontsize=18:fontcolor=white:x=10:y=h-24"
        o = tmp / f"{i:02d}.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(base), "-vf", vf, str(o)], check=True)
        tiles.append(o)
    cols = 3
    rows = -(-len(tiles) // cols)
    (tmp / "l.txt").write_text("".join(f"file '{p}'\n" for p in tiles))
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"),
                    "-vf", f"tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    print(f"→ {out}")


def cmd_pelicula(neg: str, prt: str | None, out: Path) -> None:
    sys.exit("La emulación espectral de película se hace con la app spectral-film-lut (GUI, PyQt6), que no\n"
             "corre en el entorno en la nube. En una compu de escritorio: pip install spectral-film-lut &&\n"
             "spectral-film-lut → elegir negativo/print → exportar .cube a assets/luts/film_<negativo>_<print>.cube")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generar")
    m = sub.add_parser("muestra"); m.add_argument("src"); m.add_argument("-t", type=float, default=1.0)
    m.add_argument("-o", "--out", default="docs/looks.jpg")
    f = sub.add_parser("pelicula"); f.add_argument("--negativo", required=True); f.add_argument("--print")
    f.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    if a.cmd == "generar":
        cmd_generar()
    elif a.cmd == "muestra":
        cmd_muestra(a.src, a.t, Path(a.out))
    else:
        cmd_pelicula(a.negativo, a.print, Path(a.out))


if __name__ == "__main__":
    main()
