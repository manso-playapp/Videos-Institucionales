#!/usr/bin/env python3
"""
transcribir.py — Transcribe locución o entrevistas (local, faster-whisper) a SRT + JSON con
tiempos por palabra. Sirve para: subtitular la locución, buscar frases en entrevistas
("dónde dice 'calidad'") y cortar por texto.

Uso:
  python3 tools/transcribir.py media/locucion.wav                 # → locucion.srt / .json
  python3 tools/transcribir.py media/entrevista.mp4 --modelo medium
  python3 tools/transcribir.py media/vo.wav --max-chars 42        # largo máx. de línea

Los subtítulos se arman con el estándar del estudio: ≤ 2 líneas, ≤ 42 caracteres por línea,
cortes en pausas/puntuación, mínimo 1 s y máximo 6 s en pantalla.
REVISAR SIEMPRE nombres propios, marcas y cifras: Whisper los inventa con confianza.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def tc(t: float) -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def wrap(words: list[str], max_chars: int) -> str:
    text = " ".join(words)
    if len(text) <= max_chars:
        return text
    # partir en dos líneas lo más parejas posible
    best, bi = 10**9, 1
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = abs(len(a) - len(b)) + (0 if len(a) <= max_chars and len(b) <= max_chars else 1000)
        if score < best:
            best, bi = score, i
    return " ".join(words[:bi]) + "\n" + " ".join(words[bi:])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--modelo", default="small", help="tiny|base|small|medium|large-v3")
    ap.add_argument("--idioma", default="es")
    ap.add_argument("--max-chars", type=int, default=42)
    ap.add_argument("--prompt", default="", help="vocabulario: marcas, nombres, siglas del cliente")
    a = ap.parse_args()
    from faster_whisper import WhisperModel

    import subprocess
    import numpy as np
    # Decodificamos con ffmpeg (acepta cualquier video/audio) a PCM 16 kHz mono.
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.audio, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    model = WhisperModel(a.modelo, device="cpu", compute_type="int8")
    segs, info = model.transcribe(audio, language=a.idioma, word_timestamps=True,
                                  vad_filter=True, initial_prompt=a.prompt or None)
    words = []
    for s in segs:
        for w in s.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    out = Path(a.audio).with_suffix("")
    Path(f"{out}.json").write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding="utf-8")

    # 1) frases: cortan en pausas > 0.35 s o puntuación fuerte
    phrases, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if not nxt or nxt["start"] - w["end"] > 0.35 or w["w"].endswith((".", "?", "!", ";", ":")):
            phrases.append(cur)
            cur = []
    # 2) cada frase larga se divide en partes equilibradas (≤ 2 líneas y ≤ 6 s)
    limit = a.max_chars * 2
    cues = []
    for ph in phrases:
        text = " ".join(x["w"] for x in ph)
        dur = ph[-1]["end"] - ph[0]["start"]
        n = max(-(-len(text) // limit), -(-int(dur * 10) // 60), 1)
        if n == 1:
            cues.append(ph)
            continue
        target = len(text) / n
        start, acc = 0, 0
        for j, w in enumerate(ph):
            acc += len(w["w"]) + 1
            remaining = len(ph) - j - 1
            if acc >= target and remaining >= 2:
                # preferir cortar después de coma o antes de conector cercano
                cut = j + 1
                for k in range(j, max(j - 3, start), -1):
                    if ph[k]["w"].endswith(","):
                        cut = k + 1
                        break
                cues.append(ph[start:cut])
                start, acc = cut, sum(len(x["w"]) + 1 for x in ph[cut:j + 1])
        cues.append(ph[start:])
    cues = [c for c in cues if c]
    lines = []
    for n, c in enumerate(cues, 1):
        st, en = c[0]["start"], max(c[-1]["end"], c[0]["start"] + 1.0)
        if n < len(cues):
            en = min(en, cues[n][0]["start"] - 0.04)
        lines += [str(n), f"{tc(st)} --> {tc(en)}", wrap([x["w"] for x in c], a.max_chars), ""]
    Path(f"{out}.srt").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(words)} palabras · {len(cues)} subtítulos · idioma {info.language}\n→ {out}.srt\n→ {out}.json")


if __name__ == "__main__":
    main()
