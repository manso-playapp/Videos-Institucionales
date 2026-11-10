#!/usr/bin/env node
/*
 * render.cjs — Renderiza una página HTML animada a video, cuadro por cuadro, con Chromium
 * headless (Playwright). Determinista: cada cuadro es una función del tiempo, nunca del reloj.
 *
 * Contrato de la página (ver tools/motion/templates/*.html):
 *   window.MOTION = {
 *     setup: async (params, {width, height, fps}) => duracionEnSegundos,
 *     seek:  async (t) => {}            // deja la escena en el instante t (segundos)
 *   }
 *
 * Uso:
 *   node tools/motion/render.cjs --page tools/motion/templates/dato.html \
 *        --params '{"valor":"240.000","unidad":"kg mensuales"}' \
 *        --out render/dato.mov --width 1920 --height 1080 --fps 25 [--alpha] [--draft]
 *
 * --alpha  → ProRes 4444 con canal alfa (para superponer sobre video)
 * sin alpha → ProRes 422 HQ (o H.264 si la salida es .mp4)
 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function args() {
  const a = process.argv.slice(2), o = { width: 1920, height: 1080, fps: 25, params: '{}' };
  for (let i = 0; i < a.length; i++) {
    const k = a[i].replace(/^--/, '');
    if (['alpha', 'draft', 'verbose'].includes(k)) o[k] = true;
    else o[k] = a[++i];
  }
  if (!o.page || !o.out) { console.error('Faltan --page y --out'); process.exit(2); }
  o.width = +o.width; o.height = +o.height; o.fps = +o.fps;
  if (o['params-file']) o.params = fs.readFileSync(o['params-file'], 'utf8');
  return o;
}

(async () => {
  const o = args();
  const params = JSON.parse(o.params);
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    '--allow-file-access-from-files', '--disable-web-security', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: o.width, height: o.height }, deviceScaleFactor: 1 });
  page.on('console', m => { if (o.verbose || m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => console.error('[page error]', e.message));
  // Chromium no permite fetch() de file://: la página lee archivos locales a través de Node.
  const { fileURLToPath } = require('url');
  await page.exposeFunction('readText', u => fs.readFileSync(u.startsWith('file:') ? fileURLToPath(u) : u, 'utf8'));
  await page.goto('file://' + path.resolve(o.page));
  await page.waitForFunction(() => window.MOTION && window.MOTION.setup, null, { timeout: 15000 });
  const dur = await page.evaluate(async ([p, env]) => {
    await document.fonts.ready;
    return await window.MOTION.setup(p, env);
  }, [params, { width: o.width, height: o.height, fps: o.fps, alpha: !!o.alpha }]);
  const n = Math.max(1, Math.round(dur * o.fps));

  fs.mkdirSync(path.dirname(path.resolve(o.out)), { recursive: true });
  const isMp4 = /\.mp4$/i.test(o.out);
  const enc = o.alpha
    ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-alpha_bits', '16', '-vendor', 'apl0']
    : isMp4 ? ['-c:v', 'libx264', '-crf', o.draft ? '22' : '14', '-preset', o.draft ? 'veryfast' : 'slow', '-pix_fmt', 'yuv420p']
            : ['-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', '-vendor', 'apl0'];
  const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(o.fps),
    '-c:v', 'png', '-i', '-', ...enc, '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    '-r', String(o.fps), o.out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));

  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(async t => { await window.MOTION.seek(t); }, i / o.fps);
    const buf = await page.screenshot({ type: 'png', omitBackground: !!o.alpha, animations: 'disabled' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 25 === 0) process.stderr.write(`\r  cuadro ${i + 1}/${n}`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  process.stderr.write(`\r  ${n} cuadros en ${((Date.now() - t0) / 1000).toFixed(1)}s → ${o.out}\n`);
})().catch(e => { console.error(e); process.exit(1); });
