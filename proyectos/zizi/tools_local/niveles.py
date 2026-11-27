#!/usr/bin/env python3
"""Nivelación de color de TODAS las tomas (no solo las subexpuestas): mide cada toma y calcula la corrección que la lleva
a una base común, para que el look del estudio caiga parejo.
  · punto negro y punto blanco (percentiles 1 y 99 de luminancia) -> mismo rango tonal
  · gamma -> mismo nivel medio (mediana ~0,44)
  · balance de blancos: referencia = lo más claro y poco saturado del cuadro (nubes, columnas blancas, chapa); corrige la dominante
Todo con topes y a intensidad parcial: empareja sin aplanar ni inventar luz. Mide sobre los proxies (artefacto/media).
Salida: niveles.json  {n: {med,p1,p99,wb, grade:{levels:{black,white,wb,omin,omax}, gamma}}}"""
import json, subprocess, numpy as np
from pathlib import Path
A = Path(__file__).parent.parent
W, H, N = 160, 90, 7
OBJ_MED, OMIN, OMAX = 0.44, 0.035, 0.955
def frames(p, dur):
    out = []
    for i in range(N):
        t = dur * (i + 0.5) / N
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) == W * H * 3: out.append(np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.float32) / 255)
    return np.concatenate(out) if out else None
inv = {c["n"]: c for c in json.load(open(A / "inventario/inventario.json"))}; res = {}
for n, c in sorted(inv.items()):
    p = A / f"artefacto/media/t{n:03d}.mp4"
    if not p.exists(): continue
    px = frames(p, c["duracion"])
    if px is None: continue
    Y = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    p1, med, p99 = [float(np.percentile(Y, q)) for q in (1, 50, 99)]
    # punto negro/blanco: se corrige el 75 % de la distancia al objetivo, con topes para no recortar ni estirar de más
    black = float(np.clip(0.75 * (p1 - OMIN) + 0.0, 0.0, 0.10)); black = max(0.0, black)
    white = float(np.clip(1.0 - 0.5 * (OMAX - p99) if p99 < OMAX else 1.0, 0.80, 1.0))
    # balance de blancos sobre lo claro y neutro
    sat = px.max(1) - px.min(1); m = (Y > np.percentile(Y, 90)) & (Y < 0.97) & (sat < 0.12)
    wb = [1.0, 1.0, 1.0]
    if m.sum() > 0.01 * len(Y):
        ref = px[m].mean(0); g = ref.mean() / ref                       # ganancia que neutraliza
        g = 1 + 0.6 * (g - 1); g = np.clip(g / g[1], 0.93, 1.07); wb = [round(float(v), 4) for v in g]
    # gamma para llevar la mediana (ya nivelada) al objetivo
    m2 = np.clip((med - black) / max(white - black, 1e-3), 0.02, 0.98) * (OMAX - OMIN) + OMIN
    gamma = float(np.clip(np.log(m2) / np.log(OBJ_MED), 0.80, 1.30)) if abs(m2 - OBJ_MED) > 0.03 else 1.0   # eq: salida = entrada^(1/gamma)
    gamma = round(1 + 0.8 * (gamma - 1), 2)
    gr = {"levels": {"black": round(black, 4), "white": round(white, 4), "wb": wb, "omin": 0.0, "omax": 1.0}}
    if abs(gamma - 1) >= 0.03: gr["gamma"] = gamma
    res[str(n)] = {"med": round(med, 3), "p1": round(p1, 3), "p99": round(p99, 3), "wb_ref": bool(m.sum() > 0.01 * len(Y)), "grade": gr}
json.dump(res, open(A / "niveles.json", "w"), indent=0)
g = [v["grade"].get("gamma", 1) for v in res.values()]; wbs = np.array([v["grade"]["levels"]["wb"] for v in res.values()])
print(len(res), "tomas · gamma", min(g), "a", max(g), "· con referencia de blanco:", sum(v["wb_ref"] for v in res.values()),
      "· wb R", wbs[:, 0].min(), wbs[:, 0].max(), "B", wbs[:, 2].min(), wbs[:, 2].max())
