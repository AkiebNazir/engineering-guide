import fs from 'fs';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><body></body>', { pretendToBeVisual: true, url: 'http://localhost/', runScripts: 'dangerously' });
const { window } = dom;
window.matchMedia = window.matchMedia || (() => ({ matches: false, addEventListener() {}, addListener() {} }));
window.ResizeObserver = window.ResizeObserver || class { observe() {} unobserve() {} disconnect() {} };
window.requestAnimationFrame = window.requestAnimationFrame || (cb => setTimeout(cb, 16));
// canvas 2d context isn't implemented by jsdom; stub just enough that mount()
// functions (which call c.ctx methods eagerly in some labs) don't throw.
const ctxStub = new Proxy({}, { get: (_, prop) => (prop === 'canvas' ? {} : (() => ctxStub)) });
window.HTMLCanvasElement.prototype.getContext = () => ctxStub;
if (!window.MutationObserver) {
  window.MutationObserver = class { observe() {} disconnect() {} takeRecords() { return []; } };
}
if (!window.IntersectionObserver) {
  window.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} };
}

const files = [
  'static/viz.js', 'static/viz-sd.js', 'static/viz-sd2.js', 'static/viz-sd3.js',
  'static/viz-api.js', 'static/viz-api2.js', 'static/viz-api3.js', 'static/viz-api4.js', 'static/viz-api5.js',
];

let code = '';
for (const f of files) code += fs.readFileSync(f, 'utf8') + '\n;\n';
// jsdom's MutationObserver isn't reachable as a bare global inside window.eval；
// this one line (a live-redraw-on-theme-change hookup, irrelevant to a static
// lab-registration check) is the only thing that needs it.
code = code.replace(/^new MutationObserver\([\s\S]*?attributeFilter:[^;]*;\s*$/m, '');

// LABS is declared with `const` at the top of viz.js, so it's a lexical
// binding inside this eval, not a `window` property — read it out from the
// same eval call via an explicit assignment.
code += `
window.__LAB_CHECK__ = ${JSON.stringify(['api-rest', 'api-graphql', 'api-grpc', 'api-protobuf', 'api-ws', 'api-webhooks', 'api-soap'])}
  .map(id => {
    const spec = LABS.get(id);
    if (!spec) return { id, state: 'missing' };
    if (typeof spec === 'function') return { id, state: 'simple' };
    return { id, state: typeof spec.mount === 'function' ? 'ok' : 'bad', title: spec.title };
  });
`;

// Phase 2: actually mount each lab into a live document and see if mount()
// throws. createLab() catches mount() errors itself and writes a
// `.lab-error` node instead of re-throwing, so we look for that. `createLab`
// is a strict-mode top-level function declaration, so (like `LABS` above)
// it only exists as a lexical binding inside THIS eval — everything has to
// run in the one `window.eval(code)` call below, not a separate one.
code += `
window.__MOUNT_CHECK__ = [];
(async () => {
  for (const id of ${JSON.stringify(['api-rest', 'api-graphql', 'api-grpc', 'api-protobuf', 'api-ws', 'api-webhooks', 'api-soap'])}) {
    const fig = createLab(id);
    document.body.appendChild(fig);
    await new Promise(r => setTimeout(r, 0));
    await new Promise(r => setTimeout(r, 0));
    const err = fig.querySelector('.lab-error');
    window.__MOUNT_CHECK__.push({ id, error: err ? err.textContent : null });
    fig.remove();
  }
  window.__MOUNT_DONE__ = true;
})();
`;

window.eval(code);

let ok = true;
for (const r of window.__LAB_CHECK__) {
  if (r.state === 'missing') { console.log(`MISSING  ${r.id}`); ok = false; }
  else if (r.state === 'simple') { console.log(`SIMPLE   ${r.id} (function-style, not the new canvas lab)`); ok = false; }
  else if (r.state === 'bad') { console.log(`BAD      ${r.id} (no mount())`); ok = false; }
  else console.log(`OK       ${r.id} — title: "${r.title}"`);
}
console.log(ok ? '\nAll 7 lab ids present with object-spec + mount().' : '\nSome ids missing or malformed.');

const start = Date.now();
while (!window.__MOUNT_DONE__ && Date.now() - start < 5000) {
  await new Promise(r => setTimeout(r, 20));
}
console.log('\n--- mount() smoke test ---');
let mountOk = true;
for (const r of window.__MOUNT_CHECK__ || []) {
  if (r.error) { console.log(`FAIL  ${r.id}: ${r.error}`); mountOk = false; }
  else console.log(`OK    ${r.id} mounted without throwing`);
}
if (!window.__MOUNT_DONE__) { console.log('TIMED OUT waiting for mount checks'); mountOk = false; }

process.exit(ok && mountOk ? 0 : 1);
