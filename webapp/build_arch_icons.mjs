// Builds webapp/static/arch-icons.json: the glyph bodies arch-diagram.js
// draws, cut down from two Iconify sets (MDI, Apache-2.0; SVG Logos, CC0) to
// only the icons the diagram syntax names, so the reader never needs a CDN.
//
//   cd webapp && npm i --no-save @iconify-json/mdi @iconify-json/logos
//   node build_arch_icons.mjs
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const A = require('./static/arch-diagram.js');
const packs = { mdi: require('@iconify-json/mdi/icons.json'), logos: require('@iconify-json/logos/icons.json') };

const want = new Set([...Object.values(A.ICONS).map(v => v[0]), ...A.LOGOS.map(n => 'logos:' + n)]);
const out = {};
for (const full of [...want].sort()) {
  const [prefix, name] = full.split(':');
  const p = packs[prefix];
  let icon = p.icons[name], alias = null;
  if (!icon && p.aliases && p.aliases[name]) { alias = p.aliases[name]; icon = p.icons[alias.parent]; }
  if (!icon) { console.error(`missing ${full}`); process.exitCode = 1; continue; }
  const w = icon.width || (alias && alias.width) || p.width || 24, h = icon.height || (alias && alias.height) || p.height || 24;
  // ids inside brand logos (gradients) must be unique per page: prefix them
  let b = icon.body;
  const ids = [...b.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
  for (const id of ids) {
    const nid = `${prefix}-${name}-${id}`;
    b = b.split(`id="${id}"`).join(`id="${nid}"`).split(`url(#${id})`).join(`url(#${nid})`).split(`href="#${id}"`).join(`href="#${nid}"`);
  }
  out[full] = { b, w, h };
}
fs.writeFileSync(new URL('./static/arch-icons.json', import.meta.url), JSON.stringify(out));
console.log(`${Object.keys(out).length} icons, ${(JSON.stringify(out).length / 1024).toFixed(0)} KB`);
