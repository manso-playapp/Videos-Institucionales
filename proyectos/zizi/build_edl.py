#!/usr/bin/env python3
"""v2 — Genera edl_16x9.json y edl_9x16.json desde UNA lista de planos (misma historia, dos encuadres).
Cortes en tiempos ABSOLUTOS (s) calzados con la locución limpia. fps nativo 29,97, sin push-in sintético
(medido: la conversión a 25 fps y el zoompan agregaban temblor)."""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
INV = {c["n"]: c for c in json.load(open(AQUI / "inventario/inventario.json"))}
FPS = 29.97
ERR = []

def T(tipo, dur, ease="cubic-in-out", **u):
    t = {"type": "gl:" + tipo, "dur": dur, "ease": ease}
    if u: t["uniforms"] = u
    return t
WHIP   = lambda d=0.35: T("WhipPan", d)
TILT   = lambda d=0.45: T("WhipTilt", d)
BLOOM  = lambda d=0.45: T("BloomDissolve", d)
FLASH  = lambda d=0.40: T("Overexposure", d)
DEFOC  = lambda d=0.45: T("DefocusBlur", d)
LIGHT  = lambda d=0.50: T("LightWipe", d)
XZOOM  = lambda d=0.60: T("CrossZoom", d)

# t = instante de corte (s) en que ENTRA el plano · n = clip del inventario · i = in (s) · f = foco x (vertical)
# blur = en vertical se ve completo con fondo desenfocado (dos personas en cuadro)
S = [
 # A · terreno vacío / "cada proyecto tiene un comienzo"
 dict(t=0.0,  n=101, i=1.0, f=0.45),
 dict(t=3.8,  n=98,  i=0.3, f=0.45),
 dict(t=6.7,  n=102, i=1.5, f=0.40),
 dict(t=10.2, n=96,  i=0.5, f=0.30),
 # B · "vemos el esfuerzo, las expectativas…"
 dict(t=12.2, n=93,  i=2.0, f=0.40, tr=WHIP()),
 dict(t=15.2, n=94,  i=1.0, f=0.40),
 dict(t=17.8, n=95,  i=2.0, f=0.45),
 dict(t=20.8, n=18,  i=8.0, f=0.45),
 # C · "antes de hablar de estructuras, hablamos de proyectos. Escuchamos…"
 dict(t=23.5, n=136, i=0.1, f=0.62, tr=BLOOM()),
 dict(t=26.3, n=138, i=4.0, blur=True),
 dict(t=29.9, n=147, i=0.1, f=0.50),
 dict(t=32.3, n=139, i=9.6, f=0.55),
 dict(t=33.9, n=144, i=2.7, f=0.60, tr=DEFOC()),
 # D · "más de 46 años de experiencia, conocimiento y tecnología"
 dict(t=35.4, n=112, i=6.0, f=0.50, tr=TILT()),
 dict(t=37.4, n=109, i=0.0, f=0.50),
 dict(t=39.2, n=66,  i=1.5, f=0.50, tr=LIGHT()),
 dict(t=41.2, n=67,  i=6.0, f=0.50),
 dict(t=43.0, n=56,  i=0.0, f=0.45, tr=WHIP()),
 # E · "ninguna obra se hace en soledad… nuestra gente, proveedores, clientes"
 dict(t=45.8, n=27,  i=1.0, f=0.45, tr=FLASH()),
 dict(t=48.2, n=28,  i=1.5, f=0.40),
 dict(t=50.9, n=80,  i=2.0, f=0.45),
 dict(t=52.6, n=81,  i=3.0, f=0.45),
 dict(t=54.5, n=68,  i=0.0, f=0.45, tr=WHIP()),
 dict(t=57.0, n=143, i=0.0, blur=True),
 dict(t=58.9, n=44,  i=0.2, f=0.55, tr=DEFOC(0.5)),
 dict(t=61.0, n=18,  i=14.0, f=0.45),
 dict(t=64.4, split=[93, 29, 71], si=[6.0, 8.0, 1.0], tr=BLOOM(0.4)),
 dict(t=67.8, n=77,  i=2.0, f=0.45),
 # F · "y cuando estrechamos una mano…"
 dict(t=68.8, n=145, i=3.2, blur=True, tr=FLASH(0.45)),
 dict(t=72.5, n=148, i=0.1, f=0.50),
 dict(t=74.8, n=149, i=0.2, blur=True, tr=DEFOC()),
 # G · "construir no es solamente levantar estructuras, es construir relaciones que perduren"
 dict(t=78.7, n=79,  i=0.0, f=0.50, tr=WHIP()),
 dict(t=81.9, n=8,   i=5.0, f=0.55),
 dict(t=84.6, n=1,   i=0.0, f=0.40, tr=BLOOM(0.5)),
 dict(t=87.6, n=149, i=5.6, blur=True, tr=FLASH()),
 dict(t=89.5, n=12,  i=8.0, f=0.45, tr=TILT(0.4)),
 dict(t=92.6, plate=True, tr=XZOOM()),
]
END = 96.4

