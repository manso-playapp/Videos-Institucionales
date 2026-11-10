---
name: video-institucional
description: Editar videos institucionales y corporativos horizontales (16:9 y formatos de pantalla LED) a nivel profesional, con el estándar del estudio. Usar cuando haya que editar, armar, cortar, subtitular, colorear, mezclar, masterizar o entregar un video institucional, un video de empresa o planta, un spot o un contenido para evento; cuando haya que bajar material o referencias de Google Drive; o cuando haya que revisar un corte contra las referencias de calidad.
---

# Video institucional horizontal

El objetivo es entregar piezas al nivel de las referencias del estudio (Alsafex, Schneider,
CINTER): aéreos de apertura, proceso industrial con datos duros, personas, producto aplicado y
cierre con logo, con color consistente, ritmo musical y audio masterizado. **Leé
`docs/estandar.md` antes del primer corte de cada proyecto**: tiene los números medidos.

## Herramientas (en `tools/`, todas probadas)

| Paso | Herramienta |
|---|---|
| Traer material/referencias de Drive y subir entregas | `tools/drive.sh ls|pull|push <URL o ID>` |
| Inventario del material bruto (specs + hoja de contacto por clip) | `python3 tools/analizar.py inventario <carpeta>` |
| Medir una referencia o nuestro corte (cortes, ASL, loudness, contacto) | `python3 tools/analizar.py ref <video>` |
| Transcribir locución/entrevistas → SRT + palabras con tiempo | `python3 tools/transcribir.py <audio> --prompt "marcas, nombres"` |
| Armar el video desde la línea de tiempo JSON | `python3 tools/render_edl.py <edl.json> [--draft]` (ver `docs/edl-schema.md`) |
| QC del master (specs, loudness, negros, congelados, silencios) | `python3 tools/qc.py <master> [--perfil web|broadcast|evento]` |
| Paquete de entrega (master, ProRes, web, poster, contacto) | `tools/exportar.sh <master> entregas/<Cliente>_Institucional_<año>` |

Si falta algo (rclone, faster-whisper): `bash setup.sh`.

## Flujo de trabajo

### 1. Brief (antes de tocar material)
Copiá `proyectos/_plantilla/` a `proyectos/<cliente>/` y completá `BRIEF.md`: cliente, objetivo,
público, duración, formato(s) y destino (web, evento, LED, TV), **datos verificados** que pueden
aparecer en pantalla, guion/locución, música, logo y tipografías de marca. Si falta un dato, se
pregunta: **nunca se inventan cifras, certificaciones, nombres ni cargos**.

### 2. Ingesta y visionado
1. `tools/drive.sh pull <carpeta del cliente> proyectos/<cliente>/media`
2. `python3 tools/analizar.py inventario proyectos/<cliente>/media`
3. **Mirá las hojas de contacto** (Read sobre los .jpg) y anotá en `proyectos/<cliente>/planos.md`
   los planos buenos: archivo, in/out, qué se ve, escala (general/medio/detalle), movimiento,
   calidad (foco, exposición, estabilidad). Para elegir in/out precisos, sacá cuadros sueltos
   con `ffmpeg -ss T -i clip -frames:v 1 x.jpg` o una hoja más densa del tramo.
4. Si hay frame rates mezclados, definí el fps del proyecto (25p por defecto) y marcá qué
   material de 50/60p sirve para cámara lenta.

### 3. Estructura y guion de montaje
Armá en `planos.md` la escaleta por bloques (apertura de escala → quiénes somos → proceso con
datos → personas → producto aplicado → cierre + logo) con duración objetivo por bloque.
Con locución: transcribila, revisá el SRT (nombres, cifras, tildes) y usala como columna
vertebral: cada frase pide un plano que la ilustre literalmente.

### 4. Primer corte (draft)
Escribí `proyectos/<cliente>/edl.json` (partí de `examples/edl-ejemplo.json`) y renderizá con
`--draft`. Reglas de montaje:
- Alternar escalas; nunca dos planos iguales seguidos; no repetir planos.
- Ritmo de las referencias: mediana ~1 s por plano (0,7–2 s) en proceso y personas; aéreos de
  apertura/cierre y placas 3–5 s.
- Cortar sobre el pulso musical; corte directo por defecto, disolvencia solo entre bloques.
- Todo plano con movimiento; si es fijo, `move` push-in de 3–8 %.
- Cámara lenta solo con material de alta velocidad de cuadro.

### 5. Autorrevisión (obligatoria antes de mostrar)
1. `python3 tools/analizar.py ref <draft>` y **mirá la hoja de contacto** como lo haría el
   cliente: ¿se entiende qué hace la empresa sin sonido? ¿Hay saltos de color? ¿Planos
   repetidos? ¿Textos legibles y sin errores?
2. Compará el ASL y la estructura con las referencias (`docs/estandar.md` §1).
3. Corregí y volvé a renderizar. Recién ahí renderizá el master.

### 6. Color, textos y audio
- Grade global en `grade` (LUT + ajustes); correcciones puntuales por plano en `clip.grade`.
  Objetivo: consistencia plano a plano.
- Textos con los estilos del estándar (`subtitulo`, `dato`, `zocalo_*`, `titulo`). Tipografías
  del cliente en `assets/fonts/` si las hay.
- VO + música con ducking + ambiente/SFX; la música termina con el video.
- Animaciones complejas (logo animado, infografía, collage LED, mapas): skill `hyperframes`,
  y el render resultante entra como un plano más en la EDL.

### 7. Master, QC y entrega
1. `python3 tools/render_edl.py proyectos/<cliente>/edl.json`
2. `python3 tools/qc.py <master> --fps 25` → tiene que dar APROBADO.
3. `tools/exportar.sh <master> proyectos/<cliente>/entregas/<Cliente>_Institucional_<año>`
4. `tools/drive.sh push proyectos/<cliente>/entregas <carpeta de entregas>` solo cuando el
   usuario lo pida, e informá los archivos y los resultados del QC.

## Otras skills instaladas y cuándo usarlas

- `firsttake`: post-producción "medida": sincronizar cámaras sin timecode, igualar el color de
  dos cámaras, identificar logs, diarización de entrevistas, armar proyectos para **DaVinci
  Resolve/Premiere** cuando el editor humano (Pablo) quiera terminar en un NLE, y planificar
  rodajes (checklists, offload verificado).
- `business-motion-film`: piezas cortas tipo *launch film* (15–40 s) y el **loop de crítico
  independiente** ("Gauntlet") para revisar un corte con ojos frescos.
- `hyperframes` / `hyperframes-cli`: motion graphics en HTML renderizado a video (títulos,
  infografías, logos animados, collages para pantallas LED).

## Principios

- **Medir, no suponer**: specs, loudness, ritmo y QC salen de las herramientas, no de la intuición.
- **Mirar el resultado**: después de cada render, leé la hoja de contacto. Un render sin error no
  es un buen video.
- **Verdad**: solo datos del brief o del cliente. Ante la duda, se pregunta.
- Los archivos de media no se commitean (están en `.gitignore`); el proyecto se versiona como
  texto: `BRIEF.md`, `planos.md`, `edl.json`, SRT revisados.
