# Editor de corte en artefacto

Una página (artefacto de Claude) donde el estudio edita la línea de tiempo en el navegador: mueve y recorta tomas,
cambia una toma por otra de la biblioteca, elige transiciones, velocidad, voz, música y look. Lo que guarda vuelve al
repo y se renderiza con `tools/render_edl.py`. Nació en ZIZI (nov-2026); la implementación de referencia de un
proyecto completo es `proyectos/zizi/build_edl.py`.

Todo vive en `tools/editor/`:

| Archivo | Qué es |
|---|---|
| `index.html` | El editor. No tiene nada de un cliente: lee `proyecto.json` y `corte_<versión>.json`. |
| `editor.py` | Prepara la carpeta del artefacto y convierte en los dos sentidos (corte → editor, edición → EDL). |

## Flujo

1. **Inventario** del material: `python3 tools/analizar.py inventario proyectos/<c>/media -o proyectos/<c>/inventario`.
2. **Preparar**: `python3 tools/editor/editor.py preparar proyectos/<c> --nombre "ACME" --versiones larga:Larga,corta:Corta`
   → `proyectos/<c>/artefacto/` con `index.html`, `proyecto.json`, `media/tNNN.mp4` (proxies 426×240) y `posters/tNNN.jpg`.
3. **Nivelar color** (opcional, recomendado): `python3 tools/editor/editor.py niveles proyectos/<c> --proxies`
   → `niveles.json` (grade por toma para la EDL) y `artefacto/media_g/` (proxies ya nivelados: se publican en lugar de `media/`).
4. **Primer corte**: en el `build_edl.py` del proyecto armar la lista `S` de planos y llamar a `editor.exportar_corte(...)`
   → `artefacto/corte_<versión>.json`. Locución de muestra en mp3 al lado (`ffmpeg -i vo.wav -b:a 96k artefacto/vo.mp3`).
5. **Extras de la vista rápida** (opcionales): `editor.py overlays` (textos animados como .webm con transparencia),
   `editor.py transiciones` (muestras de cada transición), `musica/<id>.mp3` (candidatas; declararlas en `proyecto.json`),
   `cierre.mp4` (placa final), `corte_<versión>.mp4` (último render, campo `render` del corte).
6. **Publicar** con la herramienta Artifact: `file_path` = `artefacto/index.html`, `files` = todo lo demás con su ruta
   relativa (`proyecto.json`, `corte_*.json`, `media/…`, `posters/…`, `ov/…`, `trans/…`, audio), y las capacidades
   `db` y `user` (cargar antes la skill `artifact-capabilities`). Republicar al mismo URL cuando cambie algo.
7. **Leer la edición**: el editor guarda en la base del artefacto, colección `selecciones`, un documento por versión
   (`selecciones/<versión>`). Leerlo con `ArtifactData` (get) y guardarlo como `proyectos/<c>/edicion_<versión>.json`.
8. **Render**: en `build_edl.py`, `S, fx = editor.cargar_edicion(...)` y `clips = editor.clips(S, ...)`; el resto de la
   EDL (audio, overlays, grade, placa) lo arma el proyecto. Después `render_edl.py` y `qc.py` como siempre.

## Contrato de datos

**`proyecto.json`** — `{id, nombre, placa, versiones: [[id, etiqueta]], musicas: [[id, etiqueta]]}`.
`id` separa lo guardado en el navegador entre proyectos; `musicas` apunta a `musica/<id>.mp3`.

**`corte_<versión>.json`** (lo escribe `exportar_corte`) —
`{version, dur, slots, lib, palabras, voces, textos, fx, render, sinMusica}`.
- `version`: etiqueta visible ("Borrador 3"). **Si cambia, el editor descarta la edición guardada** y arranca del corte nuevo.
- `slots`: `{t, tipo: toma|split|placa|negro, n, in, tr, v?, luz?, tomas?, ins?}`. `t` = cuándo entra; la duración es hasta el siguiente.
- `lib`: biblioteca `{n: {archivo, dur, grupo, res, persona?, veto?}}`. Con `veto` la toma no se ofrece (ej. falta de elementos de protección).
- `palabras`: `[{w, t, e}]` de la locución (salida de `tools/transcribir.py`); se muestran bajo la línea de tiempo.
- `voces`: `[[id, etiqueta, archivo.mp3]]`. `sinMusica: true` cuando el audio ya es una mezcla final.

**Edición guardada** (`selecciones/<versión>`) — `{slots, notas, fx: {voz, look, grano, vineta, musica}, base, editado}`.
En la edición, `in` es el punto de la fuente que se ve **en el corte `t`** (sin contar el solape de la transición);
`cargar_edicion` + `clips` hacen ese ajuste y acortan la transición si a una toma no le sobra material.

## Lo aprendido (no repetir)

- Lo que se lee de la base del artefacto viene **congelado**: clonar antes de editar (`JSON.parse(JSON.stringify(d.slots))`).
- Al recortar, el corrimiento va **en cadena**: si la toma vecina no tiene más material, se corre la siguiente o queda negro explícito.
- El audio de la vista rápida tiene que durar lo mismo que el video (rellenar con silencio) o la reproducción se frena antes.
- El estudio quiere ver **qué tomas ya están usadas** al elegir un reemplazo, y que `Supr` elimine la toma y `Espacio` reproduzca.
- No renderizar por iniciativa propia mientras el estudio edita: dejar todo en el editor y renderizar cuando lo pidan.
- Reglas que el estudio fijó en ZIZI y conviene preguntar en cada proyecto: tope de segundos por toma (`max_plano`),
  tomas vetadas, sin sonidos en transiciones, sin audio de las tomas.
- Servido en local sin el envoltorio del artefacto, los acentos se ven mal: es solo falta del `charset`; publicado se ve bien.
