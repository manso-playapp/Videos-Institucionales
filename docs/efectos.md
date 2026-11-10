# Efectos, transiciones, motion graphics y looks

Todo se usa desde la EDL (`docs/edl-schema.md`) o por línea de comandos. Todo está probado en el
entorno en la nube: Chromium headless con WebGL por software (SwiftShader) y FFmpeg 6.1.

## 1. Transiciones

### Nativas (FFmpeg `xfade`, instantáneas)
`cut` (default) · `dissolve` · `fadeblack` · `fadewhite` · `wipeleft/right` · `slideleft/right` ·
`smoothleft/right` · `circleopen` · `zoomin` · `hblur`

### De GPU con curva de aceleración (gl-transitions, 214 shaders)
```json
"transition_in": {"type": "gl:DirectionalWarp", "dur": 0.8, "ease": "cubic-in-out",
                  "uniforms": {"smoothness": 0.3}}
```
- **Muestrario visual** de las 214: [`docs/transiciones.jpg`](transiciones.jpg) (cuadro al 50 %).
- Lista con descripciones: `python3 tools/motion.py lista`.
- Curvas: `linear`, `sine-in-out`, `quad-in-out`, `cubic-in-out` (default), `quart-in-out`,
  `quint-in-out`, `expo-in-out`, `cubic-out`, `quint-out`, `cubic-in`.
- Si a una nativa se le agrega `"ease"`, se renderiza con su equivalente de GPU: `dissolve` → `Fade`,
  `wipeleft` → `DirectionalWipe`, `slideleft` → `Directional`, y así con las demás.
- Costo: ~10 s de render por segundo de transición en 1080p. Queda en caché (`.cache/motion/`).

**Recomendadas para institucionales** (sobrias, "de agencia"):

| Uso | Transición |
|---|---|
| Cambio de bloque elegante | `Fade` con `quint-in-out`, `FadeColor` (pasa por negro), `DefocusBlur` |
| Energía / proceso industrial | `DirectionalWarp`, `Directional` (empuje), `TangentMotionBlur`, `CrossZoom` |
| Hacia el cierre / logo | `CrossZoom`, `SimpleZoom`, `ZoomInOut`, `DreamyZoom` |
| Revelado con luz | `LightWipe`, `LumaWipe`, `LuminanceMelt` |
| Evitar en corporativo | corazones, caleidoscopios, páginas que se doblan, pixelados: se ven "de plantilla" |

Regla del estándar: **corte directo por defecto**. Las transiciones son puntuación: 3 a 6 por minuto
como máximo, siempre en cambios de bloque o sobre un golpe de la música.

> `assets/transitions/xfade-easing/` tiene las expresiones originales de xfade-easing (curvas y
> transiciones en FFmpeg puro). Funcionan, pero tardan entre 30 y 70 s por segundo de transición en
> 1080p, así que el motor usa GPU. Quedan como referencia y para formatos chicos.

## 2. Motion graphics (plantillas HTML + GSAP)

Se usan como `overlays` en la EDL (con transparencia sobre el video) o como plano completo:
```json
"overlays": [
  {"template": "dato",   "params": {"valor": "240.000", "prefijo": "+", "etiqueta": "kg mensuales"}, "start": 12, "dur": 3},
  {"template": "zocalo", "params": {"nombre": "María Gómez", "cargo": "Gerente de Calidad"}, "start": 30, "dur": 4},
  {"template": "titulo", "params": {"texto": "Calidad que se construye", "modo": "palabras"}, "start": 2, "dur": 3.5},
  {"template": "luz",    "params": {"semilla": 3}, "start": 0.2, "dur": 2.5, "opacity": 0.7},
  {"template": "lottie", "params": {"src": "proyectos/acme/motion/logo.json"}, "start": 58}
]
```
| Plantilla | Qué hace | Parámetros clave |
|---|---|---|
| `dato` | Cifra que cuenta + barra de acento + etiqueta (CINTER/Alsafex) | `valor`, `prefijo`, `sufijo`, `etiqueta`, `align`, `x`, `y`, `acento`, `contar` |
| `zocalo` | Nombre + cargo con barra y máscara | `nombre`, `cargo`, `fondo` (placa translúcida), `acento` |
| `titulo` | Texto cinético por palabras, letras o líneas | `texto`, `sub`, `modo`, `fuente`, `peso`, `size`, `mayus`, `align` |
| `cierre` | Placa final: logo con brillo, línea, frase y web | `logo`, `frase`, `web`, `fondo`, `color`, `logo_ancho`, `estilo` (`luz`/`limpio`) |
| `lottie` | Animación de **After Effects** (Bodymovin) o LottieFiles | `src`, `fit`, `escala`, `x`, `y`, `textos` (reemplaza texto por nombre de capa), `velocidad` |
| `luz` | Light leak orgánico generado (se mezcla en modo *screen*) | `semilla`, `paleta`, `intensidad`, `forma` (`leak`/`flare`) |