def build(vertical):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    clips = []
    for k, s in enumerate(S):
        t0 = s["t"]; t1 = S[k + 1]["t"] if k + 1 < len(S) else END
        head = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
        tail = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
        d = (t1 - t0) + head + tail
        if s.get("plate"):
            c = {"src": "media/logo/placa_web.png", "dur": round(d, 3), "fit": "contain", "bg": "black"}
        elif "split" in s:
            c = {"split": [{"src": INV[n]["file"].replace("proyectos/zizi/", ""), "in": i}
                           for n, i in zip(s["split"], s["si"])],
                 "dur": round(d, 3), "gap": 10, "layout": "v" if vertical else "h", "stagger": 0.12}
        else:
            inv = INV[s["n"]]; need = s["i"] + d
            if need > inv["duracion"] + 0.02:
                ERR.append(f"n{s['n']}: pide {need:.2f}s (in {s['i']} + {d:.2f}) y el clip dura {inv['duracion']:.2f}s")
            c = {"src": inv["file"].replace("proyectos/zizi/", ""), "in": s["i"], "dur": round(d, 3)}
            if vertical:
                if s.get("blur"):
                    c["fit"], c["bg"] = "contain", "blur"
                else:
                    c["focus"] = {"x": s.get("f", 0.5), "y": 0.5}
        if s.get("tr"): c["transition_in"] = s["tr"]
        clips.append(c)
    title_y = 330
    edl = {
        "output": f"entregas/ZIZI_Institucional_{'9x16' if vertical else '16x9'}.mp4",
        "canvas": {"width": W, "height": H, "fps": FPS},
        "grade": {"contrast": 1.04, "saturation": 1.04, "temperature": 0.04},
        "fade": {"in": 0.7, "out": 1.0, "color": "black"},
        "clips": clips, "texts": [],
        "subtitles": {"src": "locucion_limpia.srt", "offset": 0.0, "style": "subtitulo",
                      **({"size": 22, "y": 880} if vertical else {})},
        "overlays": [
            {"template": "dato", "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia",
                                            "acento": "#FDB913", "y": title_y,
                                            **({"align": "center"} if vertical else {"x": 190})},
             "start": 35.7, "dur": 3.4},
        ],
        "audio": {"vo": {"src": "media/audio/locucion_limpia.wav", "start": 0.0, "gain_db": 0}},
        "loudness": {"I": -14, "TP": -1, "LRA": 11},
        "encode": {"crf": 16, "preset": "slow", "maxrate": "30M"},
    }
    return edl

if __name__ == "__main__":
    for v in (False, True):
        edl = build(v)
        out = AQUI / ("edl_9x16.json" if v else "edl_16x9.json")
        out.write_text(json.dumps(edl, indent=2, ensure_ascii=False))
        print(out.name, f"{len(edl['clips'])} planos")
    if ERR: sys.exit("\n".join(sorted(set(ERR))))
