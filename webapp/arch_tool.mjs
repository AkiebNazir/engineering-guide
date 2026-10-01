// Checks and previews ```arch diagram blocks (see ARCH_DIAGRAMS.md).
//
//   node webapp/arch_tool.mjs check [file.md|dir ...]     parse + lint every block (default: whole repo)
//   node webapp/arch_tool.mjs shot  file.md [n] [--dark] [--out DIR]
//                                                       render block n (1-based; default all) to PNG
//
// `check` fails on syntax errors and on lines that pass through a box; it
// prints crossings and bends so a conversion can be judged without a browser.
// `shot` needs Playwright + Chromium (preinstalled in the cloud sandbox).
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
const A = require('./static/arch-diagram.js');
const icons = JSON.parse(fs.readFileSync(path.join(here, 'static/arch-icons.json'), 'utf8'));
const repo = path.resolve(here, '..');

const blocksOf = text => {
  const out = [], re = /^```arch[ \t]*\n([\s\S]*?)^```/gm;
  let m;
  while ((m = re.exec(text))) out.push({ src: m[1], line: text.slice(0, m.index).split('\n').length });
  return out;
};
const mdFiles = dir => {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (['node_modules', '.git', '_archive'].includes(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...mdFiles(p));
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
};

const [cmd, ...args] = process.argv.slice(2);
if (cmd === 'check') {
  const targets = args.length ? args.flatMap(a => fs.statSync(a).isDirectory() ? mdFiles(path.resolve(a)) : [path.resolve(a)]) : mdFiles(repo);
  let total = 0, bad = 0, warn = 0;
  for (const f of targets) {
    const blocks = blocksOf(fs.readFileSync(f, 'utf8'));
    blocks.forEach((b, i) => {
      total++;
      const where = `${path.relative(process.cwd(), f)}:${b.line} (block ${i + 1})`;
      try {
        const r = A.lint(b.src);
        const wide = r.width > 900;
        const flag = r.through.length ? 'FAIL' : r.crossings > 2 || wide ? 'WARN' : 'OK  ';
        if (r.through.length) bad++; else if (r.crossings > 2 || wide) warn++;
        console.log(`${flag} ${where}  nodes=${r.nodes} edges=${r.edges} crossings=${r.crossings} bends=${r.bends} size=${r.width}x${r.height}${wide ? '  (wider than 900px: the reader column is ~640px; aim for <= 760px)' : ''}`);
        r.through.forEach(t => console.log(`       ${t}`));
      } catch (e) {
        bad++;
        console.log(`FAIL ${where}  ${e.message}${e.line ? `  (file line ${b.line + e.line})` : ''}`);
      }
    });
  }
  console.log(`\n${total} arch blocks, ${bad} failing, ${warn} with warnings (>2 crossings or >900px wide).`);
  process.exit(bad ? 1 : 0);
} else if (cmd === 'shot') {
  const file = path.resolve(args[0]);
  const dark = args.includes('--dark');
  const oi = args.indexOf('--out');
  const outDir = oi >= 0 ? path.resolve(args[oi + 1]) : process.cwd();
  const pick = args[1] && /^\d+$/.test(args[1]) ? +args[1] : 0;
  const blocks = blocksOf(fs.readFileSync(file, 'utf8'));
  let pw;
  try { pw = require('playwright'); } catch { pw = require('/opt/node22/lib/node_modules/playwright'); }
  const browser = await pw.chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 1.5 });
  fs.mkdirSync(outDir, { recursive: true });
  for (let i = 0; i < blocks.length; i++) {
    if (pick && pick !== i + 1) continue;
    let html;
    try {
      const { svg, caption } = A.render(blocks[i].src, { dark, icons, idPrefix: `s${i}` });
      html = `<!doctype html><meta charset=utf-8><body style="margin:0;padding:16px;background:${dark ? '#11151d' : '#ffffff'};display:inline-block">${svg}`
        + (caption ? `<p style="font:italic 14px Georgia,serif;color:${dark ? '#9ba6b9' : '#4c5566'};max-width:60ch;margin:10px auto 0;text-align:center">${caption.replace(/</g, '&lt;')}</p>` : '') + '</body>';
    } catch (e) { console.log(`block ${i + 1}: ${e.message}`); continue; }
    await page.setContent(html);
    const out = path.join(outDir, `${path.basename(file, '.md')}-arch${i + 1}${dark ? '-dark' : ''}.png`);
    await (await page.$('body')).screenshot({ path: out });
    console.log(out);
  }
  await browser.close();
} else {
  console.log('usage: node webapp/arch_tool.mjs check [paths...] | shot file.md [n] [--dark] [--out DIR]');
  process.exit(2);
}
