#!/usr/bin/env python3
"""v3 — Una lista de planos con tiempos ABSOLUTOS calzados a la locución ElevenLabs (vo_el_cues.json).
Genera edl_16x9.json y edl_9x16.json. 29,97 fps, sin push sintético, look estudio_cine, música Artlist
(Nsee · Forsaken) con ducking, whooshes filtrados en cada transición, títulos animados."""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
INV = {c["n"]: c for c in json.load(open(AQUI / "inventario/inventario.json"))}
FPS, ERR = 29.97, []
END = 98.2

def T(tipo, dur, **u):
    t = {"type": "gl:" + tipo, "dur": dur, "ease": "cubic-in-out"}
    if u: t["uniforms"] = u
    return t
WHIP  = lambda d=0.38: T("WhipPan", d)
TILT  = lambda d=0.45: T("WhipTilt", d)
BLOOM = lambda d=0.5:  T("BloomDissolve", d)
FLASH = lambda d=0.42: T("Overexposure", d)
DEFOC = lambda d=0.5:  T("DefocusBlur", d)
LIGHT = lambda d=0.5:  T("LightWipe", d)
XZOOM = lambda d=0.7:  T("CrossZoom", d)

# t = corte (s) donde ENTRA el plano · n = clip del inventario · i = in en la fuente · f = foco x (vertical)
# blur = en vertical se ve completo sobre fondo desenfocado (dos personas en cuadro)
S = [
 dict(t=0.0,  n=118, i=7.05, f=0.45),                       # TERRENO VERDE VACÍO (apertura)
 dict(t=3.5,  n=99,  i=0.5, f=0.35, tr=DEFOC()),
 dict(t=6.2,  n=101, i=1.0, f=0.45),
 dict(t=10.4, n=98,  i=0.3, f=0.40, tr=WHIP()),
 dict(t=14.9, n=93,  i=2.0, f=0.42),
 dict(t=17.7, n=95,  i=2.0, f=0.45),
 dict(t=20.5, n=136, i=0.1, f=0.62, tr=BLOOM()),           # los dos con los planos
 dict(t=25.0, n=147, i=0.1, f=0.50),
 dict(t=27.5, n=138, i=4.0, blur=True, tr=WHIP()),
 dict(t=30.7, n=144, i=2.7, f=0.62, tr=FLASH()),           # dueño de ZIZI, "+46"
 dict(t=33.9, n=109, i=0.0, f=0.50),
 dict(t=36.5, n=112, i=6.0, f=0.50, tr=TILT()),
 dict(t=38.5, n=66,  i=1.5, f=0.50, tr=LIGHT()),
 dict(t=41.0, n=27,  i=1.0, f=0.45, tr=DEFOC()),           # "nuestra gente"
 dict(t=44.0, n=28,  i=1.5, f=0.40),
 dict(t=47.0, n=80,  i=2.0, f=0.45, tr=WHIP()),
 dict(t=49.6, n=68,  i=0.0, f=0.45),
 dict(t=52.2, n=81,  i=3.0, f=0.45, tr=BLOOM()),
 dict(t=55.2, split=[104, 77, 81], si=[6.0, 2.0, 12.0]),
 dict(t=58.0, n=145, i=2.9, blur=True, f=0.5, tr=FLASH()), # APRETÓN DE MANOS
 dict(t=62.0, n=149, i=0.5, blur=True),
 dict(t=65.5, n=140, i=0.5, f=0.50),
 dict(t=68.4, n=79,  i=0.0, f=0.50, tr=WHIP()),
 dict(t=72.0, n=8,   i=5.0, f=0.55),
 dict(t=75.0, n=1,   i=0.0, f=0.40, tr=BLOOM()),           # galpón terminado
 dict(t=77.5, n=149, i=4.3, blur=True, tr=FLASH()),        # "ZIZI es la gente"
 dict(t=80.7, n=12,  i=8.0, f=0.45, tr=TILT()),
 dict(t=84.2, n=4,   i=3.0, f=0.50),
 dict(t=87.4, n=10,  i=3.0, f=0.45, tr=LIGHT()),
 dict(t=91.0, plate=True, tr=XZOOM()),
]

