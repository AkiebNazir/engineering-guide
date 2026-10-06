// Runs every code block that gets a ▶ Run button in the SQL and NoSQL chapters, page by
// page and in order, in the same engines and the same per-page sessions the browser uses
// (PGlite, mingo over the shop collections, qlab-redis.js over the lab seed). Fails on any
// block that errors, unless the block says it is meant to (a comment containing "ERROR:"
// or "expect an error"), so a learner never presses Run on a broken example.
//
//   node webapp/scripts/validate_doc_runs.mjs            # all chapters
//   node webapp/scripts/validate_doc_runs.mjs -v         # also print each block's result
//   node webapp/scripts/validate_doc_runs.mjs redis/04   # only pages whose id contains this
//
// Needs no npm packages (the engines are vendored under static/vendor/).
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { execFileSync } from 'child_process';
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const STATIC = path.join(here, '..', 'static');
const require = createRequire(import.meta.url);
const Core = require(path.join(STATIC, 'qlab-core.js'));
const Redis = require(path.join(STATIC, 'qlab-redis.js'));

const args = process.argv.slice(2);
const verbose = args.includes('-v');
const only = args.filter(a => !a.startsWith('-'));

// Every chapter, as the app serves it, plus the lab data the sessions start from.
const dump = JSON.parse(execFileSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(path.join(here, '..'))})
import server
from urllib.parse import parse_qs
get = lambda route, q='': server.api_get(route, parse_qs(q))[0]
pages = []
for mod in ('sql', 'nosql'):
    for it in get('/api/' + mod)['items']:
        pages.append({'mod': mod, 'id': it['id'], 'markdown': get('/api/%s-doc' % mod, 'id=' + it['id'])['markdown']})
print(json.dumps({
    'pages': pages,
    'mongo': get('/api/query-lab-data', 'engine=mongodb&dataset=shop')['files'],
    'redis': list(get('/api/query-lab-data', 'engine=redis&dataset=seed')['files'].values())[0],
}))`], { maxBuffer: 1 << 28 }).toString());

// Fenced blocks the way marked sees them: an opening fence, its info string's first word
// as the language, the body dedented by the fence's own indent.
function codeBlocks(md) {
  const out = [];
  const lines = md.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^(\s*)(`{3,}|~{3,})\s*([^\s`]*)/);
    if (!m) continue;
    const [, indent, fence, lang] = m;
    const body = [];
    let j = i + 1;
    for (; j < lines.length; j++) {
      const t = lines[j].trimStart();
      if (t.startsWith(fence) && !t.slice(fence.length).trim()) break;
      body.push(lines[j].startsWith(indent) ? lines[j].slice(indent.length) : lines[j].trimStart());
    }
    out.push({ lang, text: body.join('\n'), line: i + 1 });
    i = j;
  }
  return out;
}
const meantToFail = text => /ERROR:|expect an error/i.test(text);

// Engines, shared across pages the way the browser shares one PGlite.
const { PGlite } = await import(pathToFileURL(path.join(STATIC, 'vendor/pglite/0.5.8/index.js')).href);
const pg = await PGlite.create();
const ctx = {}; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(STATIC, 'vendor/mingo/7.2.4/mingo.min.js'), 'utf8') + ';this.mingo=mingo;', ctx);
ctx.__core = fs.readFileSync(path.join(STATIC, 'qlab-core.js'), 'utf8');
vm.runInContext('var module = { exports: {} }; eval(__core); var Core = module.exports;', ctx);
ctx.__files = dump.mongo;
vm.runInContext(`var base = {}; for (const [n, t] of Object.entries(__files)) base[n.replace(/\\.json$/, '')] = Core.reviveEjson(JSON.parse(t));`, ctx);

function summary(engine, res) {
  if (engine === 'sql') return res.columns.length ? `${res.rows.length} rows  ${res.rows[0] ? res.rows[0].map(v => Core.normValue(v)).join(' | ') : ''}` : 'ran';
  if (engine === 'mongodb') return JSON.stringify(res).slice(0, 140);
  return res.map(x => Redis.format(x.reply).replace(/\n/g, ' ')).join(' ; ');
}

let total = 0, failures = 0, pagesWithRuns = 0;
const perEngine = { sql: 0, mongodb: 0, redis: 0 };
for (const page of dump.pages) {
  const key = `${page.mod}:${page.id}`;
  if (only.length && !only.some(o => page.id.includes(o))) continue;
  const blocks = codeBlocks(page.markdown)
    .map(b => ({ ...b, engine: Core.docEngine(page.mod, page.id, b.lang, b.text, Redis.COMMANDS) }))
    .filter(b => b.engine);
  if (!blocks.length) continue;
  pagesWithRuns++;
  const schema = 'doc_' + key.replace(/[^a-z0-9]+/gi, '_').toLowerCase().slice(0, 50);
  await pg.exec(`DROP SCHEMA IF EXISTS ${schema} CASCADE; CREATE SCHEMA ${schema};`);
  vm.runInContext('var shell = Core.createMongoShell(mingo, base);', ctx);
  const redis = new Redis.MiniRedis();
  redis.load(dump.redis);
  if (verbose) console.log(`\n${key}`);
  for (const b of blocks) {
    total++; perEngine[b.engine]++;
    const src = Core.docRunnable(b.engine, b.text);
    const where = `${key}:${b.line} (${b.engine})`;
    let err = null, res = null;
    try {
      if (b.engine === 'sql') {
        await pg.exec(`SET search_path TO ${schema}, public`);
        try { res = Core.sqlLastResult(await pg.exec(src)); }
        finally { if (pg.isInTransaction()) await pg.exec('ROLLBACK'); }   // as qlab.js sqlCloseTxn
      } else if (b.engine === 'mongodb') {
        ctx.__src = src;
        res = vm.runInContext('shell.run(__src)', ctx);
      } else {
        res = Redis.runScript(redis, src);
        const bad = res.find(x => !x.ok);
        if (bad) err = `${bad.cmd} -> ${bad.reply.message}`;
      }
    } catch (e) { err = e.message; }
    if (err && !meantToFail(b.text)) { failures++; console.log(`FAIL  ${where}: ${err.split('\n')[0]}`); continue; }
    if (verbose) console.log(`  ${err ? 'err' : 'ok '} L${String(b.line).padEnd(5)} ${err ? `(meant to fail) ${err.split('\n')[0]}` : summary(b.engine, res)}`.slice(0, 200));
  }
}
console.log(`${total} runnable blocks on ${pagesWithRuns} pages (sql ${perEngine.sql}, mongodb ${perEngine.mongodb}, redis ${perEngine.redis})`);
console.log(failures ? `${failures} FAILED` : 'All ran.');
process.exit(failures ? 1 : 0);
