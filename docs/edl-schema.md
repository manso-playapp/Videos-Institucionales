# EDL — la línea de tiempo en JSON

`tools/render_edl.py` arma el video a partir de un archivo `edl.json`. Las rutas relativas se
buscan primero junto al JSON y después desde la raíz del repo. Ejemplo completo: [`examples/edl-ejemplo.json`](../examples/edl-ejemplo.json).

```bash
python3 tools/render_edl.py proyectos/<cliente>/edl.json --draft   # preview 540p rápido
python3 tools/render_edl.py proyectos/<cliente>/edl.json           # master
```

Cómo funciona: **etapa 1 (conform)**: cada plano se recorta, se reencuadra al lienzo y se le
aplican la velocidad, el movimiento y el grade, y se guarda como intermedio ProRes en
`.cache/conform/` (en draft, como H.264). Si el plano no cambió, se reutiliza: re-renderizar
después de tocar un texto o la música tarda segundos. **Etapa 2**: se ensamblan los planos con
las transiciones, los textos, el logo y la mezcla de audio, y se hace la normalización de
loudness en dos pasadas.

## Campos

```jsonc
{
  "output": "render/Cliente_Institucional_2026.mp4",
  "canvas": {"width": 1920, "height": 1080, "fps": 25},   // LED: {"width": 2048, "height": 640, "fps": 24}

  // Grade global, aplicado a cada plano (las imágenes/placas lo omiten salvo "global_grade": true)
  "grade": {
    "lut": "assets/luts/estudio_industrial.cube",  // ver docs/efectos.md §4
    "contrast": 1.05, "saturation": 1.05, "gamma": 1.0, "brightness": 0.0,
    "temperature": -0.2,             // -1 frío … +1 cálido
    "sharpen": 0.3, "vignette": true, "grain": 4
  },
  "fade": {"in": 0.6, "out": 1.0, "color": "black"},

  "clips": [
    {
      "src": "media/DJI_0012.MP4",
      "in": 12.4, "out": 15.6,              // segundos en la fuente (o "dur" = duración en timeline)
      "speed": 0.5,                          // 0.5 = cámara lenta (solo desde 50/60p)
      "move": {"type": "push_in", "amount": 0.05},   // push_in | pull_out | pan_left | pan_right ; "ease": true
      "fit": "cover",                        // cover (llena y recorta) | contain (encaja, con "bg")
      "grade": {"brightness": 0.03},         // corrección puntual de este plano (antes del global)
      "global_grade": true,
      "audio": true, "audio_gain_db": -14,   // usar sonido directo del plano (ambiente / testimonio)
      "transition_in": {"type": "dissolve", "dur": 0.5}
      // nativas: cut (default) | dissolve | fadeblack | fadewhite | wipeleft | slideleft |
      //          smoothleft | circleopen | zoomin | hblur ...   (+ "ease" → versión GPU con curva)
      // GPU:     {"type": "gl:DirectionalWarp", "dur": 0.8, "ease": "cubic-in-out", "uniforms": {...}}
      //          214 transiciones, ver docs/efectos.md y docs/transiciones.jpg
    },
    // Split screen (2–4 paneles)
    {"split": [{"src": "media/a.mp4", "in": 3}, {"src": "media/b.mp4", "in": 8}], "dur": 2.5,
     "gap": 14, "layout": "h", "stagger": 0.12},
    // Placa/animación de cierre renderizada con tools/motion.py (sin grade global)
    {"src": "motion/cierre.mov", "global_grade": false},
    {"src": "assets/placa_logo.png", "dur": 3, "fit": "contain", "bg": "white",
     "transition_in": {"type": "fadewhite", "dur": 0.6}}
  ],

  // Textos sueltos (datos, zócalos, títulos). Estilos en tools/render_edl.py → STYLES
  "texts": [
    {"text": "70.000 m² de producción", "start": 12.0, "end": 15.0, "style": "dato"},
    {"text": "María Gómez", "start": 30, "end": 34, "style": "zocalo_nombre"},
    {"text": "Gerente de Calidad", "start": 30, "end": 34, "style": "zocalo_cargo"}
    // se puede pisar: "size", "color", "x", "y", "font"
  ],

  // Subtítulos de la locución (SRT de tools/transcribir.py, revisado)
  "subtitles": {"src": "audio/locucion.srt", "offset": 1.0, "style": "subtitulo"},

  // Motion graphics y efectos superpuestos (docs/efectos.md)
  "overlays": [
    {"template": "dato", "params": {"valor": "240.000", "prefijo": "+", "etiqueta": "kg mensuales"}, "start": 12, "dur": 3},
    {"template": "luz", "params": {"semilla": 3}, "start": 0.2, "dur": 2.5, "opacity": 0.7},
    {"template": "lottie", "params": {"src": "proyectos/acme/motion/logo.json"}, "start": 58},
    {"src": "assets/overlays/polvo.mov", "start": 0, "blend": "screen", "opacity": 0.4}
  ],

  "logo_bug": {"src": "assets/logo_blanco.png", "width": 160, "margin": 60, "opacity": 0.85,
               "start": 5, "end": 120},

  "audio": {
    "vo": {"src": "audio/locucion.wav", "start": 1.0, "gain_db": 0},
    "music": {"src": "audio/musica.wav", "in": 0, "gain_db": -8, "fade_in": 0, "fade_out": 2.5},
    "duck_music_under_vo": true,
    "duck": {"threshold": 0.03, "ratio": 6, "attack": 80, "release": 600},
    "sfx": [{"src": "audio/sfx/whoosh.wav", "at": 7.9, "gain_db": -12}]
  },

  "loudness": {"I": -14, "TP": -1, "LRA": 11},   // broadcast: {"I": -23}
  "encode": {"crf": 16, "preset": "slow", "maxrate": "30M"}
}
```

## Consejos

- **Timing de la locución**: el offset de los subtítulos tiene que ser igual al `start` de la VO.
- **Disolvencias** acortan la timeline (los planos se superponen). Los textos usan tiempo de
  timeline final: renderizá en draft y ajustá mirando la hoja de contacto.
- **Cortar al beat**: medí los beats de la música (`aubio`/a oído) y hacé que las duraciones
  `out - in` sumen hasta cada beat.
- Motion graphics, transiciones de GPU, looks y texturas: **`docs/efectos.md`**.
- Animaciones a medida (infografías complejas, mapas, collage LED): plantilla nueva en
  `tools/motion/templates/` (HTML + GSAP), o After Effects exportado como Lottie.
