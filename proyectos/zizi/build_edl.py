#!/usr/bin/env python3
"""v3 — Una lista de planos con tiempos ABSOLUTOS calzados a la locución ElevenLabs (vo_el_cues.json).
Genera edl_16x9.json y edl_9x16.json. 29,97 fps, sin push sintético, look estudio_cine, música Artlist
(Nsee · Forsaken) con ducking, whooshes filtrados en cada transición, títulos animados."""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
import os
MUSIC = os.environ.get("ZIZI_MUSIC", "media/music/bt_summer.wav")
TAG = os.environ.get("ZIZI_TAG", "")
INV = {c["n"]: c for c in json.load(open(AQUI / "inventario/inventario.json"))}
FPS, ERR = 29.97, []

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

# v4 — tiempos ABSOLUTOS sobre la locución original limpia (vo_a2.wav, palabras en media/audio/vo_a2.json)
# t = corte donde ENTRA el plano · n = clip del inventario · i = in en la fuente · f = foco x (vertical)
S = [
 dict(t=0.0,  n=118, i=6.95, f=0.45),                      # terreno verde vacío
 dict(t=3.6,  n=99,  i=0.5, f=0.35, tr=DEFOC()),
 dict(t=6.4,  n=101, i=1.0, f=0.45),                       # "terreno vacío… una idea"
 dict(t=11.2, n=98,  i=0.3, f=0.40, tr=WHIP()),            # "Nosotros vemos en ese espacio"
 dict(t=15.4, n=93,  i=2.0, f=0.42),                       # "el esfuerzo"
 dict(t=18.6, n=95,  i=2.0, f=0.45),                       # "quienes nos eligen"
 dict(t=22.3, n=136, i=0.1, f=0.62, tr=BLOOM()),           # "Por eso, en ZIZI…"
 dict(t=26.9, n=147, i=0.1, f=0.50),                       # "proyectos / escuchamos"
 dict(t=29.5, n=138, i=4.0, blur=True, tr=WHIP()),         # "compartimos ideas… juntos"
 dict(t=33.2, n=144, i=2.7, f=0.62, tr=FLASH()),           # "+46 años" (dueño de ZIZI)
 dict(t=36.6, n=109, i=0.0, f=0.50),                       # "conocimiento"
 dict(t=38.9, n=112, i=6.0, f=0.50, tr=TILT()),            # "tecnología"
 dict(t=41.0, n=66,  i=1.5, f=0.50, tr=LIGHT()),           # "una empresa que sabe construir"
 dict(t=44.6, n=27,  i=1.0, f=0.45, tr=DEFOC()),           # "ninguna obra se hace en soledad"
 dict(t=48.2, n=28,  i=1.5, f=0.40),                       # "el trabajo de nuestra gente"
 dict(t=51.4, n=68,  i=0.0, f=0.45, tr=WHIP()),            # "compromiso de nuestros proveedores"
 dict(t=53.6, n=135, i=0.0, f=0.50),                       # "confianza de nuestros clientes" (Goipat)
 dict(t=56.4, n=81,  i=3.0, f=0.45, tr=BLOOM()),           # "personas… desde distintos lugares"
 dict(t=59.6, split=[104, 77, 80], si=[6.0, 2.0, 2.0]),    # "hacen posible…"
 dict(t=62.6, n=10,  i=3.0, f=0.45),                       # "…en realidades"
 dict(t=65.0, n=145, i=2.6, blur=True, tr=FLASH()),        # "cuando estrechamos una mano"
 dict(t=69.3, n=142, i=3.6, blur=True),                    # "responsabilidad, cercanía, compromiso"
 dict(t=73.9, n=79,  i=0.0, f=0.50, tr=WHIP()),            # "construir no es solamente levantar estructuras"
 dict(t=77.6, n=8,   i=5.0, f=0.55),                       # "relaciones que perduren"
 dict(t=80.6, n=1,   i=0.0, f=0.40, tr=BLOOM()),           # galpón terminado (respiro)
 dict(t=83.2, n=149, i=0.2, blur=True, tr=FLASH()),        # "ZIZI es la gente" — sonriendo (sin pulgares)
 dict(t=86.2, n=12,  i=8.0, f=0.45, tr=TILT()),            # "construimos cultura de trabajo"
 dict(t=89.6, plate=True, tr=XZOOM()),
]
END = 95.4

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

    def claim(start, dur, items, kicker="", size=None, **kw):
        if isinstance(items, str): items = [(items, 0)]
        p = {"kicker": kicker, "items": [{"texto": t, "t": tt} for t, tt in items], "dur": dur, "acento": "#FDB913"}
        if vertical: p.update(align="center", y=330, size=size or 66, ks=17)
        else:        p.update(align="left", x=150, y=900, size=size or 128)
        p.update(kw)
        return {"template": "claim", "params": p, "start": start, "dur": dur}
    ov = [
        claim(1.4, 4.2, "Tiene un comienzo", "Cada proyecto", size=(56 if vertical else 112)),
        claim(25.0, 3.8, "Hablamos de proyectos", "Antes de hablar de estructuras", size=(46 if vertical else 104)),
        {"template": "dato", "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia", "acento": "#FDB913",
                                         "y": 330 if not vertical else 300, **({"align": "center"} if vertical else {"x": 150})},
         "start": 34.9, "dur": 3.0},
        claim(37.25, 3.0, [("Conocimiento", 0), ("Tecnología", 1.05)], "Experiencia que respalda"),
        claim(50.6, 5.3, [("Gente", 0), ("Compromiso", 1.1), ("Confianza", 3.2)], "Ninguna obra se hace en soledad"),
        claim(69.3, 5.0, [("Responsabilidad", 0), ("Cercanía", 1.7), ("Compromiso", 3.55)], "Nuestra manera de trabajar"),
        claim(78.4, 3.0, "Relaciones que perduren", "Construir", size=(48 if vertical else 104)),
        claim(83.5, 4.1, [("ZIZI es la gente", 0), ("Cultura de trabajo", 1.95)], "", size=(56 if vertical else 116)),
        {"template": "luz", "params": {"semilla": 4}, "start": 80.3, "dur": 2.6, "opacity": 0.5},
    ]
    edl = {
        "output": f"entregas/ZIZI_Institucional_{'9x16' if vertical else '16x9'}{TAG}.mp4",
        "canvas": {"width": W, "height": H, "fps": FPS},
        "grade": {"lut": "assets/luts/estudio_cine.cube", "contrast": 1.03, "saturation": 1.02, "grain": 2},
        "fade": {"in": 1.0, "out": 1.6, "color": "black"},
        "clips": clips, "texts": [], "overlays": ov,
        "audio": {
            "vo": {"src": "media/audio/vo_a2.wav", "start": 0.0, "gain_db": 0},
            "music": {"src": MUSIC, "in": 0, "gain_db": -9, "fade_in": 1.5, "fade_out": 1.8, "end": END},
            "duck_music_under_vo": True,
            "duck": {"threshold": 0.02, "ratio": 4.5, "attack": 120, "release": 900},
            "sfx": sfx,
        },
        "loudness": {"I": -14, "TP": -1, "LRA": 11},
        "encode": {"crf": 16, "preset": "slow", "maxrate": "30M"},
    }
    if vertical:   # en redes se ve sin sonido: subtítulos de la locución real
        edl["subtitles"] = {"src": "locucion_a2.srt", "offset": 0.0, "style": "subtitulo", "size": 22, "y": 1620}
    return edl

if __name__ == "__main__":
    for v in (False, True):
        edl = build(v); out = AQUI / (("edl_9x16" if v else "edl_16x9") + TAG + ".json")
        out.write_text(json.dumps(edl, indent=2, ensure_ascii=False)); print(out.name, len(edl["clips"]), "planos", len(edl["audio"]["sfx"]), "sfx")
    if ERR: sys.exit("\n".join(sorted(set(ERR))))
