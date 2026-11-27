#!/usr/bin/env python3
"""
editor.py — Editor de corte en artefacto: el estudio edita la línea de tiempo en el navegador y la edición vuelve al render.

Nació en el proyecto ZIZI (nov-2026). Flujo completo y contrato de datos: docs/editor.md

  python3 tools/editor/editor.py preparar proyectos/<cliente> --nombre "ACME" [--versiones larga:Larga,corta:Corta] [--placa ACME]
      Crea proyectos/<cliente>/artefacto/ con el editor (index.html), proyecto.json, y por cada toma del inventario
      un proxy liviano (media/tNNN.mp4, 426x240 sin audio) y un poster (posters/tNNN.jpg).
      Necesita proyectos/<cliente>/inventario/inventario.json (tools/analizar.py inventario).

  python3 tools/editor/editor.py niveles proyectos/<cliente> [--proxies]
      Mide cada toma y calcula la nivelación de color que la lleva a una base común -> niveles.json
      ({n: {grade: {levels, gamma}}}, se usa como "grade" del clip en la EDL). --proxies regenera los proxies ya nivelados.

  python3 tools/editor/editor.py overlays proyectos/<cliente> edl.json [--carpeta ov]
      Renderiza los textos animados de la EDL (overlays) a .webm con transparencia para la vista rápida del editor.

  python3 tools/editor/editor.py transiciones proyectos/<cliente> A.mp4 B.mp4
      Genera las muestras de transición (trans/<Shader>.mp4|jpg) que el editor muestra al elegir una.

Como módulo (desde el build_edl.py del proyecto):
  exportar_corte(...)   corte actual -> artefacto/corte_<ver>.json (lo que el editor carga)
  cargar_edicion(...)   edición guardada por el estudio -> lista S de planos, con transiciones ajustadas al material
  clips(...)            lista S -> clips de la EDL (in exacto en el corte, velocidad, recorte vertical)
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent.parent
# Transiciones que ofrece el editor (clave = shader GL de assets/transitions/gl; "Fade" = disolvencia) y su duración por defecto
TR_DUR = {"Fade": 0.5, "DefocusBlur": 0.5, "BloomDissolve": 0.5, "Overexposure": 0.42, "LightWipe": 0.5, "LensFlare": 0.5, "WhipPan": 0.38,
          "WhipTilt": 0.45, "CrossZoom": 0.7, "Directional": 0.5, "DirectionalWarp": 0.5, "FilmBurn": 0.6, "Comb": 0.5}


def _inv(proy: Path) -> dict:
    f = proy / "inventario/inventario.json"
    if not f.exists(): sys.exit(f"Falta {f}: corré primero tools/analizar.py inventario {proy}/media -o {proy}/inventario")
    return {c["n"]: c for c in json.load(open(f))}

def _ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)


# ---------------------------------------------------------------------------------------------------------- preparar
def preparar(proy: Path, nombre: str | None, versiones: str, placa: str | None, forzar=False):
    art = proy / "artefacto"; (art / "media").mkdir(parents=True, exist_ok=True); (art / "posters").mkdir(exist_ok=True)
    shutil.copy(AQUI / "index.html", art / "index.html")
    cfg = art / "proyecto.json"
    if not cfg.exists() or forzar:
        nombre = nombre or proy.name.upper()
        json.dump({"id": proy.name, "nombre": nombre, "placa": placa or nombre,
                   "versiones": [v.split(":", 1) if ":" in v else [v, v.capitalize()] for v in versiones.split(",")], "musicas": []},
                  open(cfg, "w"), ensure_ascii=False, indent=1)
    def uno(c):
        src = REPO / c["file"]; out = art / f"media/t{c['n']:03d}.mp4"; pos = art / f"posters/t{c['n']:03d}.jpg"
        if not out.exists():
            _ff("-skip_loop_filter", "all", "-skip_frame", "noref", "-i", src, "-an", "-vf", "scale=426:240:force_original_aspect_ratio=increase,crop=426:240",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "31", "-g", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out)
        if not pos.exists(): _ff("-ss", f"{c['duracion'] * 0.35:.2f}", "-i", out, "-frames:v", "1", "-q:v", "6", pos)
    with ThreadPoolExecutor(4) as ex: list(ex.map(uno, _inv(proy).values()))
    print(f"Editor listo en {art} · {len(list((art / 'media').glob('*.mp4')))} proxies. Falta corte_<versión>.json (exportar_corte) y publicar: ver docs/editor.md")


# ----------------------------------------------------------------------------------------------------------- niveles
def niveles(proy: Path, proxies=False):
    """Punto negro/blanco (percentiles 1 y 99), gamma (mediana ~0,44) y balance de blancos sobre lo claro y neutro.
    Con topes y a intensidad parcial: empareja sin aplanar ni inventar luz. Mide sobre los proxies."""
    import numpy as np
    W, H, N, OBJ, OMIN, OMAX = 160, 90, 7, 0.44, 0.035, 0.955
    res = {}
    for n, c in sorted(_inv(proy).items()):
        p = proy / f"artefacto/media/t{n:03d}.mp4"
        if not p.exists(): continue
        fr = []
        for i in range(N):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c['duracion'] * (i + 0.5) / N:.2f}", "-i", str(p), "-frames:v", "1", "-vf", f"scale={W}:{H}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            if len(raw) == W * H * 3: fr.append(np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.float32) / 255)
        if not fr: continue
        px = np.concatenate(fr); Y = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        p1, med, p99 = [float(np.percentile(Y, q)) for q in (1, 50, 99)]
        black = max(0.0, float(np.clip(0.75 * (p1 - OMIN), 0.0, 0.10)))
        white = float(np.clip(1.0 - 0.5 * (OMAX - p99) if p99 < OMAX else 1.0, 0.80, 1.0))
        sat = px.max(1) - px.min(1); m = (Y > np.percentile(Y, 90)) & (Y < 0.97) & (sat < 0.12); wb = [1.0, 1.0, 1.0]
        if m.sum() > 0.01 * len(Y):
            g = px[m].mean(0); g = g.mean() / g; g = 1 + 0.6 * (g - 1); g = np.clip(g / g[1], 0.93, 1.07); wb = [round(float(v), 4) for v in g]
        m2 = np.clip((med - black) / max(white - black, 1e-3), 0.02, 0.98) * (OMAX - OMIN) + OMIN
        gamma = float(np.clip(np.log(m2) / np.log(OBJ), 0.80, 1.30)) if abs(m2 - OBJ) > 0.03 else 1.0
        gamma = round(1 + 0.8 * (gamma - 1), 2)
        gr = {"levels": {"black": round(black, 4), "white": round(white, 4), "wb": wb, "omin": 0.0, "omax": 1.0}}
        if abs(gamma - 1) >= 0.03: gr["gamma"] = gamma
        res[str(n)] = {"med": round(med, 3), "p1": round(p1, 3), "p99": round(p99, 3), "grade": gr}
    json.dump(res, open(proy / "niveles.json", "w"), indent=0); print(len(res), "tomas niveladas ->", proy / "niveles.json")
    if proxies:      # proxies con el color ya nivelado (media_g/): se publican en el lugar de media/ para que el editor muestre el color real
        out = proy / "artefacto/media_g"; out.mkdir(exist_ok=True)
        for n, v in res.items():
            lv = v["grade"]["levels"]; b, w = lv["black"], lv["white"]
            f = "colorlevels=" + ":".join(f"{c}imin={b:.4f}:{c}imax={min(1.0, w / k):.4f}" for c, k in zip("rgb", lv["wb"]))
            if "gamma" in v["grade"]: f += f",eq=gamma={v['grade']['gamma']}"
            _ff("-i", proy / f"artefacto/media/t{int(n):03d}.mp4", "-an", "-vf", f, "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-g", "15",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", out / f"t{int(n):03d}.mp4")
        print("proxies nivelados ->", out)


# ---------------------------------------------------------------------------------------------------------- overlays
def overlays(proy: Path, edl: Path, carpeta="ov"):
    """Un .webm con transparencia por overlay de la EDL (en orden, sin los de 'luz'), para que la vista rápida muestre los textos."""
    e = json.load(open(edl)); out = proy / "artefacto" / carpeta; out.mkdir(parents=True, exist_ok=True)
    size = "%dx%d" % (e["canvas"]["width"] // 2, e["canvas"]["height"] // 2); lista = []
    for i, o in enumerate(x for x in e["overlays"] if x["template"] != "luz"):
        mov = out / f"o{i:02d}.mov"; webm = out / f"o{i:02d}.webm"
        subprocess.run([sys.executable, str(REPO / "tools/motion.py"), "plantilla", o["template"], "-p", json.dumps(o["params"]), "-o", str(mov), "--alpha",
                        "--size", size, "--fps", str(e["canvas"]["fps"])], check=True, capture_output=True)
        _ff("-i", mov, "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "34", "-auto-alt-ref", "0", "-an", webm); mov.unlink()
        lista.append({"t": o["start"], "dur": o["dur"], "src": f"{carpeta}/o{i:02d}.webm"})
    print(len(lista), "textos ->", out); return lista


# ------------------------------------------------------------------------------------------------------ transiciones
def transiciones(proy: Path, a: Path, b: Path):
    out = proy / "artefacto/trans"; out.mkdir(parents=True, exist_ok=True)
    A, B = out / "_a.mov", out / "_b.mov"
    for src, dst in ((a, A), (b, B)): _ff("-i", src, "-t", "2", "-an", "-vf", "scale=426:240:force_original_aspect_ratio=increase,crop=426:240", "-c:v", "prores_ks", dst)
    for sh in TR_DUR:
        if sh == "Fade": continue
        mov = out / f"{sh}.mov"
        subprocess.run([sys.executable, str(REPO / "tools/motion.py"), "transicion", str(A), str(B), "--shader", sh, "--dur", "1.0", "-o", str(mov),
                        "--size", "426x240", "--fps", "25"], check=True, capture_output=True)
        _ff("-i", mov, "-an", "-c:v", "libx264", "-crf", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out / f"{sh}.mp4")
        _ff("-ss", "0.5", "-i", mov, "-frames:v", "1", "-q:v", "6", out / f"{sh}.jpg"); mov.unlink()
    A.unlink(); B.unlink(); print("muestras ->", out)


# ------------------------------------------------------------------------------------------- corte (editor <-> EDL)
def exportar_corte(proy: Path, ver: str, etiqueta: str, S: list, end: float, palabras: list, *, voces: list, grupo=None, vetos: dict | None = None,
                   persona=None, textos: list | None = None, fx: dict | None = None, render: str | None = None, sin_musica=False):
    """Escribe artefacto/corte_<ver>.json.
    S: planos [{t, n, i, v?, luz?, tr?} | {t, split:[n..], si:[in..]} | {t, plate:True} | {t, negro:True}] (t = cuándo entra; i = in en la fuente).
    palabras: [{w, start, end}] de la locución (tools/transcribir.py). voces: [[id, etiqueta, archivo.mp3]] publicados junto al editor.
    grupo(c) -> nombre del grupo de la toma en la biblioteca; persona(c) -> True si es plano de personas (look cálido); vetos {n: motivo}: no se ofrecen.
    etiqueta: nombre visible de la versión ("Borrador 3"); si cambia, el editor descarta la edición guardada y arranca de este corte."""
    inv = _inv(proy)
    lib = {str(n): {"archivo": c["file"].split("/")[-1], "dur": round(c["duracion"], 2), "grupo": grupo(c) if grupo else "Tomas", "res": c["video"]["res"],
                    **({"persona": True} if persona and persona(c) else {}), **({"veto": vetos[n]} if vetos and n in vetos else {})} for n, c in inv.items()}
    slots = []
    for k, s in enumerate(S):
        t0 = s["t"]; t1 = S[k + 1]["t"] if k + 1 < len(S) else end
        d = {"k": k, "t": t0, "dur": round(t1 - t0, 2), "frase": " ".join(w["w"] for w in palabras if t0 - 0.15 <= w["start"] < t1 - 0.15),
             "tr": s["tr"]["type"].replace("gl:", "") if s.get("tr") else "Corte"}
        if s.get("plate"): d["tipo"] = "placa"
        elif s.get("negro"): d["tipo"] = "negro"
        elif "split" in s: d.update(tipo="split", tomas=s["split"], ins=s["si"])
        else:
            d.update(tipo="toma", n=s["n"], **{"in": s["i"]})
            if s.get("v", 1) != 1: d["v"] = s["v"]
            if s.get("luz"): d["luz"] = True
        slots.append(d)
    out = proy / f"artefacto/corte_{ver}.json"
    json.dump({"pieza": ver, "version": etiqueta, "dur": end, "fx": fx or {}, "render": render, "voces": voces, "sinMusica": sin_musica, "slots": slots, "lib": lib,
               "palabras": [{"w": w["w"], "t": round(w["start"], 2), "e": round(w["end"], 2)} for w in palabras], "textos": textos or []},
              open(out, "w"), ensure_ascii=False, indent=1)
    print(out.name, len(slots), "planos", len(lib), "tomas"); return out


def T(tipo: str, dur: float | None = None, **uniforms):
    t = {"type": "gl:" + tipo, "dur": dur if dur is not None else TR_DUR.get(tipo, 0.5), "ease": "cubic-in-out"}
    if uniforms: t["uniforms"] = uniforms
    return t


def cargar_edicion(archivo: Path, inv: dict, end: float, *, tr_dur: dict | None = None, max_plano: float | None = None):
    """Edición guardada por el editor ({slots, fx, notas}) -> (S, fx). En la edición, "in" es el punto de la fuente que se ve EN el corte t.
    Una transición solapa las dos tomas: si a una no le sobra material, la transición se acorta (o se quita si queda < 0,12 s).
    max_plano: tope de segundos en pantalla por toma contando las disolvencias (regla ZIZI: 3,0); acorta transiciones, no mueve cortes."""
    e = json.load(open(archivo)); dur = {**TR_DUR, **(tr_dur or {})}; S = []
    for x in e["slots"]:
        s = {"t": x["t"], "exacto": True}
        if x["tipo"] == "placa": s["plate"] = True
        elif x["tipo"] == "negro": s["negro"] = True
        elif x["tipo"] == "split": s["split"], s["si"] = x["tomas"], x["ins"]
        else: s.update(n=x["n"], i=x["in"], v=float(x.get("v", 1)), luz=bool(x.get("luz")))
        if x.get("tr") and x["tr"] != "Corte": s["tr"] = T(x["tr"], dur.get(x["tr"], 0.5))
        S.append(s)
    fin = lambda k: S[k + 1]["t"] if k + 1 < len(S) else end
    for k, s in enumerate(S):
        if "n" not in s: continue
        libre = inv[s["n"]]["duracion"] / float(s.get("v", 1)) - (fin(k) - s["t"]) - 0.04
        for j in (k, k + 1):
            if 0 < j < len(S) and S[j].get("tr"): S[j]["tr"] = dict(S[j]["tr"], dur=round(max(0.0, min(S[j]["tr"]["dur"], libre)), 2))
    if max_plano:
        for _ in range(3):
            for k, s in enumerate(S):
                if s.get("plate"): continue
                hd = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
                tl = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
                sobra = fin(k) - s["t"] + hd + tl - max_plano
                if sobra > 0.005 and hd + tl > 0:
                    f = max(0.0, 1 - sobra / (hd + tl))
                    for j in (k, k + 1):
                        if 0 < j < len(S) and S[j].get("tr"): S[j]["tr"] = dict(S[j]["tr"], dur=round(S[j]["tr"]["dur"] * f, 2))
    for s in S:
        if s.get("tr") and s["tr"]["dur"] < 0.12: s.pop("tr")
    return S, (e.get("fx") or {})


def clips(S: list, inv: dict, end: float, *, raiz: str = "", vertical=False, foco: dict | None = None, blur: set | None = None, grade=None, placa=None,
          negro: str = "media/negro.png", errores: list | None = None):
    """Lista S -> clips de la EDL. raiz: prefijo a quitar de inv[n]["file"] para dejar la ruta relativa al proyecto ("proyectos/acme/").
    grade(n) -> dict de grade del clip (p. ej. niveles.json[n]["grade"]). placa(dur, vertical) -> clip de la placa de cierre.
    vertical: recorte 9:16 con foco[n] = x (0..1) o, para n en blur, plano entero sobre fondo desenfocado."""
    out = []
    for k, s in enumerate(S):
        t1 = S[k + 1]["t"] if k + 1 < len(S) else end
        head = s["tr"]["dur"] / 2 if k and s.get("tr") else 0.0
        tail = S[k + 1]["tr"]["dur"] / 2 if k + 1 < len(S) and S[k + 1].get("tr") else 0.0
        d = (t1 - s["t"]) + head + tail
        if s.get("plate"): c = placa(d, vertical) if placa else {"src": negro, "dur": round(d, 3), "fit": "contain", "bg": "black"}
        elif s.get("negro"): c = {"src": negro, "dur": round(d, 3), "fit": "contain", "bg": "black"}
        elif "split" in s:
            c = {"split": [{"src": inv[n]["file"].replace(raiz, ""), "in": round(max(0.0, i - head), 3) if s.get("exacto") else i, **({"grade": grade(n)} if grade and grade(n) else {})}
                           for n, i in zip(s["split"], s["si"])], "dur": round(d, 3), "gap": 10, "layout": "v" if vertical else "h", "stagger": 0.12}
        else:
            c0 = inv[s["n"]]; v = float(s.get("v", 1)); i = s["i"]
            if s.get("exacto"):                                   # el cuadro elegido cae justo en el corte; si no alcanza la cola, arranca un poco antes
                i = round(max(0.0, i - head * v), 3); i = round(max(0.0, min(i, c0["duracion"] - d * v - 0.02)), 3)
            if i + d * v > c0["duracion"] + 0.02 and errores is not None:
                errores.append(f"n{s['n']}: pide {i + d * v:.2f}s (in {i} + {d:.2f}) y el clip dura {c0['duracion']:.2f}s")
            c = {"src": c0["file"].replace(raiz, ""), "in": i, "dur": round(d, 3)}
            if v != 1: c["speed"] = v
            if grade and grade(s["n"]): c["grade"] = grade(s["n"])
            if vertical:
                if s["n"] in (blur or ()): c["fit"], c["bg"] = "contain", "blur"
                else: c["focus"] = {"x": (foco or {}).get(s["n"], 0.5), "y": 0.5}
        if s.get("tr"): c["transition_in"] = s["tr"]
        out.append(c)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar"); p.add_argument("proyecto", type=Path); p.add_argument("--nombre"); p.add_argument("--versiones", default="corte:Corte")
    p.add_argument("--placa"); p.add_argument("--forzar", action="store_true")
    p = sub.add_parser("niveles"); p.add_argument("proyecto", type=Path); p.add_argument("--proxies", action="store_true")
    p = sub.add_parser("overlays"); p.add_argument("proyecto", type=Path); p.add_argument("edl", type=Path); p.add_argument("--carpeta", default="ov")
    p = sub.add_parser("transiciones"); p.add_argument("proyecto", type=Path); p.add_argument("a", type=Path); p.add_argument("b", type=Path)
    a = ap.parse_args(); proy = a.proyecto.resolve()
    if a.cmd == "preparar": preparar(proy, a.nombre, a.versiones, a.placa, a.forzar)
    elif a.cmd == "niveles": niveles(proy, a.proxies)
    elif a.cmd == "overlays": print(json.dumps(overlays(proy, a.edl.resolve(), a.carpeta), ensure_ascii=False))
    elif a.cmd == "transiciones": transiciones(proy, a.a.resolve(), a.b.resolve())
