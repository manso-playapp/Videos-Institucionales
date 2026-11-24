#!/usr/bin/env python3
"""v3 — Una lista de planos con tiempos ABSOLUTOS calzados a la locución ElevenLabs (vo_el_cues.json).
Genera edl_16x9.json y edl_9x16.json. 29,97 fps, sin push sintético, look estudio_cine, música Artlist
(Nsee · Forsaken) con ducking, whooshes filtrados en cada transición, títulos animados."""
import json, sys
from pathlib import Path
AQUI = Path(__file__).parent
import os
MUSIC = os.environ.get("ZIZI_MUSIC", "")   # todavía sin música elegida
TAG = os.environ.get("ZIZI_TAG", "")
VO = {"": "media/audio/vo_a2.wav", "masc": "media/audio/vo_masc.wav", "carlos": "media/audio/vo_carlos.wav"}[os.environ.get("ZIZI_VO", "")]   # locución original (default) o voz masculina alternativa
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

# v5 — tiempos ABSOLUTOS sobre la locución corregida (sin el arranque fallido; palabras en media/audio/vo_a2.json)
# t = corte donde ENTRA el plano · n = clip del inventario · i = in en la fuente · f = foco x (vertical)
S = [
 dict(t=0.0,  n=118, i=6.6, f=0.45),                       # terreno verde vacío · "Cada proyecto tiene un comienzo"
 dict(t=4.0,  n=99,  i=0.5, f=0.35, tr=DEFOC()),           # "a veces es solamente un terreno vacío"
 dict(t=6.6,  n=101, i=1.0, f=0.45),                       # "otras veces una idea…"
 dict(t=11.5, n=98,  i=0.3, f=0.40, tr=WHIP()),            # "Nosotros vemos en ese espacio…"
 dict(t=15.4, n=93,  i=2.0, f=0.42),                       # "una futura construcción"
 dict(t=16.9, n=95,  i=2.0, f=0.45),                       # "vemos el esfuerzo, las expectativas"
 dict(t=19.4, n=18,  i=8.0, f=0.45),                       # "las ganas de crecer de quienes nos eligen"
 dict(t=22.2, n=136, i=0.0, f=0.62, tr=BLOOM()),           # "Por eso, en ZIZI… hablamos de proyectos"
 dict(t=26.2, n=137, i=0.2, f=0.50),                       # "de proyectos" (plano de la obra)
 dict(t=27.8, n=147, i=0.1, f=0.50),                       # "Escuchamos"
 dict(t=29.1, n=138, i=4.0, blur=True, tr=WHIP()),         # "compartimos ideas y buscamos juntos"
 dict(t=31.3, n=139, i=9.6, f=0.55),                       # "la mejor solución"
 dict(t=33.5, n=144, i=2.7, f=0.62, tr=FLASH()),           # "+46 años de experiencia" (dueño de ZIZI)
 dict(t=37.3, n=109, i=0.0, f=0.50),                       # "conocimiento"
 dict(t=38.3, n=112, i=6.0, f=0.50, tr=TILT()),            # "tecnología"
 dict(t=40.8, n=66,  i=1.5, f=0.50, tr=LIGHT()),           # "el respaldo de una empresa que sabe construir"
 dict(t=44.4, n=27,  i=1.0, f=0.45, tr=DEFOC()),           # "ninguna obra se hace en soledad"
 dict(t=48.0, n=28,  i=1.5, f=0.40),                       # "el trabajo de nuestra gente"
 dict(t=51.4, n=68,  i=0.0, f=0.45, tr=WHIP()),            # "el compromiso de nuestros proveedores"
 dict(t=53.5, n=135, i=0.0, f=0.50),                       # "la confianza de nuestros clientes" (dueño de Goipat)
 dict(t=56.3, n=81,  i=3.0, f=0.45, tr=BLOOM()),           # "Personas que, desde distintos lugares"
 dict(t=59.0, split=[104, 77, 80], si=[6.0, 2.0, 2.0]),    # "hacen posible que las ideas se conviertan"
 dict(t=60.9, n=10,  i=3.0, f=0.45),                       # "en realidades" (galpón terminado)
 dict(t=62.6, n=145, i=2.6, blur=True, tr=FLASH()),        # "Y cuando estrechamos una mano…"
 dict(t=66.9, n=142, i=3.3, blur=True),                    # "responsabilidad, cercanía, compromiso"
 dict(t=71.8, n=4,   i=3.0, f=0.50, tr=WHIP()),            # "construir no es solamente levantar estructuras"
 dict(t=75.6, n=149, i=0.2, blur=True, tr=BLOOM()),        # "es construir relaciones que perduren" (los dos dueños)
 dict(t=78.6, n=8,   i=5.0, f=0.55),                       # pausa: banderas argentina y ZIZI
 dict(t=81.3, n=44,  i=0.2, f=0.55, tr=FLASH()),           # "ZIZI es la gente" (retrato de operario)
 dict(t=82.9, n=43,  i=0.6, f=0.50),                       # "construimos" (operarios caminando)
 dict(t=84.3, n=82,  i=1.0, f=0.45),                       # "cultura de trabajo" (equipo en el techo)
 dict(t=87.2, n=1,   i=0.0, f=0.40, tr=BLOOM()),           # galpón terminado
 dict(t=89.8, plate=True, tr=XZOOM()),
]
END = 95.2