def build(vertical):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    clips, sfx = [], []
    for k, s in enumerate(S):
        t0 = s["t"]; t1 = S[k + 1]["t"] if k + 1 < len(S) else END
        head = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
        tail = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
        d = (t1 - t0) + head + tail
        if s.get("plate"):
            c = {"src": "media/logo/placa_web.png", "dur": round(d, 3), "fit": "contain", "bg": "black"}
        elif "split" in s:
            c = {"split": [{"src": INV[n]["file"].replace("proyectos/zizi/", ""), "in": i}
                           for n, i in zip(s["split"], s["si"])], "dur": round(d, 3), "gap": 10,
                 "layout": "v" if vertical else "h", "stagger": 0.12}
        else:
            inv = INV[s["n"]]; need = s["i"] + d
            if need > inv["duracion"] + 0.02:
                ERR.append(f"n{s['n']}: pide {need:.2f}s (in {s['i']} + {d:.2f}) y el clip dura {inv['duracion']:.2f}s")
            c = {"src": inv["file"].replace("proyectos/zizi/", ""), "in": s["i"], "dur": round(d, 3)}
            if vertical:
                if s.get("blur"): c["fit"], c["bg"] = "contain", "blur"
                else: c["focus"] = {"x": s.get("f", 0.5), "y": 0.5}
        if s.get("tr"):
            c["transition_in"] = s["tr"]
            sfx.append({"src": "media/sfx/whoosh_airy.wav" if s["tr"]["type"] in ("gl:WhipPan", "gl:WhipTilt") else "media/sfx/whoosh_reverb.wav",
                        "at": round(max(t0 - s["tr"]["dur"] / 2 - 0.05, 0), 2),
                        "gain_db": -13 if s["tr"]["type"] in ("gl:WhipPan", "gl:WhipTilt") else -15})
        clips.append(c)

    def titulo(txt, start, dur, y, size, mode="palabras", **kw):
        p = {"texto": txt, "modo": mode, "size": size, "y": y, "peso": 600, "dur": dur, "color": "#ffffff", **kw}
        if vertical: p["align"] = "center"
        return {"template": "titulo", "params": p, "start": start, "dur": dur}
    ytitle = 1480 if vertical else 880
    ov = [
        titulo("Cada proyecto tiene un comienzo", 1.5, 3.6, 540 if not vertical else 900, 84 if not vertical else 70, "palabras"),
        {"template": "dato", "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia", "acento": "#FDB913",
                                         "y": 330, **({"align": "center"} if vertical else {"x": 190})},
         "start": 31.4, "dur": 3.6},
        titulo("Responsabilidad", 63.0, 1.7, ytitle, 78 if not vertical else 60, "letras", fuente="Barlow Condensed", mayus=True, peso=600, **({} if vertical else {"align": "left", "x": 190})),
        titulo("Cercanía", 64.7, 1.4, ytitle, 78 if not vertical else 60, "letras", fuente="Barlow Condensed", mayus=True, peso=600, **({} if vertical else {"align": "left", "x": 190})),
        titulo("Compromiso", 65.9, 1.9, ytitle, 78 if not vertical else 60, "letras", fuente="Barlow Condensed", mayus=True, peso=600, **({} if vertical else {"align": "left", "x": 190})),
        titulo("ZIZI es la gente.", 77.6, 3.0, 880 if not vertical else 1480, 92 if not vertical else 70, "palabras"),
        {"template": "luz", "params": {"semilla": 4}, "start": 74.6, "dur": 2.8, "opacity": 0.55},
    ]
    edl = {
        "output": f"entregas/ZIZI_Institucional_{'9x16' if vertical else '16x9'}.mp4",
        "canvas": {"width": W, "height": H, "fps": FPS},
        "grade": {"lut": "assets/luts/estudio_cine.cube", "contrast": 1.03, "saturation": 1.02, "grain": 2},
        "fade": {"in": 1.0, "out": 1.6, "color": "black"},
        "clips": clips, "texts": [], "overlays": ov,
        "audio": {
            "vo": {"src": "media/audio/vo_el.wav", "start": 0.0, "gain_db": 0},
            "music": {"src": "media/music/forsaken.wav", "in": 0, "gain_db": -7, "fade_in": 1.2, "fade_out": 2.4, "end": END},
            "duck_music_under_vo": True,
            "duck": {"threshold": 0.02, "ratio": 4.5, "attack": 120, "release": 900},
            "sfx": sfx,
        },
        "loudness": {"I": -14, "TP": -1, "LRA": 11},
        "encode": {"crf": 16, "preset": "slow", "maxrate": "30M"},
    }
    if vertical:   # en redes se ve sin sonido: subtítulos de la locución real
        edl["subtitles"] = {"src": "media/audio/vo_el.srt", "offset": 0.0, "style": "subtitulo", "size": 22, "y": 1620}
    return edl

if __name__ == "__main__":
    for v in (False, True):
        edl = build(v); out = AQUI / ("edl_9x16.json" if v else "edl_16x9.json")
        out.write_text(json.dumps(edl, indent=2, ensure_ascii=False)); print(out.name, len(edl["clips"]), "planos", len(edl["audio"]["sfx"]), "sfx")
    if ERR: sys.exit("\n".join(sorted(set(ERR))))
