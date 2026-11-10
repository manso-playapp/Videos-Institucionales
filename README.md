# Videos Institucionales

Kit para que **Claude Code** edite videos institucionales horizontales a nivel profesional:
desde el material bruto en Google Drive hasta el paquete de entrega masterizado y controlado.

## Arranque rápido

```bash
bash setup.sh                                          # rclone, transcripción, fuentes, acceso a Drive
bash examples/generar_media_prueba.sh                  # media sintética de prueba
python3 tools/render_edl.py examples/edl-ejemplo.json  # → examples/render/ejemplo_master.mp4
python3 tools/qc.py examples/render/ejemplo_master.mp4 --fps 25
```

## Proyecto real

```bash
cp -r proyectos/_plantilla proyectos/acme                       # completar BRIEF.md
tools/drive.sh pull "<URL carpeta Drive del material>" proyectos/acme/media
python3 tools/analizar.py inventario proyectos/acme/media        # hojas de contacto por clip
python3 tools/transcribir.py proyectos/acme/media/locucion.wav --prompt "ACME, nombres"
#  … escribir proyectos/acme/edl.json (ver docs/edl-schema.md)
python3 tools/render_edl.py proyectos/acme/edl.json --draft       # iterar
python3 tools/render_edl.py proyectos/acme/edl.json               # master
python3 tools/qc.py proyectos/acme/render/*.mp4 --fps 25
tools/exportar.sh proyectos/acme/render/<master>.mp4 proyectos/acme/entregas/ACME_Institucional_2026
```

O simplemente pedile a Claude: *"Editá el institucional de ACME con el material de esta carpeta: <link>"*.
La skill `video-institucional` guía el resto.

## Contenido

| | |
|---|---|
| `docs/estandar.md` | Vara de calidad medida sobre las referencias (estructura, ritmo, color, tipografía, audio, specs) |
| `docs/edl-schema.md` | Formato de la línea de tiempo JSON |
| `tools/render_edl.py` | Motor de montaje: conform cacheado → transiciones, movimientos, grade/LUT, textos, logo, VO + música con ducking, SFX y loudness en dos pasadas |
| `tools/analizar.py` | Inventario de material y análisis de referencias (cortes, ASL, loudness, hojas de contacto) |
| `tools/transcribir.py` | Transcripción local (faster-whisper) → SRT con estándar de subtitulado + palabras con tiempo |
| `tools/qc.py` | QC de entrega: specs, LUFS y true peak, negros, congelados y silencios |
| `tools/exportar.sh` | Master, ProRes 422 HQ, versión web, poster y hoja de contacto |
| `tools/drive.sh` | Google Drive vía rclone (ls / pull / push / link) |
| `tools/motion.py` + `tools/motion/` | Motion graphics (HTML + GSAP + Lottie) y 214 transiciones de GPU renderizadas cuadro por cuadro con Chromium |
| `tools/luts.py` + `assets/luts/` | Looks de color del estudio (.cube) y muestrario comparativo |
| `docs/efectos.md` | Catálogo de transiciones, plantillas, looks y texturas, con recomendaciones de uso |
| `.claude/skills/` | `video-institucional` (propia) + `firsttake`, `business-motion-film`, `hyperframes` ([créditos](THIRD_PARTY.md)) |

Requisitos: ffmpeg ≥ 6.1, Python ≥ 3.10, Node ≥ 18 con Playwright/Chromium (motion y transiciones), rclone, y `RCLONE_DRIVE_TOKEN` en el entorno para usar Drive.
