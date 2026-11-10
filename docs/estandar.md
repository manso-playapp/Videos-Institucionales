# Estándar de calidad — Videos institucionales horizontales

Derivado de **medir** las 4 piezas de referencia de la carpeta
[Nivel esperado](https://drive.google.com/drive/folders/1KXB3dRwdVJe9fg8ieclaclFpCV4sl7Q2)
con `tools/analizar.py ref`. Es la vara mínima: cada entrega tiene que estar a este nivel o arriba.

## 1. Lo que dicen las referencias

| Pieza | Formato | Duración | Cortes duros | Plano medio (ASL) | Loudness | True peak |
|---|---|---|---|---|---|---|
| A (Alsafex, versión larga) | 1920×1080 · 25p · H.264 20 Mbps | 2:17 | 59 | 2,3 s (mediana 1,5 s) | −7,2 LUFS | **+2,3 dBTP ⚠️** |
| Schneider (master HD) | 1920×1080 · 25p · H.264 15 Mbps | 0:43 | 39 | 1,1 s (mediana 0,8 s) | −11,8 LUFS | +0,2 dBTP ⚠️ |
| CINTER | 1920×1080 · 29,97p · H.264 31 Mbps | 1:18 | 80 | 1,0 s (mediana 0,7 s) | −14,2 LUFS | −0,1 dBTP ⚠️ |
| Alsafex 2025 (pantalla LED) | **2048×640** · 24p · H.264 10 Mbps | 2:49 | 6 (collage animado) | — | −13,4 LUFS | −1,9 dBTP |

Análisis completos y hojas de contacto: [`docs/referencias/`](referencias/).

\* El detector cuenta solo los cortes duros; las disolvencias y los planos con movimiento lento
alargan el ASL. En la práctica: **mediana de ~1 s por plano (0,7–2 s) en bloques de proceso y
personas; 3–5 s en aéreos de apertura/cierre y placas.** Un corte con planos de 3 s parejos se
siente lento comparado con estas piezas.

> ⚠️ A, Schneider y CINTER están masterizados **a 0 dBTP o por encima** (clipping/inter-sample peaks). Es un
> defecto, no un estilo: nosotros entregamos a −14 LUFS / −1 dBTP (web) y se escucha igual de
> fuerte en YouTube/LinkedIn/Instagram, que normalizan hacia abajo.

## 2. Estructura narrativa (lo que comparten las 4)

1. **Apertura de escala** (0–8 s): aéreo de drone de la ciudad/planta, luz de amanecer o
   atardecer, movimiento lento. Sin texto o con una frase.
2. **Quiénes somos** (8–25 s): edificio/fachada → interior → personas trabajando. La locución
   dice qué hace la empresa en una frase.
3. **Proceso y capacidad** (25–60 %): planta, máquinas, detalles macro del producto, manos.
   Aquí van los **datos duros** (m², kg/mes, años, empleados, certificaciones).
4. **Personas y valores**: equipo, miradas, trabajo en conjunto, atención al cliente, logística.
5. **Producto aplicado / impacto**: la obra terminada, el producto en uso, el cliente final.
6. **Cierre aspiracional + logo** (últimos 4–6 s): aéreo o hero shot, frase de marca, logo
   sobre placa limpia o integrado sobre el plano. La música resuelve en el logo.

## 3. Lenguaje visual

- **Planos**: alternar escalas siempre (general → medio → detalle). Nunca dos planos de la
  misma escala y ángulo seguidos. Macro de producto con poca profundidad de campo = "premium".
- **Movimiento**: casi todo plano tiene movimiento (gimbal, slider, drone). Si el material es
  fijo, agregar push-in sutil (3–8 %) con `move` en la EDL. Nada de zooms digitales bruscos.
- **Cámara lenta**: solo desde material de 50/60p (o más) conformado a 25p. Nunca ralentizar
  material de 25p por debajo de 0,8× (se ve a saltos).
- **Color**: look limpio y frío-neutro en industria (azules/verdes petróleo en sombras, blancos
  limpios), contraste medio, negros que no se empastan, piel natural. Grade **consistente
  plano a plano**: es lo primero que delata a un amateur.
- **Transiciones**: corte directo por defecto. Disolvencia solo para pasar de bloque o en
  aéreos lentos. Fundidos a negro/blanco solo en apertura y cierre. Sin wipes "de plantilla".
- **Ritmo**: cortes sobre el pulso de la música (marcar beats). Bloques de proceso más
  rápidos; apertura y cierre respiran.
- **Split screens / collage** (Schneider, Alsafex LED): 2–3 paneles con bordes redondeados o
  separadores finos; útiles para mostrar variedad de producto.

## 4. Tipografía en pantalla

| Uso | Estilo EDL | Referencia | Especificación (a 1080p) |
|---|---|---|---|
| Subtítulo de locución | `subtitulo` | Alsafex, Schneider | Sans regular (Inter), 38–42 px, blanco, centrado, base a ~70 px del borde inferior, sombra suave. ≤ 2 líneas, ≤ 42 caracteres/línea. |
| Dato / claim | `dato` | CINTER, Alsafex LED | Condensada semibold/bold en MAYÚSCULAS (Barlow Condensed), 70–80 px, alineada a la izquierda en el tercio inferior, entra deslizando. |
| Zócalo de entrevista | `zocalo_nombre` + `zocalo_cargo` | — | Nombre en condensada bold mayúsculas + cargo en sans light. |
| Título / capítulo | `titulo` | — | Sans semibold 80–90 px centrado. |
| Cierre | placa + logo | Schneider, CINTER | Logo oficial del cliente (vector/PNG con alfa), sobre placa blanca o sobre el último aéreo. |

Reglas: márgenes de seguridad del 10 % (title-safe), nunca texto sobre zonas de alto detalle,
mismo tamaño y posición para el mismo tipo de texto en todo el video. **Las tipografías de
marca del cliente reemplazan a las del estudio** cuando existan (copiarlas a `assets/fonts/`).

## 5. Audio

- Locución profesional, procesada (filtro pasa-altos a 80 Hz, compresión suave, de-esser si
  hace falta). La música baja automáticamente debajo de la locución (*ducking*).
- Música: corporativa-emotiva, *build* progresivo, final resuelto sobre el logo. Cortar la
  música para que **termine con el video** (no fade-out a mitad de frase musical).
- Sonido ambiente/SFX de planta en momentos clave (máquina, soldadura, camión) a bajo nivel:
  da realismo.
- **Loudness de entrega** (lo valida `tools/qc.py`):
  - Web/redes: **−14 LUFS integrado, −1 dBTP** (perfil `web`, por defecto)
  - TV/broadcast: −23 LUFS, −1 dBTP (perfil `broadcast`)
  - Eventos/pantallas: −16 LUFS (perfil `evento`; ajustar al sistema de sonido)

## 6. Especificaciones de entrega

| Archivo | Spec |
|---|---|
| Master | H.264 High, 1920×1080 (o 3840×2160 si todo el material es 4K), fps del proyecto (25p por defecto; 29,97/24 si el material lo pide), yuv420p, bt709 etiquetado, ~20 Mbps, AAC 320 kbps 48 kHz |
| Mezzanine | ProRes 422 HQ, PCM 24 bit |
| Web | H.264 8 Mbps, AAC 192 kbps, faststart |
| Pantallas LED / formatos especiales | Resolución nativa del pixel map del cliente (ej. 2048×640), sin escalar |
| Extras | Poster JPG, hoja de contacto, SRT de subtítulos si aplica |

Nombres: `<Cliente>_Institucional_<año>_<variante>.<ext>` — `tools/exportar.sh` arma el paquete.

## 7. Checklist antes de mostrar al cliente

- [ ] `tools/qc.py` aprobado
- [ ] Revisé la hoja de contacto completa: sin planos repetidos, sin saltos de color
- [ ] Nombres propios, marcas, cifras y cargos verificados contra el brief (nada inventado)
- [ ] Ortografía y tildes de todos los textos
- [ ] Logo oficial, en su versión correcta y con aire alrededor
- [ ] Música licenciada (guardar la licencia en la carpeta del proyecto)
- [ ] Escuché el mix completo con auriculares y en parlante de notebook
