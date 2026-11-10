/*
 * _base.js — utilidades comunes de las plantillas de motion.
 * Cada plantilla arma una línea de tiempo GSAP en pausa; render.cjs la recorre con seek(t).
 */
(function () {
  const ROOT = new URL('../../../', document.baseURI).href;   // raíz del repo
  window.REPO = ROOT;

  // Fuentes del estudio (assets/fonts). Las de marca del cliente se pasan en params.fonts.
  const FONTS = [
    ['Inter', 300, 'Inter-Light.ttf'], ['Inter', 400, 'Inter-Regular.ttf'],
    ['Inter', 500, 'Inter-Medium.ttf'], ['Inter', 600, 'Inter-SemiBold.ttf'],
    ['Barlow Condensed', 400, 'BarlowCondensed-Regular.ttf'], ['Barlow Condensed', 500, 'BarlowCondensed-Medium.ttf'],
    ['Barlow Condensed', 600, 'BarlowCondensed-SemiBold.ttf'], ['Barlow Condensed', 700, 'BarlowCondensed-Bold.ttf'],
  ];
  window.loadFonts = async function (extra = []) {
    const all = FONTS.map(([f, w, file]) => [f, w, ROOT + 'assets/fonts/' + file]).concat(
      extra.map(e => [e.family, e.weight || 400, new URL(e.src, ROOT).href]));
    await Promise.all(all.map(async ([family, weight, url]) => {
      const ff = new FontFace(family, `url(${url})`, { weight: String(weight) });
      document.fonts.add(await ff.load());
    }));
  };

  window.loadScript = src => new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = ROOT + src; s.onload = res; s.onerror = () => rej(new Error('No cargó ' + src));
    document.head.appendChild(s);
  });

  // Escala: las plantillas se diseñan a 1080 de alto; se adaptan a cualquier lienzo (ej. LED 2048x640).
  window.setupStage = function (env) {
    const k = env.height / 1080;
    document.documentElement.style.setProperty('--k', k);
    document.documentElement.style.setProperty('--w', env.width + 'px');
    document.documentElement.style.setProperty('--h', env.height + 'px');
    document.body.style.width = env.width + 'px';
    document.body.style.height = env.height + 'px';
    if (!env.alpha) document.body.style.background = document.body.dataset.bg || '#000';
    return k;
  };

  // Registro estándar: setup construye `tl` (gsap.timeline en pausa) y devuelve duración.
  window.defineMotion = function (build) {
    window.MOTION = {
      async setup(params, env) {
        await loadScript('assets/js/gsap.min.js');
        await loadScript('assets/js/CustomEase.min.js');
        await loadScript('assets/js/SplitText.min.js');
        gsap.registerPlugin(CustomEase, SplitText);
        // Curvas de la casa: salida suave y "premium", sin rebotes.
        CustomEase.create('casa', '0.22, 1, 0.36, 1');          // easeOutQuint-ish
        CustomEase.create('casaInOut', '0.65, 0, 0.35, 1');
        await loadFonts(params.fonts || []);
        const k = setupStage(env);
        gsap.ticker.lagSmoothing(0);
        const tl = gsap.timeline({ paused: true });
        const dur = await build(tl, params, env, k);
        window.__tl = tl;
        return dur ?? tl.duration();
      },
      async seek(t) { window.__tl.seek(t, false); }
    };
  };
})();