# Edición hecha por el estudio en el artefacto (doc selecciones/horizontal → edicion_horizontal.json): si existe, manda sobre S.
# Ahí "in" es el punto de la fuente que se ve en el corte t (sin contar el solape de la transición).
UHD = bool(os.environ.get("ZIZI_4K"))
DIN = os.environ.get("ZIZI_VERSION", "") == "dinamica"     # versión corta y dinámica: Carlos a ritmo natural (1:15) + ráfagas
VER = os.environ.get("ZIZI_VERSION", "")                     # "" = edición larga del estudio · "dinamica" · "emocional"
EDIC = AQUI / {"dinamica": "edicion_dinamica.json", "emocional": "edicion_emocional.json"}.get(VER, "edicion_horizontal.json")
if DIN: END = 79.4; VO = "media/audio/vo_carlos_c.wav"
# Emocional (25-11): el audio es la mezcla final que armó Javier (locución de Lara + música); no se le suma música ni ducking.
EMO = VER == "emocional"
if EMO:
    import numpy as _np
    _m = json.load(open(AQUI / "mapa_tiempos_emocional.json")); END = 86.8; VO = "media/audio/mezcla_javier.wav"
    def REMAP(t): return round(float(_np.interp(t, [0] + _m["viejo"], [0] + _m["nuevo"])), 2)   # tiempos de la locución anterior -> mezcla nueva, palabra por palabra
