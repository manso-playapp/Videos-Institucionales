#!/usr/bin/env python3
"""Locución original (toma A) -> pista limpia, un poco más ágil y sin recortes.
1) Limpieza del audio completo (adeclick, NLM + FFT denoise, EQ de voz) SIN compuerta.
2) Corte por frases del guion (9 bloques) con las palabras de Whisper; dentro de cada bloque las
   pausas internas > 0.45 s se acortan a 0.32 s con crossfade (sin silencio digital).
3) Cada bloque se acelera (rubberband, formantes preservados) y se ubica con pausas fijas.
Salidas: media/audio/vo_a2.wav, vo_a2_cues.json"""
import json, subprocess, numpy as np, re
from pathlib import Path
A = Path(__file__).parent.parent
SRC = A / "media/audio/locucion_A.wav"
WORDS = [(d["start"], d["end"], d["w"]) for d in json.load(open(A / "media/WhatsApp Audio 2026-11-16 at 12.02.24 PM.json"))]
SR = 48000; TEMPO = 1.07
LEAD = 1.5
GAPS = [1.0, 1.05, 1.0, 1.15, 0.9, 1.0, 1.1, 2.6]
END = 0  # se calcula
STARTS = ["Cada", "Nosotros", "Por", "Aportamos", "Pero", "Detrás|Personas", "Y", "Porque", "Zizi|ZIZI"]
# B5 = "Pero también… clientes." / B6 = "Personas… realidades."
STARTS = ["Cada", "Nosotros", "Por", "Aportamos", "Pero", "Personas", "Y", "Porque", "Zizi"]

def run(cmd): subprocess.run(cmd, check=True)
def load(p, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").copy()
def save(x, p):
    raw = Path(str(p) + ".f32"); x.astype("<f4").tofile(raw)
    run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw), "-c:a", "pcm_f32le", str(p)]); raw.unlink()

# 1) limpieza global
clean = A / "media/audio/_a_clean.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(SRC), "-ac", "1", "-ar", str(SR), "-af",
     # clics -> retumbe/hum (pasa-altos 95 Hz + muescas 50/100) -> ruido de fondo -> EQ de voz -> de-esser
     "adeclick=w=55:o=75,highpass=f=95:p=2,bandreject=f=50:t=q:w=8,bandreject=f=100:t=q:w=10,"
     "anlmdn=s=0.002:p=0.004:r=0.006,afftdn=nr=14:nf=-48:tn=1,"
     "equalizer=f=190:t=q:w=1:g=-2,equalizer=f=330:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.1:g=2.5,"
     "equalizer=f=9500:t=h:w=1:g=1,deesser=i=0.55:m=0.5:f=0.45", "-c:a", "pcm_f32le", str(clean)])
x = load(clean)

# 2) bloques por frases
idx, k = [], 0
for i, (s, e, w) in enumerate(WORDS):
    if k < len(STARTS) and re.sub(r"[^\wáéíóúñ]", "", w, flags=re.I).lower() == STARTS[k].lower() and (not idx or i > idx[-1] + 3):
        idx.append(i); k += 1
