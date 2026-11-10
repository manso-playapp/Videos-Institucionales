# Videos Institucionales — Experiencias Audiovisuales

Repositorio de trabajo para editar **videos institucionales horizontales a nivel profesional**
(16:9 y formatos de pantalla LED) desde Claude Code, sin NLE, con FFmpeg + herramientas propias.
Unidad de negocio: Experiencias Audiovisuales (Javier Manso). Edición humana de referencia:
Pablo Benzaquen. Idioma de trabajo: español rioplatense.

## Antes de editar
1. Usá la skill **`video-institucional`** (`.claude/skills/video-institucional/SKILL.md`): define el flujo completo.
2. Leé `docs/estandar.md`: es la vara de calidad medida sobre las referencias del estudio.
3. Si es una sesión nueva en la nube: `bash setup.sh` (instala rclone y faster-whisper y verifica fuentes).

## Estructura
```
.claude/skills/        skills: video-institucional (propia) + firsttake, business-motion-film, hyperframes (terceros)
tools/                 render_edl.py · analizar.py · transcribir.py · qc.py · drive.sh · exportar.sh
docs/                  estandar.md (vara de calidad) · edl-schema.md (formato de la línea de tiempo)
assets/fonts/          tipografías del estudio (Barlow Condensed, OFL) + las de cada cliente
examples/              EDL de ejemplo
proyectos/<cliente>/   BRIEF.md · planos.md · edl.json · media/ (no versionado) · entregas/ (no versionado)
```

## Reglas
- Media (video/audio/imágenes pesadas) **no se commitea**: vive en Drive y se baja con `tools/drive.sh`.
- Referencias de nivel esperado: Drive `1KXB3dRwdVJe9fg8ieclaclFpCV4sl7Q2`.
- Nunca inventar datos del cliente en pantalla (cifras, certificaciones, cargos).
- Todo master pasa `tools/qc.py` antes de entregarse. Entregar a −14 LUFS / −1 dBTP (web) salvo pedido.
- Las credenciales de Drive vienen por variables de entorno (`RCLONE_DRIVE_TOKEN`); nunca escribirlas a archivos del repo.
