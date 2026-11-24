#!/usr/bin/env python3
"""Exporta el corte actual (build_edl.S) a artefacto/corte.json para el artefacto de selección."""
import json, sys, re
from pathlib import Path
A = Path(__file__).parent.parent; sys.path.insert(0, str(A))
import build_edl as B
inv = {c["n"]: c for c in json.load(open(A / "inventario/inventario.json"))}
words = json.load(open(A / ("media/audio/vo_carlos_c.json" if B.DIN else "media/audio/mezcla_javier.json" if B.VER == "emocional" else "media/audio/vo_a2.json")))
GR = {"14-11": "14-11 · Galpón terminado", "27-10": "27-10 · Montaje", "30-10": "30-10 · Primeros techos", "6-11": "6-11 · Techo completo"}
def grupo(c):
    p = c["file"].split("/tomas/")[1]
    if "/" in p:
        g = GR[p.split("/")[0]]; return g + (" (celular)" if "IMG_" in p else "")
    return "19-10 · Dueños y planos (celular)" if "IMG_" in p else "19-10 · Terreno y columnas"
lib = {str(n): {"archivo": c["file"].split("/")[-1], "dur": round(c["duracion"], 2), "grupo": grupo(c),
                "res": c["video"]["res"]} for n, c in inv.items() if n < 150}
for n in (80, 81, 82, 83, 84, 86, 87): lib[str(n)]["veto"] = "sin protección"      # operarios sobre el techo sin elementos de protección: no se usan (pedido del estudio, 24-11)
slots = []
for k, s in enumerate(B.S):
    t0 = s["t"]; t1 = B.S[k + 1]["t"] if k + 1 < len(B.S) else B.END
    frase = " ".join(w["w"] for w in words if t0 - 0.15 <= w["start"] < t1 - 0.15)
    frase = re.sub(r"\bZizi\b", "ZIZI", frase).replace("ninguna hora", "ninguna obra")
    d = {"k": k, "t": t0, "dur": round(t1 - t0, 2), "frase": frase,
         "tr": s["tr"]["type"].replace("gl:", "") if s.get("tr") else "Corte"}
    if s.get("plate"): d["tipo"] = "placa"
    elif s.get("negro"): d["tipo"] = "negro"
    elif "split" in s: d["tipo"] = "split"; d["tomas"] = s["split"]; d["ins"] = s["si"]
    else:
        d["tipo"] = "toma"; d["n"] = s["n"]; d["in"] = s["i"]
        if s.get("v", 1) != 1: d["v"] = s["v"]
        if s.get("luz"): d["luz"] = True
    slots.append(d)
pal = [{"w": re.sub(r"\bZizi\b", "ZIZI", w["w"]).replace("hora", "obra") if w["w"] in ("hora",) else re.sub(r"\bZizi\b", "ZIZI", w["w"]),
        "t": round(w["start"], 2), "e": round(w["end"], 2)} for w in words]
# textos animados: los .webm con transparencia de artefacto/ov/ (uno por overlay de la EDL, en orden) para la vista rápida
textos = [{"t": o["start"], "dur": o["dur"], "src": ("ov" if B.DIN else "ove") + "/o%02d.webm" % i} for i, o in enumerate(x for x in B.build(False)["overlays"] if x["template"] != "luz")]
json.dump({"pieza": "Horizontal 16:9", "version": "Dinámica 2" if B.DIN else "Emocional 3" if B.VER == "emocional" else "Borrador 6", "dur": B.END, "fx": B.FX, "render": "corte_%s.mp4" % B.VER,
           "voces": [["carlos", "Carlos (argentina) · ritmo natural", "vo_cc.mp3"]] if B.DIN else [["javier", "Mezcla final (Lara + música)", "vo_j.mp3"]], "sinMusica": B.VER == "emocional", "slots": slots, "lib": lib, "palabras": pal, "textos": textos},
          open(A / ("artefacto/corte_%s.json" % (B.VER or "larga")), "w"), ensure_ascii=False, indent=1)
print(len(slots), "slots", len(lib), "tomas")
