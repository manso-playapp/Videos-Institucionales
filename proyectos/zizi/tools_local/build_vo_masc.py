#!/usr/bin/env python3
"""Versión alternativa de la locución con voz masculina (ElevenLabs vía Artlist, voz argentina «Mauricio»).
Parte de una sola generación (media/audio/masc/alberto_raw.mp3), la corta en los mismos 9 bloques del guion y ubica cada
bloque donde empieza el de la locución original (vo_a2_cues.json), para que la edición hecha sobre la voz femenina siga calzando.
Cada bloque se estira hasta un 10 % si es más corto que el original. Salida: media/audio/vo_masc.wav (+ .json/.srt de palabras)."""
import json, subprocess, re, numpy as np
from pathlib import Path
A = Path(__file__).parent.parent; SR = 48000
import sys
# uso: build_vo_masc.py [toma.mp3] [salida]   (por defecto: Mauricio, toma 2 -> vo_masc)
RAW = A / (sys.argv[1] if len(sys.argv) > 1 else "media/audio/masc/mauricio_t2.mp3"); OUT = sys.argv[2] if len(sys.argv) > 2 else "vo_masc"      # ElevenLabs · «Mauricio - Publicidad cálida | Argentina» (rioplatense), toma 2
W = json.load(open(RAW.with_suffix(".json"))); CUES = json.load(open(A / "vo_a2_cues.json"))
STARTS = ["cada", "nosotros", "por", "aportamos", "pero", "personas", "y", "porque", "zizi"]
def load(p, af=None):
    c = ["ffmpeg", "-v", "error", "-i", str(p)] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True, check=True).stdout, dtype="<f4").copy()
def save(x, p, af="anull"):
    raw = Path(str(p) + ".f32"); x.astype("<f4").tofile(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw), "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", str(p)], check=True); raw.unlink()
x = load(RAW, "highpass=f=70")
norm = lambda w: re.sub(r"[^\wáéíóúñ]", "", w, flags=re.I).lower()
idx, k = [], 0
for i, d in enumerate(W):
    if k < 9 and norm(d["w"]) == STARTS[k] and (not idx or i > idx[-1] + 3): idx.append(i); k += 1
assert len(idx) == 9, idx
def borde(t, lado):                              # afina el borde con la energía (silencio más cercano)
    w = int(0.02 * SR); a = t - 0.25 if lado < 0 else t; n = 25
    e = np.array([np.sqrt(np.mean(x[int(a * SR) + i * w: int(a * SR) + (i + 1) * w] ** 2) + 1e-12) for i in range(n)]); viva = np.where(e > 0.004)[0]
    if lado < 0: return max(0, a + (viva[viva > 0][0] if len(viva[viva > 0]) and e[0] < 0.004 else 10) * 0.02 - 0.05)
    return a + ((viva[-1] + 1) if len(viva) else 5) * 0.02 + 0.12
y = np.zeros(4180829, dtype=np.float32); cues = []
for b in range(9):
    ws = W[idx[b]: idx[b + 1] if b < 8 else len(W)]
    s, e = borde(ws[0]["start"], -1), min(len(x) / SR, borde(ws[-1]["end"], +1))
    if b < 8: e = min(e, W[idx[b + 1]]["start"] - 0.06)
    seg = x[int(s * SR):int(e * SR)].copy(); f = int(0.03 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-3 * f:] *= np.linspace(1, 0, 3 * f) ** 2
    orig = CUES[b]["end"] - CUES[b]["start"]; tempo = float(np.clip(len(seg) / SR / (orig - 0.25), 0.90, 1.10))
    p = A / f"media/audio/masc/_b{b}.wav"; save(seg, p, f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality"); seg = load(p); p.unlink()
    t0 = CUES[b]["start"]; i0 = int(t0 * SR); y[i0:i0 + len(seg)] += seg[:len(y) - i0]
    cues.append({"block": b + 1, "start": round(t0, 3), "end": round(t0 + len(seg) / SR, 3), "tempo": round(tempo, 3), "orig_end": CUES[b]["end"]})
    print(f"  bloque {b+1}: {len(seg)/SR:.2f} s (original {orig:.2f}) tempo {tempo:.2f}")
rng = np.random.default_rng(7); sala = np.cumsum(rng.standard_normal(len(y)).astype(np.float32)); sala -= np.convolve(sala, np.ones(2400) / 2400, "same")
sala *= 10 ** (-68 / 20) / (np.sqrt(np.mean(sala ** 2)) + 1e-9); r = int(0.4 * SR); sala[:r] *= np.linspace(0, 1, r); sala[-SR:] *= np.linspace(1, 0, SR)
save(y, A / "media/audio/_m.wav", "equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3500:t=q:w=1.2:g=1.5,deesser=i=0.3:f=0.5,acompressor=threshold=0.09:ratio=2.5:attack=10:release=160:makeup=2,alimiter=limit=0.89")
v = load(A / "media/audio/_m.wav") + sala; (A / "media/audio/_m.wav").unlink()
save(v, A / f"media/audio/{OUT}.wav", "aformat=channel_layouts=stereo")
json.dump(cues, open(A / f"{OUT}_cues.json", "w"), indent=1)
subprocess.run(["python3", str(A.parent.parent / "tools/transcribir.py"), str(A / f"media/audio/{OUT}.wav"), "--prompt", "ZIZI, 46 años, obra"], capture_output=True, check=True)
print("ok", round(len(v) / SR, 2))
