/* ============================================================================
   Drive every DSA visualizer through the real player in headless Chromium.

     make app                          # in another terminal (or DSA_PORT=…)
     node webapp/scripts/validate_viz_player.js [http://127.0.0.1:8420]

   Two passes:
     problems  each of the 345 problems' Visualize tab: the exact animation is
               found, builds from its example input, has a non-empty stage and
               steps all the way to its last frame
     specs     every distinct spec registered in ALGOS (pattern animations too)
   Exits non-zero on any build failure, empty stage or console/page error.

   Needs Playwright (npm i -g playwright, or the copy under /opt/node22 in the
   cloud sandbox). CodeMirror/marked load from cdnjs; with no network the app
   degrades and this still runs — the visualizers do not depend on them.
   ========================================================================= */
'use strict';

let chromium;
for (const mod of ['playwright', '/opt/node22/lib/node_modules/playwright']) {
  try { ({ chromium } = require(mod)); break; } catch (e) { /* try the next */ }
}
if (!chromium) { console.error('Playwright not found — npm i -g playwright'); process.exit(2); }

const BASE = process.argv[2] || `http://127.0.0.1:${process.env.DSA_PORT || 8420}`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
  page.on('console', m => {
    if (m.type() === 'error' && !/Failed to load resource|ERR_/.test(m.text())) errors.push(`console: ${m.text().slice(0, 240)}`);
  });
  await page.goto(`${BASE}/#/dsa`);
  await page.waitForFunction(() => typeof DATA !== 'undefined' && DATA.problems && typeof renderAlgoTab === 'function', null, { timeout: 20000 });

  const result = await page.evaluate(() => {
    const host = document.createElement('div');
    host.style.cssText = 'position:fixed;inset:0 auto auto 0;width:900px;height:800px;overflow:auto;z-index:9999;background:#000';
    document.body.append(host);
    const drive = (label, mount) => {
      try {
        mount();
        const root = host.querySelector('.vz');
        if (!root) return `${label}: no player (${host.textContent.trim().slice(0, 80)})`;
        const err = root.querySelector('.vz-err').textContent;
        if (err) return `${label}: build failed — ${err}`;
        const total = +root.querySelector('.vz-count').textContent.split('/')[1];
        const next = root.querySelector('[data-a=next]');
        for (let i = 0; i < total; i++) next.click();
        if (root.dataset.kind !== 'canvas' && !root.querySelector('.vz-dom').children.length) return `${label}: empty stage`;
        if (!root.querySelector('.vz-count').textContent.startsWith(`${total} /`)) return `${label}: did not reach the last step`;
        return null;
      } catch (e) { return `${label}: threw ${e.message}`; }
    };
    const fails = [];
    let problems = 0, specs = 0;
    for (const p of DATA.problems) {
      const f = drive(p.id, () => renderAlgoTab(host, p.topic, p));
      if (f) fails.push(f); else problems++;
    }
    const all = [...new Set(Object.entries(ALGOS).filter(([k]) => k !== '__solution__').flatMap(([, v]) => v))];
    for (const s of all) {
      const f = drive(s.title, () => { ALGOS.__solution__ = [s]; renderAlgoTab(host, '__solution__'); });
      if (f) fails.push(f); else specs++;
    }
    host.remove();
    return { problems, totalProblems: DATA.problems.length, specs, totalSpecs: all.length, fails };
  });

  console.log(`problems: ${result.problems}/${result.totalProblems} play end to end`);
  console.log(`specs:    ${result.specs}/${result.totalSpecs} play end to end`);
  result.fails.forEach(f => console.log(`  FAIL ${f}`));
  [...new Set(errors)].slice(0, 20).forEach(e => console.log(`  ERROR ${e}`));
  await browser.close();
  process.exit(result.fails.length || errors.length ? 1 : 0);
})();
