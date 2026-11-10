# Componentes de terceros

Skills incluidas sin modificaciones (salvo lo indicado), con su licencia original en cada carpeta.

| Componente | Origen | Commit | Licencia | Notas |
|---|---|---|---|---|
| `.claude/skills/firsttake` | github.com/emersonsklar/firsttake | `d1feb84` | Apache-2.0 (`LICENSE`, `NOTICE`) | Se excluyeron `docs/` y `scripts/first_run_footage/` (material de prueba de 9 MB) por peso. `scripts/first_run.py` necesita ese material: bajarlo del repo original si se usa. |
| `.claude/skills/business-motion-film` | github.com/echris6/motion-video-kit | `e4b1c00` | MIT (`LICENSE`) | |
| `.claude/skills/hyperframes`, `.claude/skills/hyperframes-cli` | github.com/heygen-com/hyperframes | `ec30de0` | Apache-2.0 (`LICENSE`) | Usa `npx hyperframes`, que manda telemetría (desactivable según su doc). |
| `assets/transitions/gl/` (214 `.glsl`) | github.com/gl-transitions/gl-transitions | `main` 2026-11 | MIT (`LICENSE`; cada shader declara la suya: 212 MIT) | `InvertedPageCurl` es BSD-3 (uso comercial OK, con atribución). `StereoViewer` no declara licencia: no usarla en entregas a clientes. |
| `assets/transitions/xfade-easing/` | github.com/scriptituk/xfade-easing | `main` 2026-09 | MIT (`LICENSE`) | Solo las expresiones generadas (`expr/`). |
| `assets/js/gsap.min.js` + plugins (CustomEase, SplitText, DrawSVG, MorphSVG, MotionPath) | npm `gsap` 3.15.1 | 3.15.1 | GSAP Standard "No Charge" License (gsap.com/standard-license): uso comercial gratuito, no es open source | Uso comercial en videos OK; leer las condiciones antes de usarlo dentro de un producto de software propio. |
| `assets/js/lottie.min.js` | npm `lottie-web` 5.13.0 (Airbnb) | 5.13.0 | MIT (`LICENSE-lottie-web.md`) | |
| `assets/fonts/Inter-*.ttf` | Inter, rsms (vía @fontsource/inter, subset latin) | 5.x | SIL OFL 1.1 (`OFL-Inter.txt`) | |
| `assets/fonts/BarlowCondensed-*.ttf` | Barlow, Jeremy Tribby (vía @fontsource/barlow-condensed, subset latin) | 5.3.0 | SIL OFL 1.1 (`OFL-BarlowCondensed.txt`) | |

Evaluados y **no** incluidos:
- **spectral-film-lut** (MIT): emulación espectral de película a partir de las hojas técnicas.
  Es una app con interfaz gráfica (PyQt6, numba, OpenCV) y la instalación no termina en el entorno
  en la nube. Usarla en una compu de escritorio y exportar los `.cube` a `assets/luts/`.
- **ffmpeg-gl-transition** / **FFmpeg-PlusPlus**: requieren compilar FFmpeg y tener GPU. Reemplazado
  por el renderizador de Chromium (`tools/motion/`), que corre los mismos shaders.
- **video-use** (browser-use): agente de edición para *talking heads* y redes; depende de
  ElevenLabs. No suma para institucionales.
- **OpenMontage** (79k ★): muy completo, pero es AGPL-3.0, pesa 165 MB y está orientado a
  generación con IA más que a montaje de material filmado. Conviene consultarlo como referencia
  y no vendorizarlo.
- **Remotion** y las skills basadas en Remotion: requieren licencia comercial para empresas de
  más de 3 personas. HyperFrames (Apache-2.0) cubre el mismo uso.
- Skills de edición vertical/reels (heditor, open-edits, edit-reel…): están pensadas para 9:16
  y *talking heads*, no para institucionales horizontales.
