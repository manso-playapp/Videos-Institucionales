#!/usr/bin/env python3
"""Locución ElevenLabs (9 bloques) -> una sola pista cinematográfica: recorta silencios de cada bloque,
los coloca con pausas de guion, agrega calidez/presencia, compresión suave y un espacio (reverb corto).
Salidas: media/audio/vo_el.wav · vo_el_cues.json (inicio/fin de cada bloque y palabra)"""
import json, subprocess, numpy as np
from pathlib import Path
AQUI = Path(__file__).parent.parent
EL = AQUI / "media/audio/el"; SR = 48000
LEAD = 1.7                                   # aire inicial (la música entra sola)
GAPS = [1.3, 1.4, 1.3, 1.5, 1.2, 1.3, 1.5, 3.6]   # pausa tras B1..B8
END = 100.2                                  # largo de la música (termina sola)

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").copy()
def trim(x, thr_db=-46, pad=0.10):
    a = np.abs(x); w = int(SR * 0.01); env = np.convolve(a, np.ones(w) / w, "same")
    idx = np.where(env > 10 ** (thr_db / 20))[0]
    i0 = max(idx[0] - int(pad * SR), 0); i1 = min(idx[-1] + int(pad * SR * 2), len(x))
    seg = x[i0:i1].copy(); f = int(0.02 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f * 3:] *= np.linspace(1, 0, f * 3)
    return seg
blocks = [trim(load(EL / f"B{i}.mp3")) for i in range(1, 10)]
t = LEAD; out = np.zeros(int(END * SR), dtype=np.float32); cues = []
for i, b in enumerate(blocks):
    s = int(t * SR); out[s:s + len(b)] += b[:len(out) - s]
    cues.append({"block": i + 1, "start": round(t, 3), "end": round(t + len(b) / SR, 3)})
    t += len(b) / SR + (GAPS[i] if i < len(GAPS) else 0)
raw = AQUI / "media/audio/_vo_raw.f32"; out.astype("<f4").tofile(raw)
# reverb corto sintético (respuesta al impulso: ruido filtrado con decaimiento exponencial, 0.9 s)
rng = np.random.default_rng(7); n = int(0.9 * SR); tt = np.arange(n) / SR
ir = (rng.standard_normal(n) * np.exp(-tt / 0.22)).astype("<f4"); ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
irp = AQUI / "media/audio/_ir.f32"; ir.tofile(irp)
fc = ("[0:a]highpass=f=75,equalizer=f=130:t=h:w=1:g=1.5,equalizer=f=260:t=q:w=1:g=-1.5,"
      "equalizer=f=3400:t=q:w=1.1:g=2,deesser=i=0.35:f=0.5,"
      "acompressor=threshold=0.09:ratio=2.6:attack=12:release=180:makeup=2.5,asplit[dry][w];"
      "[w][1:a]afir=dry=0:wet=1,lowpass=f=6500,volume=-19dB[wet];"
      "[dry][wet]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89,aformat=sample_fmts=s32:channel_layouts=stereo[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(irp), "-filter_complex", fc, "-map", "[o]",
                "-ar", str(SR), "-c:a", "pcm_s24le", str(AQUI / "media/audio/vo_el.wav")], check=True)
raw.unlink(); irp.unlink()
json.dump(cues, open(AQUI / "vo_el_cues.json", "w"), indent=1)
print("bloques:", [(c["block"], c["start"], c["end"]) for c in cues])