assert len(idx) == 9, idx
blocks = []
F = int(0.04 * SR)
# v3 — bordes por energía (Whisper marca los comienzos antes de tiempo y los finales antes de que termine la cola):
#  · comienzo de bloque: si entre la marca y la voz hay un silencio, se arranca al final de ese silencio (deja afuera chasquidos y respiraciones)
#  · final de bloque: se sigue la cola real de la última palabra y se funde despacio
# Los bloques se ubican en los mismos tiempos de la versión anterior (ANCLA), así la edición hecha sobre la locución no se corre.
ANCLA = [1.5, 11.846, 22.615, 33.821, 44.934, 56.862, 63.095, 72.501, 80.689]
W20 = int(0.02 * SR)
def envdb(a, b):
    n = max(1, int((b - a) * SR) // W20); s0 = int(a * SR)
    return np.array([20 * np.log10(np.sqrt(np.mean(x[s0 + i * W20: s0 + (i + 1) * W20] ** 2)) + 1e-9) for i in range(n)])
PICO = 20 * np.log10(np.sqrt(np.mean(np.sort(x ** 2)[-len(x) // 4:])) + 1e-9)       # nivel típico de la voz
def comienzo(s):                                # s = marca de Whisper
    a = s - 0.15; e = envdb(a, a + 1.6); fuerte = np.where((e[:-2] > PICO - 8) & (e[1:-1] > PICO - 8) & (e[2:] > PICO - 8))[0]   # voz: 60 ms seguidos bien arriba
    if not len(fuerte): return a
    f, ini, run, tope = fuerte[0], None, 0, None
    for i in range(f - 1, -1, -1):              # hacia atrás desde la voz: el silencio (>= 120 ms) más cercano
        if e[i] < PICO - 24:
            if run == 0: tope = i + 1           # primer cuadro con sonido después de ese silencio
            run += 1
            if run >= 6: ini = tope; break
        else: run = 0
    return a if ini is None else max(a, a + ini * 0.02 - 0.05)
def final(t):                                   # t = fin de la última palabra según Whisper
    e = envdb(t - 0.1, t + 0.7); viva = np.where(e > PICO - 28)[0]
    return (t - 0.1 + (viva[-1] + 1) * 0.02 if len(viva) else t) + 0.16
for b in range(9):
    ws = WORDS[idx[b]: idx[b + 1] if b < 8 else len(WORDS)]
    if b == 5:   # arranque fallido de la locutora ("Personas que…" 74,0–75,4 s): la frase buena empieza en 76,2 s
        ws = [(max(s, 76.24), max(e, 76.5), w) for (s, e, w) in ws]
    ini = comienzo(ws[0][0]); corr = ini - (ws[0][0] - 0.12)
    segs, cur = [], [ini, ws[0][1]]
    for (s, e, w) in ws[1:]:
        if s - cur[1] > 0.45:
            segs.append(cur); cur = [s - 0.10, e]
        else:
            cur[1] = e
    segs.append(cur); segs[-1][1] = final(segs[-1][1])
    out = np.zeros(0, dtype=np.float32)
    for j, (s, e) in enumerate(segs):
        seg = x[int(s * SR):int(e * SR)].copy()
        if j == 0:
            seg[:F] *= np.linspace(0, 1, F)
        if j > 0:
            pause = np.zeros(int(0.32 * SR) - 2 * F, dtype=np.float32)
            out[-F:] *= np.linspace(1, 0, F); seg[:F] *= np.linspace(0, 1, F)
            out = np.concatenate([out, pause])
        out = np.concatenate([out, seg])
    out[-int(0.14 * SR):] *= np.linspace(1, 0, int(0.14 * SR)) ** 2
    p = A / f"media/audio/_b{b+1}.wav"; save(out, p)
    q = A / f"media/audio/_b{b+1}_t.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-af", f"rubberband=tempo={TEMPO}:formant=preserved:pitchq=quality:window=standard", "-c:a", "pcm_f32le", str(q)])
    blocks.append((load(q), ANCLA[b] + corr / TEMPO)); p.unlink(); q.unlink()
    print(f"  bloque {b+1}: comienzo {corr:+.2f} s respecto de antes")

cues = []
y = np.zeros(4180829, dtype=np.float32)          # misma duración que la versión anterior (87,10 s)
for i, (b, t) in enumerate(blocks):
    s = int(t * SR); y[s:s + len(b)] += b
    cues.append({"block": i + 1, "start": round(t, 3), "end": round(t + len(b) / SR, 3)})
tmp = A / "media/audio/_a_seq.wav"; save(y, tmp)
run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af",
     # nivelado suave entre frases + compresión + limitador
     "dynaudnorm=f=400:g=21:p=0.85:m=5:s=8,acompressor=threshold=0.07:ratio=3:attack=8:release=140:makeup=2,"
     "alimiter=limit=0.89,aformat=channel_layouts=stereo",
     "-ar", str(SR), "-c:a", "pcm_s24le", str(A / "media/audio/vo_a2.wav")])
tmp.unlink(); clean.unlink()
v0 = load(A / "media/audio/vo_a2.wav"); rng = np.random.default_rng(7)
sala = np.cumsum(rng.standard_normal(len(v0)).astype(np.float32)); sala -= np.convolve(sala, np.ones(2400) / 2400, "same")   # ruido grave y parejo
sala *= 10 ** (-66 / 20) / (np.sqrt(np.mean(sala ** 2)) + 1e-9)
r = int(0.4 * SR); sala[:r] *= np.linspace(0, 1, r); sala[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
save(v0 + sala, A / "media/audio/_sala.wav")
run(["ffmpeg", "-v", "error", "-y", "-i", str(A / "media/audio/_sala.wav"), "-af", "aformat=channel_layouts=stereo", "-ar", str(SR), "-c:a", "pcm_s24le", str(A / "media/audio/vo_a2.wav")])
(A / "media/audio/_sala.wav").unlink()
json.dump(cues, open(A / "vo_a2_cues.json", "w"), indent=1)
print("dur", round(len(y) / SR, 2), [(c["block"], c["start"], c["end"]) for c in cues])

# 4) atenuar respiraciones/ruidos en las pausas (-15 dB con rampas de 50 ms), sin silencio digital
subprocess.run(["python3", str(A.parent.parent / "tools/transcribir.py"), str(A / "media/audio/vo_a2.wav"), "--prompt", "ZIZI, 46 años, obra"],
               capture_output=True, check=True)
w = json.load(open(A / "media/audio/vo_a2.json"))
v = load(A / "media/audio/vo_a2.wav")
g = np.ones_like(v); R = int(0.09 * SR); floor = 10 ** (-12 / 20)
for i in range(len(w) - 1):
    a, b = w[i]["end"] + 0.26, w[i + 1]["start"] - 0.14
    if b - a > 0.2:
        s, e = int(a * SR), int(b * SR)
        env = np.full(e - s, floor, dtype=np.float32)
        r = min(R, (e - s) // 2); env[:r] = np.linspace(1, floor, r); env[-r:] = np.linspace(floor, 1, r)
        g[s:e] = np.minimum(g[s:e], env)
pass
save(v * g, A / "media/audio/_vo_g.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(A / "media/audio/_vo_g.wav"), "-af", "aformat=channel_layouts=stereo",
                "-ar", str(SR), "-c:a", "pcm_s24le", str(A / "media/audio/vo_a2.wav")], check=True)
(A / "media/audio/_vo_g.wav").unlink()
print("pausas atenuadas")
