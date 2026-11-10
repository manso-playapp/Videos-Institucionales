# Componentes de terceros

Skills incluidas sin modificaciones (salvo lo indicado), con su licencia original en cada carpeta.

| Componente | Origen | Commit | Licencia | Notas |
|---|---|---|---|---|
| `.claude/skills/firsttake` | github.com/emersonsklar/firsttake | `d1feb84` | Apache-2.0 (`LICENSE`, `NOTICE`) | Se excluyeron `docs/` y `scripts/first_run_footage/` (material de prueba de 9 MB) por peso. `scripts/first_run.py` necesita ese material: bajarlo del repo original si se usa. |
| `.claude/skills/business-motion-film` | github.com/echris6/motion-video-kit | `e4b1c00` | MIT (`LICENSE`) | |
| `.claude/skills/hyperframes`, `.claude/skills/hyperframes-cli` | github.com/heygen-com/hyperframes | `ec30de0` | Apache-2.0 (`LICENSE`) | Usa `npx hyperframes`, que manda telemetría (desactivable según su doc). |
| `assets/fonts/Inter-*.ttf` | Inter, rsms (vía @fontsource/inter, subset latin) | 5.x | SIL OFL 1.1 (`OFL-Inter.txt`) | |
| `assets/fonts/BarlowCondensed-*.ttf` | Barlow, Jeremy Tribby (vía @fontsource/barlow-condensed, subset latin) | 5.3.0 | SIL OFL 1.1 (`OFL-BarlowCondensed.txt`) | |

Evaluados y **no** incluidos:
- **OpenMontage** (79k ★): muy completo, pero es AGPL-3.0, pesa 165 MB y está orientado a
  generación con IA más que a montaje de material filmado. Conviene consultarlo como referencia
  y no vendorizarlo.
- **Remotion** y las skills basadas en Remotion: requieren licencia comercial para empresas de
  más de 3 personas. HyperFrames (Apache-2.0) cubre el mismo uso.
- Skills de edición vertical/reels (heditor, open-edits, edit-reel…): están pensadas para 9:16
  y *talking heads*, no para institucionales horizontales.
