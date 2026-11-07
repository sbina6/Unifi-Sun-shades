// Screenshots of the adapter viewer -> adapter/viewer/s_*.png (stitched by export_adapter.py). Run: node cad/adapter_shots.js
const { chromium } = require('playwright');
const OUT = require('path').resolve(__dirname, '../adapter/viewer');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1300, height: 820 }, deviceScaleFactor: 1 });
  const errs = []; p.on('console', m => m.type() === 'error' && errs.push(m.text())); p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + require('path').resolve(__dirname, '../adapter/viewer/index.html')); await p.waitForTimeout(5000);
  const shots = [['front','v4',0,true],['front','flat',0,true],['back','none',0,false],['side','v4',40,true]];
  for (const [v,m,e,w] of shots) { await p.evaluate(a => window.__setView(...a), [v,m,e,w]); await p.waitForTimeout(1200);
    await p.locator('.stage').screenshot({ path: `${OUT}/s_${v}_${m}.png` }); }
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