# Opciones de look, textura y música elegidas en el editor (campo fx de la edición guardada)
FX = (json.load(open(EDIC)).get("fx") or {}) if EDIC.exists() and not os.environ.get("ZIZI_SIN_EDICION") else {}
LUT = {"calido": "assets/luts/estudio_calido.cube"}.get(FX.get("look"), "assets/luts/estudio_limpio.cube")
BASE_G = {"saturation": 1.05, "temperature": 0.06, **({"grain": 3} if FX.get("grano") else {}), **({"vignette": True} if FX.get("vineta") else {})}
if not MUSIC and FX.get("musica") and (AQUI / f"media/music/{FX['musica']}.wav").exists(): MUSIC = f"media/music/{FX['musica']}.wav"
if not os.environ.get("ZIZI_VO") and not DIN and not EMO: VO = {"masc": "media/audio/vo_masc.wav", "carlos": "media/audio/vo_carlos.wav"}.get(FX.get("voz"), "media/audio/vo_a2.wav")
if EMO: MUSIC = ""
MUS_GAIN = {"glaciers": -8, "travelling_light": -4}.get(FX.get("musica"), -7)     # 24-11: el estudio pidió la música más presente
MUS_IN = {"glaciers": 4.0}.get(FX.get("musica"), 0.0)      # desde dónde entra el tema, para que llegue rápido a pleno
TR_DUR = {"WhipPan": 0.38, "WhipTilt": 0.45, "BloomDissolve": 0.5, "Overexposure": 0.42, "DefocusBlur": 0.5, "LightWipe": 0.5, "CrossZoom": 0.7}
if EDIC.exists() and not os.environ.get("ZIZI_SIN_EDICION"):
    _meta = {s["n"]: {k: s[k] for k in ("f", "blur") if k in s} for s in S if "n" in s}
    S2 = []
    for e in json.load(open(EDIC))["slots"]:
        s = {"t": e["t"], "exacto": True}
        if e["tipo"] == "placa": s["plate"] = True
        elif e["tipo"] == "negro": s["negro"] = True      # espacio reservado sin toma: sale negro
        elif e["tipo"] == "split": s["split"], s["si"] = e["tomas"], e["ins"]
        else: s.update(n=e["n"], i=e["in"], v=float(e.get("v", 1)), luz=bool(e.get("luz")), **_meta.get(e["n"], {}))
        if e.get("tr") and e["tr"] != "Corte": s["tr"] = T(e["tr"], 0.7 if (VER == "emocional" and e["tr"] == "Fade") else TR_DUR.get(e["tr"], 0.5))   # disolvencias largas en la emocional
        S2.append(s)
    S = S2
    # una transición necesita material extra de las dos tomas (se solapan): si a una toma no le sobra, la transición se acorta
    for k, s in enumerate(S):
        if "n" not in s: continue
        libre = (INV[s["n"]]["duracion"] / float(s.get("v", 1))) - ((S[k + 1]["t"] if k + 1 < len(S) else END) - s["t"]) - 0.04
        for j in (k, k + 1):
            if 0 < j < len(S) and S[j].get("tr"):
                S[j]["tr"] = dict(S[j]["tr"], dur=round(max(0.0, min(S[j]["tr"]["dur"], libre)), 2))
                if S[j]["tr"]["dur"] < 0.12: S[j].pop("tr")
# Regla del estudio (24-11): ninguna toma dura más de 3 s en pantalla, contando lo que se ve durante las disolvencias
MAXP = 3.0
if EDIC.exists() and not os.environ.get("ZIZI_SIN_EDICION"):
    for _ in range(3):
        for k, s in enumerate(S):
            if s.get("plate"): continue
            d = (S[k + 1]["t"] if k + 1 < len(S) else END) - s["t"]
            hd = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
            tl = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
            sobra = d + hd + tl - MAXP
            if sobra > 0.005 and hd + tl > 0:
                f = max(0.0, 1 - sobra / (hd + tl))
                for j in (k, k + 1):
                    if 0 < j < len(S) and S[j].get("tr"): S[j]["tr"] = dict(S[j]["tr"], dur=round(S[j]["tr"]["dur"] * f, 2))
    for s in S:
        if s.get("tr") and s["tr"]["dur"] < 0.12: s.pop("tr")
NIV = json.load(open(AQUI / "niveles.json"))
def niveles(n):
    g = dict(NIV.get(str(n), {}).get("grade", {}))
    if "gamma" in g: g["gamma"] = min(g["gamma"], 1.3)
    return g

