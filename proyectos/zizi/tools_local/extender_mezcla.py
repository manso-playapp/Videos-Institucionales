#!/usr/bin/env python3
"""La mezcla de Javier (locución + música) funde la música a silencio junto con la última palabra, y el video sigue ~6 s (última toma + logo).
La música sigue estando en el archivo, solo que atenuada: se le devuelve el nivel que tenía en las pausas entre frases (deshace el fundido)
y se cierra con un fundido propio al final del video. No se agrega ni se inventa música.
Salida: media/audio/mezcla_javier_ext.wav"""
import subprocess, numpy as np, os
from pathlib import Path
A = Path(__file__).parent.parent; SR = 44100; END = 86.8; T0 = 80.35          # T0: después de la última palabra
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(A / 'media/audio/mezcla_javier.wav'), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout, dtype='<f4').reshape(-1, 2).copy()
n = int(END * SR); x = x[:n] if len(x) >= n else np.vstack([x, np.zeros((n - len(x), 2), np.float32)])
mono = x.mean(1).astype(np.float64)
def media_movil(v, w):
    c = np.cumsum(np.concatenate([[0.0], v])); h = w // 2; i = np.arange(len(v)); a = np.maximum(i - h, 0); b = np.minimum(i + h + 1, len(v)); return (c[b] - c[a]) / (b - a)
env = np.sqrt(media_movil(mono ** 2, int(0.5 * SR)) + 1e-14); db = lambda v: 20 * np.log10(v + 1e-12)
seg = lambda m: ' '.join(f"{db(np.sqrt(np.mean(m[int(t * SR):int((t + 1) * SR)] ** 2))):.0f}" for t in range(76, 86))
print('original, dB por segundo desde 76:', seg(mono))
ref = np.percentile(env[int(10 * SR):int(78 * SR)], 3); print('música sola en las pausas ≈', round(float(db(ref)), 1), 'dB')
i0 = int(T0 * SR); gg = np.clip(ref / env[i0:], 1.0, 10 ** (42 / 20))
r = int(0.6 * SR); gg[:r] = 1 + (gg[:r] - 1) * np.linspace(0, 1, r); gg = media_movil(gg, int(0.6 * SR))
g = np.ones(n); g[i0:] = gg; fo = int(2.6 * SR); g[-fo:] *= np.linspace(1, 0, fo) ** 1.5
y = x * g[:, None]
print('nuevo,    dB por segundo desde 76:', seg(y.mean(1))); print('ganancia máxima:', round(float(db(g.max())), 1), 'dB · pico de la cola', round(float(db(np.abs(y[i0:]).max())), 1), 'dBFS')
raw = A / 'media/audio/_ext.f32'; y.astype('<f4').tofile(raw)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(raw), '-c:a', 'pcm_s24le', '-ar', '48000', str(A / 'media/audio/mezcla_javier_ext.wav')], check=True); os.remove(raw)