- Se adaptan solas a cualquier lienzo (16:9, 4K o LED 2048×640): están diseñadas a 1080 de alto y escalan.
- Tipografías de marca del cliente: `"fonts": [{"family": "Marca", "src": "proyectos/acme/fonts/Marca-Bold.otf", "weight": 700}]`
  dentro de `params`, y luego `"fuente": "Marca"`.
- Para renderizar una sola: `python3 tools/motion.py plantilla dato -p '{...}' -o render/dato.mov --alpha`.
- **Plantillas nuevas:** copiar una de `tools/motion/templates/`. El contrato es
  `defineMotion(async (tl, params, env, k) => duracion)`: se arma una línea de tiempo GSAP y el
  renderizador la recorre cuadro por cuadro. Están disponibles los plugins GSAP SplitText,
  CustomEase, DrawSVG, MorphSVG y MotionPath (`assets/js/`).

### Animaciones de After Effects (Lottie)
1. En AE, instalar **Bodymovin** y exportar la composición a `.json` (sin imágenes rasterizadas
   si se puede; las fuentes, como *glyphs* o tipografías instaladas).
2. Copiarla a `proyectos/<cliente>/motion/` y usarla con `{"template": "lottie", ...}`.
3. Para cambiar textos sin volver a AE: `"textos": {"Nombre de la capa": "Texto nuevo"}`.

## 3. Split screen
Plano especial con 2 a 4 paneles (estilo Schneider/Alsafex), con separación y entrada escalonada:
```json
{"split": [{"src": "media/a.mp4", "in": 3}, {"src": "media/b.mp4", "in": 8, "move": {"type": "push_in"}},
           {"src": "media/c.mp4", "in": 1}], "dur": 2.5, "gap": 14, "layout": "h", "stagger": 0.12}
```
`layout`: `h` (columnas) o `grid` (2×2 con 4 paneles).

## 4. Looks de color (LUTs del estudio)
`assets/luts/*.cube`, generados con `python3 tools/luts.py generar`. Muestra:
[`docs/looks.jpg`](looks.jpg).

| LUT | Para |
|---|---|
| `estudio_industrial` | Planta, metal, arquitectura (Alsafex/Schneider): sombras petróleo, blancos limpios |
| `estudio_calido` | Personas, oficinas, hospitalidad |
| `estudio_cine` | Teal & orange moderado con *roll-off* de altas luces |
| `estudio_limpio` | Solo contraste suave y *roll-off*; arregla material "plano" sin cambiar el color |
| `estudio_atardecer` | Aéreos de amanecer y atardecer |
| `estudio_bn` | Blanco y negro de contraste (testimonios, archivo) |

Todos protegen los tonos de piel. Se aplican sobre material en Rec.709: si es **log** (S-Log, V-Log,
D-Log), primero va el LUT de conversión del fabricante (`clip.grade.lut`) o la skill `firsttake`
para identificarlo. Uso: `"grade": {"lut": "assets/luts/estudio_industrial.cube", "contrast": 1.02}` (las rutas se
buscan primero junto a la EDL y después desde la raíz del repo).

## 5. Texturas
- **Grano:** `"grade": {"grain": 4}` (3 a 6, sutil).
- **Viñeta:** `"grade": {"vignette": true}`.
- **Light leaks / destellos:** plantilla `luz`.
- **Packs comprados** (polvo, grano de película escaneado, *light leaks* reales de Artlist u otros):
  van como `overlays` con `"src"` y `"blend": "screen"`.
