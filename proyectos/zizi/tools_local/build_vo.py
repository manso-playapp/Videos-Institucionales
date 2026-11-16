#!/usr/bin/env python3
"""Limpia la locución: acorta pausas muertas, saca ruido y deja la voz lista para mezclar.
Genera media/audio/locucion_limpia.wav, vo_map.json (tiempo viejo -> nuevo) y locucion_limpia.srt."""
import json, re, subprocess, wave, numpy as np
from pathlib import Path
AQUI = Path(__file__).parent.parent
SRC = AQUI / "media/audio/locucion_A.wav"
WORDS = AQUI / "media/WhatsApp Audio 2026-11-16 at 12.02.24 PM.json"
SRT = AQUI / "locucion_A.srt"
OUT = AQUI / "media/audio/locucion_limpia.wav"
LEAD, TAIL = 0.9, 1.2                  # aire antes de la primera palabra / después de la última
HEAD, TAILK = 0.32, 0.28               # cola de respiración que se conserva a cada lado de una pausa
# duración objetivo de cada pausa larga (s), en orden. Las cortas (<0.9 s) no se tocan.
OBJ = [1.3, 1.4, 1.0, 1.4, 1.2, 1.4, 1.1, 2.4]

w = wave.open(str(SRC)); sr, ch = w.getframerate(), w.getnchannels()
b = np.frombuffer(w.readframes(w.getnframes()), dtype=np.uint8).reshape(-1, 3)
x = ((b[:, 2].astype(np.int32) << 24) | (b[:, 1].astype(np.int32) << 16) | (b[:, 0].astype(np.int32) << 8)) >> 8
x = (x.astype(np.float64) / 2**23).reshape(-1, ch).mean(axis=1)
words = [(d["start"], d["end"]) for d in json.load(open(WORDS))]
first, last = words[0][0], words[-1][1]

# trozos [old_a, old_b] que se conservan; entre ellos va silencio de largo fijo
pieces, silences, k = [], [], 0
cur = first - 0.25
gaps = [(words[i][1], words[i + 1][0]) for i in range(len(words) - 1) if words[i + 1][0] - words[i][1] >= 0.9]
for a, bb in gaps:
    pieces.append((cur, a + HEAD)); silences.append(max(OBJ[k] - HEAD - TAILK, 0.0)); cur = bb - TAILK; k += 1
pieces.append((cur, last + 0.35))
assert k == len(OBJ), (k, len(OBJ))

fade = int(0.015 * sr)
chunks, mapping, t_new = [np.zeros(int(LEAD * sr) - int(0.25 * sr))], [], LEAD - 0.25
for i, (pa, pb) in enumerate(pieces):
    seg = x[int(pa * sr):int(pb * sr)].copy()
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    mapping.append((pa, pb, t_new)); chunks.append(seg); t_new += len(seg) / sr
    if i < len(silences):
        chunks.append(np.zeros(int(silences[i] * sr))); t_new += silences[i]
chunks.append(np.zeros(int(TAIL * sr)))
y = np.concatenate(chunks)
raw = AQUI / "media/audio/_tmp_vo.f32"; y.astype("<f4").tofile(raw)

af = ("afftdn=nr=18:nf=-50:tn=1,highpass=f=85,"
      "agate=threshold=0.0125:ratio=6:attack=4:release=160:range=0.01,"
      "equalizer=f=220:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,lowpass=f=13500,"
      "deesser=i=0.3:f=0.5,acompressor=threshold=0.06:ratio=3:attack=8:release=140:makeup=3,"
      "alimiter=limit=0.9,aformat=sample_fmts=s32:channel_layouts=stereo")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", str(raw),
                "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", str(OUT)], check=True)
raw.unlink()

def newt(t):
    for pa, pb, tn in mapping:
        if pa - 0.4 <= t <= pb + 0.05:
            return tn + (min(max(t, pa), pb) - pa)
    return None
json.dump({"mapping": mapping, "dur": float(len(y) / sr)}, open(AQUI / "vo_map.json", "w"), indent=1)

# SRT remapeado
def ts(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
blocks, out = re.split(r"\n\s*\n", SRT.read_text().strip()), []
for n, blk in enumerate(blocks, 1):
    ln = blk.splitlines(); m = re.match(r"([\d:,]+) --> ([\d:,]+)", ln[1])
    f = lambda s: sum(float(v.replace(",", ".")) * k for v, k in zip(s.split(":"), (3600, 60, 1)))
    a, e = newt(f(m.group(1))), newt(f(m.group(2)))
    if a is None or e is None: continue
    out.append(f"{len(out)+1}\n{ts(a)} --> {ts(max(e, a + 0.6))}\n" + "\n".join(ln[2:]))
(AQUI / "locucion_limpia.srt").write_text("\n\n".join(out) + "\n")
print("VO limpia:", round(len(y) / sr, 1), "s ·", len(out), "subtítulos")
