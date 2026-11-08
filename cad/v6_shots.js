// Screenshots of the v6 shade designer -> v6_viewer/s_<name>.png. Run: node cad/v5_shots.js
const { chromium } = require('playwright');
const path = require('path');
const OUT = path.resolve(__dirname, '../v6_viewer');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1300, height: 820 }, deviceScaleFactor: 1 });
  const errs = []; p.on('console', m => m.type() === 'error' && errs.push(m.text())); p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.join(OUT, 'index.html')); await p.addStyleTag({ content: '.hint{display:none}' }); await p.waitForTimeout(6000);
  const shots = [
    ['front', { pattern: 'khatam', view: 'front', mode: 'all', wall: true }],
    ['side', { view: 'side' }],
    ['close_khatam', { view: 'close' }],
    ['close_hexstar', { pattern: 'hexstar' }],
    ['close_rosette', { pattern: 'rosette' }],
    ['close_octstar', { pattern: 'octstar' }],
    ['mount_front', { pattern: 'khatam', view: 'front', mount: true }],
    ['mount_back', { view: 'back', mount: true, mode: 'none' }],
  ];
  for (const [n, o] of shots) { await p.evaluate(a => window.__set(a), o); await p.waitForTimeout(1500);
    await p.locator('.stage').screenshot({ path: `${OUT}/s_${n}.png` }); }
  await p.screenshot({ path: `${OUT}/s_full.png` });
  console.log('errors', JSON.stringify(errs)); await b.close();
})();
