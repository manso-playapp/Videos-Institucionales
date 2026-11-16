#!/usr/bin/env python3
"""Genera edl_16x9.json y edl_9x16.json desde UNA lista de planos (misma historia, dos encuadres).
Cada plano: n = número del inventario, i = in (s), d = duración hasta el próximo corte (s),
tr = transición de entrada, f = foco horizontal para el vertical (0 izq … 1 der)."""
import json, sys
from pathlib import Path

AQUI = Path(__file__).parent
INV = {c["n"]: c for c in json.load(open(AQUI / "inventario/inventario.json"))}

ERR = []

def T(tipo, dur=0.8, ease="cubic-in-out", **u):
    t = {"type": "gl:" + tipo, "dur": dur, "ease": ease}
    if u: t["uniforms"] = u
    return t

# n, in, dur, transición, foco x (vertical), movimiento
S = [
 # --- A · "Cada proyecto tiene un comienzo": terreno vacío (0:00–0:16)
 dict(n=101, i=1.0, d=4.5, f=0.45, mv="push_in"),
 dict(n=98,  i=0.3, d=3.5, f=0.35),
 dict(n=102, i=1.5, d=4.0, f=0.40),
 dict(n=96,  i=0.5, d=4.0, f=0.30),
 # --- B · "Vemos el esfuerzo, las expectativas…" (0:16–0:31)
 dict(n=93,  i=2.0, d=3.5, tr=T("Directional", 0.8, direction=[1, 0]), f=0.45),
 dict(n=94,  i=1.0, d=3.0, f=0.40),
 dict(n=95,  i=2.0, d=3.5, f=0.45),
 dict(n=118, i=0.0, d=5.0, f=0.40),
 # --- C · "Escuchamos, compartimos ideas…" (0:31–0:43)
 dict(n=136, i=0.0, d=3.5, tr=T("DefocusBlur", 0.9), f=0.55),
 dict(n=138, i=1.0, d=3.5, f=0.50),
 dict(n=147, i=0.0, d=2.8, f=0.50),
 dict(n=135, i=0.0, d=2.7, f=0.50),
 # --- D · "Más de 46 años de experiencia, conocimiento y tecnología" (0:43–0:56)
 dict(n=109, i=0.0, d=3.0, tr=T("CrossZoom", 0.8), f=0.50),
 dict(n=112, i=4.0, d=3.5, f=0.50),
 dict(n=66,  i=2.0, d=3.0, f=0.50),
 dict(n=67,  i=6.0, d=3.5, f=0.50),
 dict(n=56,  i=0.0, d=3.5, tr=T("Comb", 0.9), f=0.45),
 # --- E · "Detrás de cada proyecto… nuestra gente, proveedores, clientes" (0:58–1:24)
 dict(n=80,  i=2.0, d=3.5, tr=T("Directional", 0.8, direction=[-1, 0]), f=0.45),
 dict(n=44,  i=0.0, d=3.0, f=0.55),
 dict(n=68,  i=0.0, d=3.0, f=0.45),
 dict(n=143, i=0.0, d=2.5, f=0.50),
 dict(n=81,  i=3.0, d=4.5, tr=T("BandWipe", 0.9), f=0.45),
 dict(split=[93, 29, 71], si=[6.0, 8.0, 1.0], d=3.5, f=0.5),
 dict(n=77,  i=2.0, d=4.5, f=0.45),
 # --- F · "Y cuando estrechamos una mano…" (1:24–1:34)
 dict(n=140, i=0.5, d=3.0, tr=T("DefocusBlur", 0.9), f=0.50),
 dict(n=145, i=1.6, d=5.0, f=0.50),
 dict(n=141, i=5.0, d=2.5, f=0.50),
 # --- G · "Construir no es levantar estructuras, es construir relaciones" + galpón terminado (1:34–1:58)
 dict(n=79,  i=0.0, d=4.0, tr=T("Directional", 0.8, direction=[1, 0]), f=0.50),
 dict(n=8,   i=5.0, d=3.0, f=0.55),
 dict(n=1,   i=0.0, d=5.0, f=0.40),
 dict(n=4,   i=3.0, d=3.5, f=0.50),
 dict(n=12,  i=8.0, d=3.5, f=0.45),
 dict(n=149, i=1.0, d=4.5, tr=T("DefocusBlur", 0.9), f=0.50),
 dict(plate=True, d=3.5, tr=T("CrossZoom", 1.0)),
]

def clip_spec(s, vertical, extra_head, extra_tail, canvas_w):
    d = s["d"] + extra_head + extra_tail
    if s.get("plate"):
        c = {"src": "media/logo/placa_web.png", "dur": round(d, 3), "fit": "contain", "bg": "black"}
    elif "split" in s:
        panels = []
        for n, i in zip(s["split"], s["si"]):
            panels.append({"src": INV[n]["file"].replace("proyectos/zizi/", ""), "in": i})
        c = {"split": panels, "dur": round(d, 3), "gap": 10, "layout": "v" if vertical else "h", "stagger": 0.15}
    else:
        inv = INV[s["n"]]
        need = s["i"] + d
        if need > inv["duracion"] + 0.01:
            ERR.append(f"Plano {s['n']}: pide {need:.2f}s y el clip dura {inv['duracion']:.2f}s")
        c = {"src": inv["file"].replace("proyectos/zizi/", ""), "in": s["i"], "dur": round(d, 3)}
        mv = s.get("mv")
        c["move"] = {"type": mv or "push_in", "amount": 0.04 if not mv else 0.05}
        if vertical:
            c["focus"] = {"x": s.get("f", 0.5), "y": 0.5}
    if s.get("tr"):
        c["transition_in"] = s["tr"]
    return c

def build(vertical):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    clips, t = [], 0.0
    marks = []
    for k, s in enumerate(S):
        head = (S[k]["tr"]["dur"] / 2) if k > 0 and S[k].get("tr") else 0.0
        tail = (S[k + 1]["tr"]["dur"] / 2) if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
        clips.append(clip_spec(s, vertical, head, tail, W))
        marks.append(round(t, 2)); t += s["d"]
    edl = {
        "output": f"entregas/ZIZI_Institucional_{'9x16' if vertical else '16x9'}.mp4",
        "canvas": {"width": W, "height": H, "fps": 25},
        "grade": {"contrast": 1.04, "saturation": 1.04, "temperature": 0.05, "grain": 2},
        "fade": {"in": 0.8, "out": 1.2, "color": "black"},
        "clips": clips,
        "texts": [],
        "subtitles": {"src": "locucion_A.srt", "offset": 0.0, "style": "subtitulo"},
        "overlays": [
            {"template": "dato",
             "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia",
                        "acento": "#FDB913", "y": 330, **({"align": "center"} if vertical else {"x": 190})},
             "start": 44.8, "dur": 3.6}
        ],
        "audio": {"vo": {"src": "media/audio/locucion_A.wav", "start": 0.0, "gain_db": 0}},
        "loudness": {"I": -14, "TP": -1, "LRA": 11},
        "encode": {"crf": 16, "preset": "slow", "maxrate": "30M"},
    }
    return edl, marks, t

if __name__ == "__main__":
    for v in (False, True):
        edl, marks, total = build(v)
        out = AQUI / ("edl_9x16.json" if v else "edl_16x9.json")
        out.write_text(json.dumps(edl, indent=2, ensure_ascii=False))
        print(out.name, f"{len(edl['clips'])} planos, {total:.1f}s")
    if ERR:
        sys.exit("\n".join(sorted(set(ERR))))
    print("cortes (s):", marks)
