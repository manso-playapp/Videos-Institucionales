# Brief — ZIZI Construcciones Metalúrgicas · Video institucional 2026

| Campo | Valor |
|---|---|
| Cliente / marca | ZIZI Construcciones Metalúrgicas (www.tingladoszizi.com.ar) |
| Contacto y aprobador | **PENDIENTE** |
| Objetivo del video | Institucional de cultura/relaciones: "ZIZI es la gente". Posible vínculo con Semana ZIZI (2da edición, "No es asistir. Es ser parte.") — **confirmar** |
| Público | **PENDIENTE** (¿clientes, proveedores, personal?) |
| Duración objetivo | ~1:55 según locución (VO de 1:40 a 2:00 según toma) |
| Formatos / destinos | **PENDIENTE** (default: 16:9 1080p web, −14 LUFS / −1 dBTP) |
| Fecha de entrega | **PENDIENTE** |

## Mensaje
ZIZI es la gente: construye relaciones que perduren y una cultura de trabajo.

## Datos verificados que pueden aparecer en pantalla
- "Más de 46 años de experiencia" (fuente: guion, Guion.docx)
- Web: www.tingladoszizi.com.ar y redes IG/FB/YouTube (fuente: logo del cliente)

## Locución / guion
- Guion: `media/Guion.docx` (4 bloques separados por [Pausa]: comienzo del proyecto · escucha y 46 años · gente, proveedores, clientes · apretón de manos y cierre).
- Dos tomas de locución en Drive (WhatsApp Audio, 1:37 y 2:00). Transcriptas con Whisper (SRT/JSON en media/).
  - Toma 1 (2:00, pausas largas y respiración): más cercana al guion; error de ASR "hora" por "obra".
  - Toma 2 (1:37, más ágil): ASR dudoso en "vacío", "nos eligen", "ninguna obra se hace en soledad".
  - **Decisión: se usa la toma 1 (2:00)**: mejor dicción (menos errores de ASR) y pausas largas en las [Pausa] del guion. Toma 2 queda de respaldo. Revisable si el cliente prefiere otra. Los audios son de WhatsApp (AAC): limpiar/mejorar o regrabar si hay tiempo.

## Música
- **PENDIENTE** (track + licencia).

## Marca
- Logo: `media/LOGO C redes y web.pdf` (amarillo ZIZI sobre negro; versión con web). Pedir vector/PNG con alfa.
- Tipografías / colores: amarillo ~#FDB913 (a medir del logo), negro. **Confirmar manual de marca**.
- `media/cuadernos - zizi.pdf`: cuaderno "Semana ZIZI 2da edición".

## Material
- Carpeta de Drive recibida: 1uXl13_fjsM9zc1vs91WG5xy7-n8UBTwu — **no contiene video ni fotos** (solo guion, VO, logo y PDF).
- Carpeta de entregas: **PENDIENTE**
- Referencias: Alsafex / Schneider / CINTER (docs/estandar.md)

## Personas y cliente final (dato dado por el estudio)
- Hombre de casco amarillo y camisa ZIZI: **dueño de ZIZI** (nombre a confirmar para el zócalo).
- Hombre de camisa azul: **dueño de la marca Goipat**, para quien se construye el galpón (nombre a confirmar).

## Decisiones del estudio (16-11)
- **No usar el audio de las tomas** (solo imagen). La voz es la locución A.
- **Dos entregas del mismo video**: 16:9 y **vertical 9:16** reacomodando las tomas.
- Música de fondo tranquila (Artlist; track y licencia pendientes). Ducking bajo la voz.
- Las tomas tienen que acompañar el guion. Transiciones de GPU como en Schneider (empuje, franjas, split), usadas como puntuación.

## Entregables pedidos por el cliente (19-11)
1. **Pieza horizontal 16:9** (la principal; se resuelve primero).
2. **Pieza vertical 9:16** (mismo video, tomas reacomodadas).
3. **Pieza para pantalla LED**: sin locución, con música; subtítulos/textos de apoyo si hace falta. Resolución de la pantalla: **PENDIENTE**.
4. **Versión resumida < 60 s** para YouTube Shorts, con audio (la principal dura 1:35, así que corresponde).

## Estado (19-11)
- Borrador 4 de la horizontal entregado para revisión: locución original limpia (+7 % de velocidad), 8 textos de marca, tres músicas candidatas (Signs of Summer / Winter to Spring / As Far as It Goes). Falta elección de música y visto bueno.

## Prohibido
- **PENDIENTE** (el audio original de las tomas no se usa)

## Estado al 24-11 — entregado, a la espera de devolución
Dos versiones horizontales 1080p (29,97 fps) entregadas al cliente por Drive (carpeta de ZIZI, subcarpeta `Final`):
- **Emocional** (1:27) — `ZIZI_Institucional_Emocional_1080p_v3.mp4`. Audio = mezcla final de Javier (locución de Lara + música),
  con la cola de música continuada (`tools_local/extender_mezcla.py`). Edición: `edicion_emocional.json` · EDL `edl_16x9_emocional3.json`.
- **Dinámica** (1:19) — `ZIZI_Institucional_Dinamica_1080p_v2.mp4`. Voz Carlos (ElevenLabs, argentina) a ritmo natural + «Glaciers» (Artlist, licenciada).
  Edición: `edicion_dinamica.json` · EDL `edl_16x9_dinamica2.json`.

Reglas del estudio que quedaron firmes:
- **Ninguna toma dura más de 3 s en pantalla** (cuenta la disolvencia). La placa del logo queda exceptuada (~5 s).
- **No usar tomas de operarios sobre el techo** (80–84, 86, 87): sin elementos de protección. Tampoco 70, 119, 120 (no gustaron).
- Sin sonidos en transiciones; no usar el audio de las tomas.
- Devolución del cliente (24-11): el concepto es **emocional**; faltan planos detalle y de personas en el material filmado.

Regenerar: `ZIZI_VERSION=emocional|dinamica ZIZI_TAG=_x python3 build_edl.py` → `tools/render_edl.py` → `tools/qc.py` (ahora falla si el audio termina antes que la imagen).
Editor (artefacto): https://claude.ai/artifact/TiYHN4kHMHtuL8QVu6uc21 — selector Emocional / Dinámica, cada una guarda su edición aparte.

Pendiente: devolución del cliente · vertical 9:16 · versión LED (falta resolución) · short < 60 s · master 4K si lo piden (`ZIZI_4K=1`).
