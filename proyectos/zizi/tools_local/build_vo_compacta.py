#!/usr/bin/env python3
"""Locución COMPACTA para la versión dinámica: la voz de Carlos (ElevenLabs, argentina) a su ritmo natural, sin estirarla
para calzar con la locutora, y con pausas cortas entre frases. Define una duración nueva y más corta del video.
Salidas: media/audio/vo_carlos_c.wav (+ .json/.srt de palabras) · vo_carlos_c_cues.json (bloques nuevos y de la versión larga, para reubicar la edición)."""
import json, subprocess, re, numpy as np
from pathlib import Path
A = Path(__file__).parent.parent; SR = 48000
RAW = A / "media/audio/masc/carlos_t1.mp3"; W = json.load(open(RAW.with_suffix(".json"))); VIEJO = json.load(open(A / "vo_a2_cues.json"))
STARTS = ["cada", "nosotros", "por", "aportamos", "pero", "personas", "y", "porque", "zizi"]
LEAD = 0.9; GAPS = [0.55, 0.55, 0.5, 0.55, 0.45, 0.6, 0.55, 1.1]; COLA = 0.7
def load(p, af=None):
    c = ["ffmpeg", "-v", "error", "-i", str(p)] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True, check=True).stdout, dtype="<f4").copy()
def save(x, p, af="anull"):
    raw = Path(str(p) + ".f32"); x.astype("<f4").tofile(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw), "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", str(p)], check=True); raw.unlink()
x = load(RAW, "highpass=f=70"); norm = lambda w: re.sub(r"[^\wáéíóúñ]", "", w, flags=re.I).lower()
idx, k = [], 0
for i, d in enumerate(W):
    if k < 9 and norm(d["w"]) == STARTS[k] and (not idx or i > idx[-1] + 3): idx.append(i); k += 1
assert len(idx) == 9, idx
def env(a, n):
    w = int(0.02 * SR); return np.array([np.sqrt(np.mean(x[int(a * SR) + i * w: int(a * SR) + (i + 1) * w] ** 2) + 1e-12) if int(a * SR) + (i + 1) * w <= len(x) else 0 for i in range(n)])
segs = []
for b in range(9):
    ws = W[idx[b]: idx[b + 1] if b < 8 else len(W)]
    a = max(0, ws[0]["start"] - 0.25); e = env(a, 25); viva = np.where(e > 0.004)[0]; s = a + (viva[0] * 0.02 if len(viva) else 0.2) - 0.05
    e2 = env(ws[-1]["end"], 30); v2 = np.where(e2 > 0.004)[0]; f = ws[-1]["end"] + ((v2[-1] + 1) * 0.02 if len(v2) else 0.1) + 0.12
    if b < 8: f = min(f, W[idx[b + 1]]["start"] - 0.06)
    seg = x[int(max(0, s) * SR):int(min(len(x) / SR, f) * SR)].copy(); r = int(0.03 * SR); seg[:r] *= np.linspace(0, 1, r); seg[-3 * r:] *= np.linspace(1, 0, 3 * r) ** 2
    segs.append(seg)
t = LEAD; cues = []
for b, seg in enumerate(segs):
    cues.append({"block": b + 1, "start": round(t, 3), "end": round(t + len(seg) / SR, 3), "viejo": [VIEJO[b]["start"], VIEJO[b]["end"]]}); t += len(seg) / SR + (GAPS[b] if b < 8 else 0)
total = t + COLA; y = np.zeros(int(total * SR), dtype=np.float32)
for c, seg in zip(cues, segs): i0 = int(c["start"] * SR); y[i0:i0 + len(seg)] += seg
rng = np.random.default_rng(7); sala = np.cumsum(rng.standard_normal(len(y)).astype(np.float32)); sala -= np.convolve(sala, np.ones(2400) / 2400, "same")
sala *= 10 ** (-68 / 20) / (np.sqrt(np.mean(sala ** 2)) + 1e-9); r = int(0.4 * SR); sala[:r] *= np.linspace(0, 1, r); sala[-r:] *= np.linspace(1, 0, r)
save(y, A / "media/audio/_c.wav", "equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3500:t=q:w=1.2:g=1.5,deesser=i=0.3:f=0.5,acompressor=threshold=0.09:ratio=2.5:attack=10:release=160:makeup=2,alimiter=limit=0.89")
v = load(A / "media/audio/_c.wav") + sala; (A / "media/audio/_c.wav").unlink(); save(v, A / "media/audio/vo_carlos_c.wav", "aformat=channel_layouts=stereo")
json.dump(cues, open(A / "vo_carlos_c_cues.json", "w"), indent=1)
subprocess.run(["python3", str(A.parent.parent / "tools/transcribir.py"), str(A / "media/audio/vo_carlos_c.wav"), "--prompt", "ZIZI, 46 años, obra"], capture_output=True, check=True)
print("locución compacta:", round(total, 2), "s ·", [(c["block"], c["start"], c["end"]) for c in cues])