def build(vertical):
    MUS = ({"music": {"src": MUSIC, "in": MUS_IN, "gain_db": MUS_GAIN, "fade_in": 1.5, "fade_out": 1.8, "end": END},
            "duck_music_under_vo": True, "duck": {"threshold": 0.02, "ratio": 3.0, "attack": 120, "release": 900}} if MUSIC else {})
    W, H = (1080, 1920) if vertical else (1920, 1080)
    if UHD: W, H = W * 2, H * 2                       # master 4K (3840x2160): el material de dron es 4K nativo
    clips, sfx = [], []
    for k, s in enumerate(S):
        t0 = s["t"]; t1 = S[k + 1]["t"] if k + 1 < len(S) else END
        head = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
        tail = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
        d = (t1 - t0) + head + tail
        if s.get("plate"):
            # placa de cierre animada (logo vectorial que se arma): se renderiza una vez con tools/motion.py y entra como plano
            cierre = AQUI / ("render/cierre_zizi_4k.mov" if UHD else "render/cierre_zizi.mov"); pc = {"logo": "proyectos/zizi/motion/logo_zizi.json", "web": "WWW.TINGLADOSZIZI.COM.AR", "dur": round(d + 0.4, 2)}
            firma = cierre.with_suffix(".json")
            if not cierre.exists() or not firma.exists() or json.load(open(firma)) != pc:
                import subprocess; cierre.parent.mkdir(exist_ok=True)
                subprocess.run(["python3", str(AQUI.parent.parent / "tools/motion.py"), "plantilla", "cierre_vector", "-p", json.dumps(pc), "-o", str(cierre),
                                "--size", "3840x2160" if UHD else "1920x1080", "--fps", str(FPS)], check=True, capture_output=True); json.dump(pc, open(firma, "w"))
            c = {"src": "render/" + cierre.name, "in": 0, "dur": round(d, 3), "global_grade": False}
        elif s.get("negro"):
            neg = AQUI / "media/negro.png"
            if not neg.exists():
                import subprocess; subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x180", "-frames:v", "1", str(neg)], check=True)
            c = {"src": "media/negro.png", "dur": round(d, 3), "fit": "contain", "bg": "black"}
        elif "split" in s:
            c = {"split": [{"src": INV[n]["file"].replace("proyectos/zizi/", ""), "in": i, **({"grade": niveles(n)} if niveles(n) else {})}
                           for n, i in zip(s["split"], [round(max(0.0, x - head), 3) if s.get("exacto") else x for x in s["si"]])], "dur": round(d, 3), "gap": 10,
                 "layout": "v" if vertical else "h", "stagger": 0.12}
        else:
            inv = INV[s["n"]]
            vv = float(s.get("v", 1))             # velocidad de la toma (editor): 2 = el doble de rápido; consume el doble de material
            if s.get("exacto"): s = {**s, "i": round(max(0.0, s["i"] - head * vv), 3)}   # el cuadro elegido cae justo en el corte
            if s.get("exacto"): s = dict(s, i=round(max(0.0, min(s["i"], inv["duracion"] - d * vv - 0.02)), 3))        # si no alcanza la cola, arranca un poco antes
            need = s["i"] + d * vv
            if need > inv["duracion"] + 0.02:
                ERR.append(f"n{s['n']}: pide {need:.2f}s (in {s['i']} + {d:.2f}) y el clip dura {inv['duracion']:.2f}s")
            c = {"src": inv["file"].replace("proyectos/zizi/", ""), "in": s["i"], "dur": round(d, 3)}
            if vv != 1: c["speed"] = vv
            if niveles(s["n"]): c["grade"] = niveles(s["n"])
            if FX.get("look") == "personas" and "IMG_" in inv["file"]:      # look cálido solo en los planos de personas (celulares)
                c["grade"] = {**c.get("grade", {}), **BASE_G, "lut": "assets/luts/estudio_calido.cube"}; c["global_grade"] = False
            if vertical:
                if s.get("blur"): c["fit"], c["bg"] = "contain", "blur"
                else: c["focus"] = {"x": s.get("f", 0.5), "y": 0.5}
        if s.get("tr"):
            c["transition_in"] = s["tr"]
            pass   # sin efectos de sonido en las transiciones: hay locución encima (pedido del estudio)
        clips.append(c)

    F = 0.5 if vertical else 1.0                       # el vertical mide 607 unidades de ancho: la tipografía va a la mitad
    def L(texto, size, t=0, fuente="display", **kw):
        return {"texto": texto, "size": round(size * F), "fuente": fuente, "t": t, **kw}
    def frase(start, dur, lineas, y=None):
        p = {"lineas": lineas, "dur": dur, "acento": "#FDB913"}
        if vertical: p.update(align="center", y=y or 400)
        else:        p.update(align="left", x=150, y=y or 520)
        return {"template": "frase", "params": p, "start": start, "dur": dur}
    lead = dict(fuente="texto", peso=300)
    lugar = {"lugar": "Santa Fe", "pais": "Argentina", "acento": "#FDB913", "dur": 3.8, "size": round(78 * (0.6 if vertical else 1))}
    lugar.update(dict(x=40, y=70) if vertical else dict(x=150, y=130))
    if DIN:      # tiempos sobre la locución compacta (media/audio/vo_carlos_c.json)
        lugar["dur"] = 3.2
        ov = [
            {"template": "lugar", "params": lugar, "start": 0.3, "dur": 3.2},
            frase(0.45, 3.4, [L("Cada proyecto tiene un", 54, 0, **lead), L("comienzo", 240, 1.6, mayus=True, punto=True)]),
            frase(20.5, 3.2, [L("Antes de hablar de estructuras,", 50, 0, **lead), L("hablamos de", 104, 1.3, peso=500, mayus=True), L("proyectos", 220, 2.3, mayus=True, punto=True)]),
            {"template": "dato", "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia", "acento": "#FDB913",
                                             "y": 330 if not vertical else 300, **({"align": "center"} if vertical else {"x": 150})}, "start": 29.7, "dur": 2.3},
            frase(31.95, 2.6, [L("conocimiento", 150, 0, mayus=True), L("y tecnología", 150, 0.75, mayus=True, punto=True, color="acento")]),
            frase(43.2, 5.4, [L("Nuestra gente", 118, 0, mayus=True, punto=True), L("Nuestros proveedores", 118, 2.0, mayus=True, punto=True), L("Nuestros clientes", 118, 4.1, mayus=True, punto=True)]),
            frase(52.2, 2.5, [L("Las ideas se convierten en", 52, 0, **lead), L("realidades", 220, 1.3, mayus=True, punto=True)]),
            frase(58.9, 4.6, [L("Responsabilidad", 128, 0, mayus=True, punto=True), L("Cercanía", 128, 1.45, mayus=True, punto=True), L("Compromiso", 128, 3.4, mayus=True, punto=True, color="acento")]),
            frase(67.0, 2.7, [L("Construir", 54, 0, **lead), L("relaciones", 220, 0.6, mayus=True), L("que perduren", 104, 1.25, peso=500, mayus=True, punto=True)]),
            frase(70.0, 4.2, [L("ZIZI es la gente", 176, 0, mayus=True, punto=True), L("Construimos cultura de trabajo", 58, 2.0, **lead)]),
        ]
    else:
        ov = [
            {"template": "lugar", "params": lugar, "start": 0.3, "dur": 3.8},      # localizador de apertura (dato dado por el estudio)
            frase(1.5, 4.2, [L("Cada proyecto tiene un", 54, 0, **lead), L("comienzo", 240, 1.55, mayus=True, punto=True)]),
            frase(24.3, 3.6, [L("Antes de hablar de estructuras,", 50, 0, **lead), L("hablamos de", 104, 1.25, peso=500, mayus=True),
                              L("proyectos", 220, 1.9, mayus=True, punto=True)]),
            {"template": "dato", "params": {"valor": "46", "prefijo": "+", "etiqueta": "años de experiencia", "acento": "#FDB913",
                                             "y": 330 if not vertical else 300, **({"align": "center"} if vertical else {"x": 150})},
             "start": 34.9, "dur": 2.6},
            frase(37.4, 3.3, [L("conocimiento", 150, 0, mayus=True), L("y tecnología", 150, 0.95, mayus=True, punto=True, color="acento")]),
            frase(50.5, 5.6, [L("Nuestra gente", 118, 0, mayus=True, punto=True), L("Nuestros proveedores", 118, 1.9, mayus=True, punto=True),
                              L("Nuestros clientes", 118, 4.25, mayus=True, punto=True)]),
            frase(59.6, 3.0, [L("Las ideas se convierten en", 52, 0, **lead), L("realidades", 220, 1.6, mayus=True, punto=True)]),
            frase(67.2, 4.6, [L("Responsabilidad", 128, 0, mayus=True, punto=True), L("Cercanía", 128, 1.5, mayus=True, punto=True),
                              L("Compromiso", 128, 3.3, mayus=True, punto=True, color="acento")]),
            frase(75.9, 2.7, [L("Construir", 54, 0, **lead), L("relaciones", 220, 0.5, mayus=True), L("que perduren", 104, 1.45, peso=500, mayus=True, punto=True)]),
            frase(81.4, 4.4, [L("ZIZI es la gente", 176, 0, mayus=True, punto=True), L("Construimos cultura de trabajo", 58, 1.75, **lead)]),
        ]
    if EMO:
        for o in ov: o["start"] = REMAP(o["start"])
        for a_, b_ in zip(ov, ov[1:]):                 # la mezcla nueva tiene pausas más cortas: ningún texto pisa al siguiente
            if a_["template"] == "frase" and b_["template"] == "frase" and a_["start"] + a_["dur"] > b_["start"] - 0.1:
                a_["dur"] = round(b_["start"] - a_["start"] - 0.1, 2); a_["params"] = dict(a_["params"], dur=a_["dur"])
    for k, s in enumerate(S):                           # luz cálida orgánica sobre las tomas marcadas en el editor
        if s.get("luz"):
            d = (S[k + 1]["t"] if k + 1 < len(S) else END) - s["t"]
            ov.append({"template": "luz", "params": {"semilla": 3 + k}, "start": s["t"], "dur": round(min(max(d, 1.2), 4.0), 2), "opacity": 0.6})
    edl = {
        "output": f"entregas/ZIZI_Institucional_{'9x16' if vertical else '16x9'}{TAG}.mp4",
        "canvas": {"width": W, "height": H, "fps": FPS},
        "grade": {"lut": LUT, **BASE_G},
        "fade": {"in": 1.0, "out": 1.6, "color": "black"},
        "clips": clips, "texts": [], "overlays": ov,
        "audio": {
            "vo": {"src": VO, "start": 0.0, "gain_db": 0, **({"raw": True} if EMO else {})},
            **MUS,
            "sfx": sfx,
        },
        "loudness": {"I": -14, "TP": -1.5 if UHD else -1, "LRA": 11},
        "encode": {"crf": 17, "preset": "medium", "maxrate": "60M"} if UHD else {"crf": 16, "preset": "slow", "maxrate": "30M"},
    }
    if vertical:   # en redes se ve sin sonido: subtítulos de la locución real
        edl["subtitles"] = {"src": "locucion_a2.srt", "offset": 0.0, "style": "subtitulo", "size": 22, "y": 1620}
    return edl

if __name__ == "__main__":
    for v in (False, True):
        edl = build(v); out = AQUI / (("edl_9x16" if v else "edl_16x9") + TAG + ".json")
        out.write_text(json.dumps(edl, indent=2, ensure_ascii=False)); print(out.name, len(edl["clips"]), "planos", len(edl["audio"]["sfx"]), "sfx")
    if ERR: sys.exit("\n".join(sorted(set(ERR))))
