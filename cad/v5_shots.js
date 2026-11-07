// Screenshots of the v5 viewer -> v5_viewer/s_<variant>_<view>.png. Run: node cad/adapter_shots.js
const { chromium } = require('playwright');
const OUT = require('path').resolve(__dirname, '../v5_viewer');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1300, height: 820 }, deviceScaleFactor: 1 });
  const errs = []; p.on('console', m => m.type() === 'error' && errs.push(m.text())); p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + require('path').resolve(__dirname, '../v5_viewer/index.html')); await p.waitForTimeout(5000);
  const shots = [['front','all',0,true,'a'],['front','all',0,true,'b'],['side','all',0,true,'a'],['side','all',0,true,'b'],['back','none',0,false,'a'],['back','none',0,false,'b']];
  for (const [v,m,e,w,x] of shots) { await p.evaluate(a => window.__setView(...a), [v,m,e,w,x]); await p.waitForTimeout(1200);
    await p.locator('.stage').screenshot({ path: `${OUT}/s_${x}_${v}.png` }); }
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
