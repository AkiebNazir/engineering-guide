// Runs every Query Lab question's reference solution against its dataset, in the same
// engines the browser uses (PGlite, mingo, qlab-redis.js), and fails on any error, empty
// result, or a solution that doesn't pass its own checker.
//
//   node webapp/scripts/validate_query_labs.mjs            # all labs
//   node webapp/scripts/validate_query_labs.mjs sql -v     # one lab, print each result's first row
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
const engines = only.length ? only : ['sql', 'mongodb', 'redis'];

// The question banks and datasets come from the server's own parser.
const api = (route, params) => JSON.parse(execFileSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(path.join(here, '..'))})
import server
from urllib.parse import parse_qs
r = server.api_get(${JSON.stringify(route)}, parse_qs(${JSON.stringify(new URLSearchParams(params).toString())}))
print(json.dumps(r[0] if r else None))`], { maxBuffer: 1 << 28 }).toString());

let failures = 0, total = 0;
const fail = (q, msg) => { failures++; console.log(`FAIL  ${q.id}: ${msg}`); };
const show = (q, t) => {
  if (!verbose) return;
  const first = t.rows[0] ? t.rows[0].map(v => Core.normValue(v)).join(' | ') : '(none)';
  console.log(`  ok  ${q.id.padEnd(34)} ${String(t.rows.length).padStart(5)} rows   ${first.slice(0, 110)}`);
};

async function validateSql() {
  const lab = api('/api/query-lab', { engine: 'sql' });
  const { PGlite } = await import(pathToFileURL(path.join(STATIC, 'vendor/pglite/0.5.8/index.js')).href);
  const db = await PGlite.create();
  for (const d of lab.datasets) {
    const data = api('/api/query-lab-data', { engine: 'sql', dataset: d.id });
    for (const text of Object.values(data.files)) await db.exec(text);
  }
  const run = async (q, sql) => {
    await db.exec('BEGIN');
    try {
      await db.exec(`SET LOCAL search_path TO ${q.dataset}, public`);
      let res = Core.sqlLastResult(await db.exec(sql));
      if (q.verify) res = Core.sqlLastResult(await db.exec(q.verify));
      return res;
    } finally {
      await db.exec('ROLLBACK');
    }
  };
  for (const q of lab.questions) {
    total++;
    try {
      const t = await run(q, q.solution);
      if (!t.columns.length) { fail(q, 'solution returned no result set'); continue; }
      if (!t.rows.length) { fail(q, 'solution returned 0 rows'); continue; }
      const again = await run(q, q.solution);
      const c = Core.compareResults(t, again, q.order === 'strict');
      if (!c.ok) { fail(q, `not deterministic: ${c.reason}`); continue; }
      show(q, t);
    } catch (e) { fail(q, e.message); }
  }
  console.log(`sql: ${lab.questions.length} questions over ${lab.datasets.map(d => d.id).join(', ')}`);
}

async function validateMongo() {
  const lab = api('/api/query-lab', { engine: 'mongodb' });
  if (!lab) return console.log('mongodb: no question bank yet');
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(STATIC, 'vendor/mingo/7.2.4/mingo.min.js'), 'utf8') + ';this.mingo=mingo;', ctx);
  const files = api('/api/query-lab-data', { engine: 'mongodb', dataset: 'shop' }).files;
  // Build the shell inside the vm context so Dates and Arrays share mingo's realm.
  ctx.__core = fs.readFileSync(path.join(STATIC, 'qlab-core.js'), 'utf8');
  vm.runInContext('var module = { exports: {} }; eval(__core); var Core = module.exports;', ctx);
  ctx.__files = files;
  vm.runInContext(`var base = {}; for (const [n, t] of Object.entries(__files)) base[n.replace(/\\.json$/, '')] = Core.reviveEjson(JSON.parse(t));`, ctx);
  for (const q of lab.questions) {
    total++;
    ctx.__q = q;
    try {
      const out = vm.runInContext(`(() => {
        const s = Core.createMongoShell(mingo, base);
        let r = s.run(__q.solution);
        if (__q.verify) r = s.run(__q.verify);
        const s2 = Core.createMongoShell(mingo, base);
        let r2 = s2.run(__q.solution);
        if (__q.verify) r2 = s2.run(__q.verify);
        const c = Core.compareMongo(r, r2, __q.order === 'strict');
        return { table: Core.mongoToTable(r), det: c, n: Array.isArray(r) ? r.length : 1, json: JSON.stringify(r).slice(0, 110) };
      })()`, ctx);
      if (Array.isArray(out.table.rows) && out.n === 0) { fail(q, 'solution returned no documents'); continue; }
      if (!out.det.ok) { fail(q, `not deterministic: ${out.det.reason}`); continue; }
      if (verbose) console.log(`  ok  ${q.id.padEnd(34)} ${String(out.n).padStart(5)} docs   ${out.json}`);
    } catch (e) { fail(q, e.message); }
  }
  console.log(`mongodb: ${lab.questions.length} questions`);
}

function validateRedis() {
  const lab = api('/api/query-lab', { engine: 'redis' });
  if (!lab) return console.log('redis: no question bank yet');
  const seed = Object.values(api('/api/query-lab-data', { engine: 'redis', dataset: 'seed' }).files)[0];
  const fresh = () => { const r = new Redis.MiniRedis({ now: () => Date.UTC(2025, 9, 5, 10, 15) }); r.load(seed); return r; };
  for (const q of lab.questions) {
    total++;
    try {
      const r = fresh();
      const results = Redis.runScript(r, q.solution);
      const bad = results.find(x => !x.ok && !/expect-error/.test(q.tags.join(' ')));
      if (bad) { fail(q, `"${bad.cmd}" -> ${bad.reply.message}`); continue; }
      let reply = Core.redisLastReply(results);
      if (q.verify) reply = Core.redisLastReply(Redis.runScript(r, q.verify));
      if (reply === null && !q.tags.includes('nil')) { fail(q, 'last reply is (nil)'); continue; }
      if (verbose) console.log(`  ok  ${q.id.padEnd(34)} ${Redis.format(reply).replace(/\n/g, ' ').slice(0, 110)}`);
    } catch (e) { fail(q, e.message); }
  }
  console.log(`redis: ${lab.questions.length} questions`);
}

for (const e of engines) {
  if (e === 'sql') await validateSql();
  else if (e === 'mongodb') await validateMongo();
  else if (e === 'redis') validateRedis();
}
console.log(failures ? `\n${failures} of ${total} solutions FAILED` : `\nAll ${total} solutions ran and returned results.`);
process.exit(failures ? 1 : 0);
