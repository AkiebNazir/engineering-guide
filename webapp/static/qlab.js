/* ============================================================================
   Query Lab — run SQL, MongoDB and Redis in the browser against realistic
   datasets, with an interview question bank that checks your answer.

     #/query-lab/<engine>              playground (engine: sql | mongodb | redis)
     #/query-lab/<engine>/<question>   one question

   Engines run client-side, so the lab works the same with the local server and
   on a static host:
     sql      PGlite (PostgreSQL compiled to WebAssembly) in a Web Worker,
              qlab-sql-worker.js + vendor/pglite/
     mongodb  mingo (MongoDB query language) behind a mongosh-style `db`, qlab-core.js
     redis    MiniRedis, qlab-redis.js

   Question banks and datasets come from /api/query-lab and /api/query-lab-data
   (SQL/lab/, NoSQL/lab/). Progress and drafts are saved per question as
   state.problems["qlab/<engine>/<id>"], like the other practice areas.

   Also: Run buttons on SQL / mongosh / redis-cli code blocks in the SQL and
   NoSQL chapters (qlabEnhanceDoc, called from reader.js).

   Reads app.js globals: DATA, $, $$, esc, api, patch, showView, leaveWorkspace,
   renderSidebar, renderMarkdown, emptyMsg, toast, STATUS_GLYPH, curModule.
   ========================================================================= */
'use strict';

const QLAB_ENGINES = {
  sql: {
    label: 'SQL', engineName: 'PostgreSQL', module: 'sql', cmMode: 'text/x-pgsql', lang: 'sql',
    blurb: 'A real PostgreSQL engine runs in your browser. Pick a dataset and query its tables by name.',
    starter: '-- Any SQL works: SELECT, joins, CTEs, window functions, even CREATE TABLE.\n-- Ctrl/Cmd + Enter runs the editor (or just the selected text).\nSELECT order_id, status, total_amount, ordered_at\nFROM orders\nORDER BY ordered_at DESC\nLIMIT 10;\n',
  },
  mongodb: {
    label: 'MongoDB', engineName: 'mongosh', module: 'nosql', cmMode: 'javascript', lang: 'js',
    blurb: 'mongosh syntax over the shop collections: customers, products, orders, reviews. The last expression is the result.',
    starter: '// db.<collection>.find(filter, projection), .aggregate([...]), countDocuments, distinct, insert/update/delete…\n// Ctrl/Cmd + Enter runs. Writes stay until you press Reset data.\ndb.orders.find({ status: "delivered" }, { total: 1, "customer.name": 1 })\n  .sort({ ordered_at: -1 })\n  .limit(5)\n',
  },
  redis: {
    label: 'Redis', engineName: 'redis-cli', module: 'nosql', cmMode: null, lang: 'redis',
    blurb: 'One redis-cli command per line. Keys for caches, leaderboards, sessions, carts, bitmaps, geo and streams are loaded.',
    starter: '# One command per line, exactly as in redis-cli. Ctrl/Cmd + Enter runs.\nZREVRANGE leaderboard:2025-W40 0 4 WITHSCORES\nHGETALL product:105\nTTL product:101\n',
  },
};
const QLAB_LEVELS = ['Easy', 'Medium', 'Hard'];
/* Shortcut labels in the platform's own words: ⌘ on a Mac, Ctrl elsewhere. */
const QLAB_MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || '');
const QLAB_MODK = QLAB_MAC ? '⌘' : 'Ctrl';
const QLAB_SHIFT = QLAB_MAC ? '⇧' : 'Shift';
const QLAB_ENTER = QLAB_MAC ? '↵' : 'Enter';
const qlabKeys = (...keys) => keys.map(k => `<kbd>${k}</kbd>`).join('');

let qlabEngine = null;          // engine on screen
let qlabQid = null;             // question on screen, or null for the playground
let qlabEditor = null;          // CodeMirror instance (or a <textarea> fallback)
let qlabDataset = { sql: 'shop', mongodb: 'shop', redis: 'seed' };
let qlabFilter = { level: 'all', q: '' };
let qlabSide = 'questions';
let qlabHints = 0;              // hints revealed for the open question
let qlabSaveTimer = 0;
let qlabBusy = false;
const qlabBanks = {};           // engine -> /api/query-lab payload (promise)
const qlabBanksSync = {};       // engine -> its questions, once loaded

const qlabBank = engine => (qlabBanks[engine] ||= api(`/api/query-lab?engine=${engine}`).catch(e => { delete qlabBanks[engine]; throw e; }));
const qlabRecId = (engine, qid) => `qlab/${engine}/${qid || 'playground'}`;
const qlabRec = id => (DATA.state.problems[id] ||= { status: 'todo', drafts: {} });
const qlabStatus = (engine, qid) => (DATA.state.problems[qlabRecId(engine, qid)] || {}).status || 'todo';

/* ============================================================= engines == */
const QE = {
  // sql: worker = the SqlWorkerDb starting or running, db = the same once PGlite is up,
  // loaded = dataset -> promise of its load into this worker
  sql: { worker: null, db: null, ready: null, loaded: new Map(), scratchPages: new Set() },
  mongodb: { base: null, ready: null, shell: null },
  redis: { seed: null, ready: null, live: null },
};

function qlabScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.onload = resolve; s.onerror = () => reject(new Error(`Could not load ${src}`));
    document.head.appendChild(s);
  });
}

/* One PGlite connection serves the lab and every chapter, so a run must never leave a
   transaction open behind it: a BEGIN without COMMIT (or one aborted by an error) would
   make every later statement fail with "current transaction is aborted". */
const sqlStripTxn = code => code.replace(
  /(^|;)(\s*)(?:BEGIN|START\s+TRANSACTION|COMMIT|END|ROLLBACK|ABORT)(?:\s+(?:WORK|TRANSACTION))?(?:\s+ISOLATION\s+LEVEL\s+[A-Z ]+?)?\s*(?=;|$)/gi, '$1$2');
async function sqlCloseTxn(db) {
  if (!(await db.isInTransaction())) return '';
  await db.exec('ROLLBACK');
  return 'The run left a transaction open, so it was rolled back. End it with COMMIT in the same run to keep its changes.';
}

/* --- SQL: PGlite in a Web Worker (qlab-sql-worker.js) --------------------
   PGlite ignores statement_timeout, and a statement can't be cancelled from
   outside, so a runaway query (say a recursive CTE with no stop condition) is
   stopped by terminating the worker. Learners' SQL runs with { limit: true }:
   past SQL_TIME_LIMIT_MS, or on the Stop button, sqlStop() throws the worker
   away and starts a fresh one; callers reload their dataset with sqlLoad(). */
const SQL_TIME_LIMIT_MS = 10000;

class SqlWorkerDb {
  constructor() {
    this.worker = new Worker(new URL('./qlab-sql-worker.js', document.baseURI), { type: 'module' });
    this.pending = new Map();
    this.seq = 0;
    this.dead = null;
    this.ready = new Promise((resolve, reject) => { this.boot = { resolve, reject }; });
    this.ready.catch(() => {});
    this.chain = this.ready.catch(() => {});
    this.worker.onmessage = ({ data: m }) => {
      if ('ready' in m) { m.ready ? this.boot.resolve(this) : this.kill(sqlError(m.error)); return; }
      const p = this.pending.get(m.id);
      if (!p) return;
      this.pending.delete(m.id);
      m.ok ? p.resolve(m.result) : p.reject(sqlError(m.error));
    };
    this.worker.onerror = e => {
      e.preventDefault();
      this.kill(new Error(`PostgreSQL did not start: ${e.message || 'its worker failed to load'}`));
    };
  }
  // One request at a time, so a time limit measures that request and nothing queued before it.
  call(msg, limit) {
    const run = this.chain.then(() => new Promise((resolve, reject) => {
      if (this.dead) { reject(this.dead); return; }
      const id = ++this.seq;
      const timer = limit ? setTimeout(() => sqlStop('timeout', this), SQL_TIME_LIMIT_MS) : 0;
      this.pending.set(id, {
        resolve: v => { clearTimeout(timer); resolve(v); },
        reject: e => { clearTimeout(timer); reject(e); },
      });
      this.worker.postMessage({ id, ...msg });
    }));
    this.chain = run.catch(() => {});
    return run;
  }
  exec(sql, { limit = false } = {}) { return this.call({ op: 'exec', sql }, limit); }
  query(sql, params = [], { limit = false } = {}) { return this.call({ op: 'query', sql, params }, limit); }
  isInTransaction() { return this.call({ op: 'inTxn' }); }   // async here, unlike PGlite's own
  kill(err) {
    if (this.dead) return;
    this.dead = err;
    this.worker.terminate();
    this.boot.reject(err);
    for (const p of this.pending.values()) p.reject(err);
    this.pending.clear();
  }
}

// Errors come back from the worker as plain objects (message, position, code, …).
function sqlError(o) {
  return Object.assign(new Error(o && o.message ? o.message : 'PostgreSQL error'), o || {});
}

async function sqlDb() {
  if (!QE.sql.ready) {
    const w = QE.sql.worker = new SqlWorkerDb();
    const p = QE.sql.ready = w.ready.then(db => { if (QE.sql.worker === w) QE.sql.db = db; return db; });
    p.catch(() => {
      if (QE.sql.ready !== p) return;
      QE.sql.ready = QE.sql.worker = QE.sql.db = null;
      QE.sql.loaded.clear();
    });
  }
  return QE.sql.ready;
}
async function sqlLoad(dataset) {
  const db = await sqlDb();
  if (dataset === 'scratch') return db;
  let p = QE.sql.loaded.get(dataset);
  if (!p) {
    p = (async () => {
      const d = await api(`/api/query-lab-data?engine=sql&dataset=${encodeURIComponent(dataset)}`);
      for (const text of Object.values(d.files)) await db.exec(text);
    })();
    QE.sql.loaded.set(dataset, p);
    p.catch(() => { if (QE.sql.loaded.get(dataset) === p) QE.sql.loaded.delete(dataset); });
  }
  await p;
  return db;
}

// Stop whatever SQL is running: terminate the worker (every pending call rejects with
// an error that has .stopped set) and boot a fresh one. reason: 'timeout' | 'user'.
function sqlStop(reason, w = QE.sql.worker) {
  if (!w || w.dead) return;
  const err = new Error(reason === 'timeout'
    ? `Query stopped after ${SQL_TIME_LIMIT_MS / 1000} s, the database was restarted.`
    : 'Query stopped, the database was restarted.');
  err.stopped = true;
  if (QE.sql.worker === w) {
    QE.sql.ready = QE.sql.worker = QE.sql.db = null;
    QE.sql.loaded.clear();
    // chapter pages' scratch schemas died with it: their next Run sets them up again
    for (const [key, sess] of QLAB_DOC_SESSIONS) {
      if (sess.schema) { QLAB_DOC_SESSIONS.delete(key); QLAB_DOC_RAN.delete(key); }
    }
  }
  w.kill(err);
  sqlDb().catch(() => {});
}
const sqlPath = ds => (ds === 'scratch' ? 'public' : `${ds}, public`);

async function mongoBase() {
  QE.mongodb.ready ??= (async () => {
    if (typeof mingo === 'undefined') await qlabScript('./vendor/mingo/7.2.4/mingo.min.js');
    const d = await api('/api/query-lab-data?engine=mongodb&dataset=shop');
    const base = {};
    for (const [name, text] of Object.entries(d.files)) base[name.replace(/\.json$/, '')] = QLabCore.reviveEjson(JSON.parse(text));
    QE.mongodb.base = base;
    QE.mongodb.shell = QLabCore.createMongoShell(mingo, base);
    return base;
  })().catch(e => { QE.mongodb.ready = null; throw e; });
  return QE.mongodb.ready;
}

async function redisSeed() {
  QE.redis.ready ??= (async () => {
    const d = await api('/api/query-lab-data?engine=redis&dataset=seed');
    QE.redis.seed = Object.values(d.files)[0] || '';
    QE.redis.live = qlabFreshRedis();
    return QE.redis.seed;
  })().catch(e => { QE.redis.ready = null; throw e; });
  return QE.redis.ready;
}
function qlabFreshRedis() {
  const r = new QLabRedis.MiniRedis();
  r.load(QE.redis.seed || '');
  return r;
}

const qlabEnsure = engine => (engine === 'sql' ? sqlLoad(qlabDataset.sql) : engine === 'mongodb' ? mongoBase() : redisSeed());

/* --- run: playground semantics (changes persist until Reset data) ------- */
async function qlabRunPlayground(engine, code) {
  const t0 = performance.now();
  if (engine === 'sql') {
    const db = await sqlLoad(qlabDataset.sql);
    await db.exec(`SET search_path TO ${sqlPath(qlabDataset.sql)}`);
    try {
      const res = await db.exec(code, { limit: true });
      return { kind: 'table', ms: performance.now() - t0, statements: res.length, ...QLabCore.sqlLastResult(res), note: await sqlCloseTxn(db) };
    } finally {
      await sqlCloseTxn(db);
    }
  }
  if (engine === 'mongodb') {
    await mongoBase();
    const out = QE.mongodb.shell.run(code);
    return { kind: 'mongo', ms: performance.now() - t0, value: out };
  }
  await redisSeed();
  const results = QLabRedis.runScript(QE.redis.live, code);
  return { kind: 'redis', ms: performance.now() - t0, results };
}

/* --- run in isolation, for checking answers ------------------------------ */
async function qlabRunIsolated(engine, q, code) {
  if (engine === 'sql') {
    const db = await sqlLoad(q.dataset);
    await sqlCloseTxn(db);
    await db.exec('BEGIN');
    try {
      await db.exec(`SET LOCAL search_path TO ${sqlPath(q.dataset)}`);
      // The check already runs inside a transaction it rolls back; an answer's own
      // BEGIN/COMMIT would end that early and make its changes permanent.
      let r = QLabCore.sqlLastResult(await db.exec(sqlStripTxn(code), { limit: true }));
      if (q.verify) r = QLabCore.sqlLastResult(await db.exec(q.verify, { limit: true }));
      return r;
    } finally {
      await db.exec('ROLLBACK').catch(() => {});
    }
  }
  if (engine === 'mongodb') {
    await mongoBase();
    const shell = QLabCore.createMongoShell(mingo, QE.mongodb.base);
    let out = shell.run(code);
    if (q.verify) out = shell.run(q.verify);
    return out;
  }
  await redisSeed();
  const r = qlabFreshRedis();
  const results = QLabRedis.runScript(r, code);
  const failed = results.find(x => !x.ok);
  if (failed && !q.tags.includes('expect-error')) throw new Error(`${failed.cmd}: ${failed.reply.message}`);
  if (!results.length) throw new Error('Type at least one command.');
  let reply = QLabCore.redisLastReply(results);
  if (q.verify) reply = QLabCore.redisLastReply(QLabRedis.runScript(r, q.verify));
  return reply;
}

function qlabCompare(engine, q, expected, actual) {
  if (engine === 'sql') {
    if (!actual.columns.length) return { ok: false, reason: 'Your SQL ran but returned no result set. End with a SELECT.' };
    return QLabCore.compareResults(expected, actual, q.order === 'strict');
  }
  if (engine === 'mongodb') return QLabCore.compareMongo(expected, actual, q.order === 'strict');
  const a = QLabRedis.format(expected), b = QLabRedis.format(actual);
  return a === b ? { ok: true } : { ok: false, reason: 'Your last command\'s reply differs from the expected reply.' };
}

/* ========================================================= rendering == */
async function renderQueryLab(engine, qid) {
  const host = $('#viewQueryLab');
  if (!QLAB_ENGINES[engine]) engine = 'sql';
  const sameShell = qlabEngine === engine && host.querySelector('.qlab');
  qlabEngine = engine;
  qlabQid = qid || null;
  qlabHints = 0;
  if (!sameShell) {
    host.innerHTML = `<div class="mod-loading">Loading the ${QLAB_ENGINES[engine].label} lab…</div>`;
  }
  let bank;
  try { bank = await qlabBank(engine); } catch (e) {
    host.innerHTML = emptyMsg('Query Lab unavailable', `The question bank did not load (${esc(e.message)}).`);
    return;
  }
  if (qlabEngine !== engine || host.hidden) return;
  qlabBanksSync[engine] = bank.questions;
  const q = qid ? bank.questions.find(x => x.id === qid) : null;
  if (qid && !q) { location.replace(`#/query-lab/${engine}`); return; }
  if (q) qlabDataset[engine] = q.dataset;

  if (!sameShell) host.innerHTML = qlabShell(engine, bank);
  qlabPaintHead(engine, bank);
  qlabPaintSide(engine, bank);
  qlabPaintQuestion(engine, q);
  qlabMountEditor(engine, q);
  qlabPaintOutput(null);
  qlabWire(host, engine, bank);
  // warm the engine up in the background so the first Run is quick
  qlabSetEngineState('loading');
  qlabEnsure(engine).then(() => { if (qlabEngine === engine) { qlabSetEngineState('ready'); if (qlabSide === 'schema') qlabPaintSchema(engine); } })
    .catch(e => qlabSetEngineState('error', e.message));
}

function qlabShell(engine, bank) {
  const E = QLAB_ENGINES[engine];
  return `
    <div class="qlab" data-engine="${engine}">
      <header class="qlab-head">
        <div class="qlab-head-main">
          <div class="crumb"><a href="#/${E.module === 'sql' ? 'sql' : 'nosql'}">${E.module === 'sql' ? 'SQL' : 'NoSQL'}</a><span>›</span><span>Query Lab</span></div>
          <div class="qlab-title-row">
            <h1 class="qlab-title">Query Lab <span class="qlab-title-engine">${esc(E.label)}</span></h1>
            <span class="qlab-progress" id="qlabProgress"></span>
          </div>
          <p class="qlab-sub" id="qlabSub"></p>
        </div>
        <nav class="lang-switch qlab-engines" aria-label="Database">
          ${Object.entries(QLAB_ENGINES).map(([k, e]) => `<a class="lang${k === engine ? ' is-on' : ''}" href="#/query-lab/${k}"${k === engine ? ' aria-current="page"' : ''}>${e.label}</a>`).join('')}
        </nav>
      </header>
      <div class="qlab-body">
        <aside class="qlab-side">
          <div class="tabs qlab-side-tabs" role="tablist">
            <button class="tab${qlabSide === 'questions' ? ' is-on' : ''}" data-side="questions" role="tab">Questions</button>
            <button class="tab${qlabSide === 'schema' ? ' is-on' : ''}" data-side="schema" role="tab">${engine === 'redis' ? 'Keys' : engine === 'mongodb' ? 'Collections' : 'Schema'}</button>
          </div>
          <div class="qlab-side-body" id="qlabSideBody"></div>
        </aside>
        <section class="qlab-main">
          <article class="qlab-q" id="qlabQ"></article>
          <div class="qlab-editor-wrap">
            <div class="editor-bar qlab-bar">
              <label class="qlab-ds"${engine !== 'sql' ? ' hidden' : ''}>
                <span>Dataset</span>
                <select id="qlabDs">
                  ${bank.datasets.map(d => `<option value="${esc(d.id)}">${esc(d.id)}</option>`).join('')}
                  <option value="scratch">scratch (empty)</option>
                </select>
              </label>
              <span class="qlab-engine-state" id="qlabState" aria-live="polite"></span>
              <div class="editor-actions">
                <button class="btn btn-ghost" id="qlabReset" title="Reload the dataset, undoing your changes">Reset data</button>
                <button class="btn btn-ghost qlab-check" id="qlabCheck" hidden title="Check your answer against the reference (Shift + ${QLAB_MODK} + Enter)">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>Check answer</button>
                <button class="btn btn-ghost qlab-stop" id="qlabStop" hidden title="Stop the running query (restarts the database)">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor"/></svg>Stop</button>
                <button class="btn btn-primary" id="qlabRun" title="Run the editor, or just the selected text (${QLAB_MODK} + Enter)">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z" fill="currentColor"/></svg>Run<span class="qlab-kbd" aria-hidden="true">${QLAB_MAC ? '⌘↵' : 'Ctrl+Enter'}</span></button>
              </div>
            </div>
            <div class="qlab-editor" id="qlabEditor"></div>
          </div>
          <div class="qlab-out" id="qlabOut" aria-live="polite"></div>
          <div class="qlab-solution" id="qlabSolution" hidden></div>
        </section>
      </div>
    </div>`;
}

function qlabPaintHead(engine, bank) {
  const done = bank.questions.filter(q => qlabStatus(engine, q.id) === 'solved').length;
  const E = QLAB_ENGINES[engine];
  $('#qlabSub').textContent = E.blurb;
  $('#qlabProgress').innerHTML = `<b>${done}</b> / ${bank.questions.length} solved`;
  $('#qlabProgress').classList.toggle('has-done', done > 0);
  const ds = $('#qlabDs');
  if (ds) {
    ds.value = qlabDataset.sql;
    ds.disabled = !!qlabQid;
    ds.title = qlabQid ? 'This question uses its own dataset' : 'Which dataset the editor queries';
  }
}

function qlabSetEngineState(state, msg) {
  const el = $('#qlabState');
  if (!el) return;
  const E = QLAB_ENGINES[qlabEngine];
  el.dataset.state = state;
  el.textContent = state === 'loading' ? `Starting ${E.engineName}…` : state === 'running' ? 'Running…'
    : state === 'ready' ? `${E.engineName} ready` : `Engine failed: ${msg || ''}`;
}

/* ---------------------------------------------------------- side rail -- */
function qlabPaintSide(engine, bank) {
  $$('.qlab-side-tabs .tab').forEach(t => {
    t.classList.toggle('is-on', t.dataset.side === qlabSide);
    t.setAttribute('aria-selected', String(t.dataset.side === qlabSide));
  });
  if (qlabSide === 'schema') { qlabPaintSchema(engine); return; }
  const f = qlabFilter, term = f.q.trim().toLowerCase();
  const pass = q => (f.level === 'all' || q.level === f.level)
    && (!term || `${q.title} ${q.tags.join(' ')} ${q.section}`.toLowerCase().includes(term));
  const sections = [];
  for (const q of bank.questions) {
    if (!pass(q)) continue;
    let s = sections.find(x => x.name === q.section);
    if (!s) sections.push(s = { name: q.section, items: [] });
    s.items.push(q);
  }
  $('#qlabSideBody').innerHTML = `
    <div class="qlab-filter">
      <input type="search" id="qlabSearch" placeholder="Filter questions or tags" value="${esc(f.q)}" aria-label="Filter questions">
      <div class="filter-row">
        ${['all', ...QLAB_LEVELS].map(l => `<button class="chip${f.level === l ? ' is-on' : ''}" data-level="${l}">${l === 'all' ? 'All' : l}</button>`).join('')}
      </div>
    </div>
    <a class="qlab-play${qlabQid ? '' : ' is-on'}" href="#/query-lab/${engine}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4zM8 9l3 3-3 3M13 15h3"/></svg>Free playground</a>
    ${sections.length ? sections.map(s => `
      <section class="qlab-sec">
        <h3>${esc(s.name)}</h3>
        <ol>${s.items.map(q => {
          const st = qlabStatus(engine, q.id);
          return `<li><a class="qlab-item st-${st}${q.id === qlabQid ? ' is-on' : ''}" href="#/query-lab/${engine}/${q.id}">
            <span class="qlab-item-glyph" aria-label="${st}">${STATUS_GLYPH[st] || STATUS_GLYPH.todo}</span>
            <span class="qlab-item-title">${esc(q.title)}</span>
            <span class="qlab-lvl" data-l="${esc(q.level)}">${esc(q.level[0])}</span></a></li>`;
        }).join('')}</ol>
      </section>`).join('') : '<p class="qlab-none">No questions match.</p>'}`;
  // keep the open question visible, scrolling only the list (scrollIntoView would also move the page)
  const list = $('#qlabSideBody'), on = $('.qlab-item.is-on', list);
  if (on && (on.offsetTop < list.scrollTop || on.offsetTop > list.scrollTop + list.clientHeight - 40)) {
    list.scrollTop = on.offsetTop - list.clientHeight / 2;
  }
}

async function qlabPaintSchema(engine) {
  const body = $('#qlabSideBody');
  if (!body || qlabSide !== 'schema') return;
  body.innerHTML = '<p class="qlab-none">Loading…</p>';
  try {
    if (engine === 'sql') {
      const ds = qlabQid ? (await qlabBank('sql')).questions.find(q => q.id === qlabQid).dataset : qlabDataset.sql;
      const db = await sqlLoad(ds);
      const schema = ds === 'scratch' ? 'public' : ds;
      const r = await db.query(`
        SELECT c.table_name, c.column_name, c.data_type, c.is_nullable,
               (SELECT count(*) FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage k USING (constraint_schema, constraint_name)
                 WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = c.table_schema
                   AND tc.table_name = c.table_name AND k.column_name = c.column_name) > 0 AS pk
        FROM information_schema.columns c
        WHERE c.table_schema = $1
        ORDER BY c.table_name, c.ordinal_position`, [schema]);
      const tables = {};
      r.rows.forEach(x => (tables[x.table_name] ||= []).push(x));
      const counts = {};
      for (const t of Object.keys(tables)) {
        counts[t] = (await db.query(`SELECT count(*)::int AS n FROM "${schema}"."${t}"`)).rows[0].n;
      }
      body.innerHTML = Object.keys(tables).length ? `<p class="qlab-schema-note">Schema <code>${esc(schema)}</code>. Click a table to insert its name.</p>` +
        Object.entries(tables).map(([t, cols]) => `
          <details class="qlab-tbl" open>
            <summary><button class="qlab-ins" data-ins="${esc(t)}">${esc(t)}</button><span>${counts[t].toLocaleString()} rows</span></summary>
            <ul>${cols.map(c => `<li><button class="qlab-ins" data-ins="${esc(c.column_name)}">${esc(c.column_name)}</button>
              <span class="qlab-type">${esc(c.data_type.replace('timestamp with time zone', 'timestamptz').replace('character varying', 'varchar'))}${c.pk ? ' · PK' : ''}${c.is_nullable === 'YES' ? '' : ''}</span></li>`).join('')}</ul>
          </details>`).join('')
        : '<p class="qlab-none">No tables yet. In the scratch dataset, CREATE TABLE something.</p>';
    } else if (engine === 'mongodb') {
      await mongoBase();
      const shell = QE.mongodb.shell;
      body.innerHTML = `<p class="qlab-schema-note">Fields of each collection's first document. Click to insert.</p>` +
        shell.collectionNames().map(n => {
          const docs = shell.db[n].find().limit(1).toArray();
          const keys = docs[0] ? qlabDocPaths(docs[0]) : [];
          return `<details class="qlab-tbl" open><summary><button class="qlab-ins" data-ins="db.${esc(n)}">${esc(n)}</button>
            <span>${shell.db[n].estimatedDocumentCount().toLocaleString()} docs</span></summary>
            <ul>${keys.map(([k, t]) => `<li><button class="qlab-ins" data-ins="${esc(k)}">${esc(k)}</button><span class="qlab-type">${esc(t)}</span></li>`).join('')}</ul></details>`;
        }).join('');
    } else {
      await redisSeed();
      const keys = QE.redis.live.keys();
      const fams = {};
      keys.forEach(k => { const fam = k.key.includes(':') ? k.key.split(':')[0] + ':*' : k.key; (fams[fam] ||= []).push(k); });
      body.innerHTML = `<p class="qlab-schema-note">${keys.length} keys. Click a key to insert it.</p>` +
        Object.entries(fams).map(([fam, ks]) => `
          <details class="qlab-tbl"${ks.length < 8 ? ' open' : ''}><summary><span class="qlab-fam">${esc(fam)}</span><span>${ks.length} · ${esc(ks[0].type)}</span></summary>
            <ul>${ks.slice(0, 60).map(k => `<li><button class="qlab-ins" data-ins="${esc(k.key)}">${esc(k.key)}</button>
              <span class="qlab-type">${esc(k.type)}${k.ttl >= 0 ? ` · ttl ${k.ttl}s` : ''}</span></li>`).join('')}
            ${ks.length > 60 ? `<li class="qlab-more">… ${ks.length - 60} more</li>` : ''}</ul></details>`).join('');
    }
  } catch (e) {
    body.innerHTML = `<p class="qlab-none">Could not read the schema: ${esc(e.message)}</p>`;
  }
}

function qlabDocPaths(doc, prefix = '', out = []) {
  for (const [k, v] of Object.entries(doc)) {
    const p = prefix ? `${prefix}.${k}` : k;
    if (v instanceof Date) out.push([p, 'date']);
    else if (Array.isArray(v)) {
      out.push([p, v.length && typeof v[0] === 'object' ? 'array of documents' : 'array']);
      if (v.length && v[0] && typeof v[0] === 'object' && !Array.isArray(v[0])) qlabDocPaths(v[0], p, out);
    } else if (v && typeof v === 'object') qlabDocPaths(v, p, out);
    else out.push([p, v === null ? 'null' : typeof v]);
  }
  return out;
}

/* ------------------------------------------------------- question card -- */
function qlabPaintQuestion(engine, q) {
  const host = $('#qlabQ');
  const E = QLAB_ENGINES[engine];
  $('#qlabCheck').hidden = !q;
  const sol = $('#qlabSolution');
  sol.hidden = true; sol.innerHTML = '';
  if (!q) {
    host.innerHTML = `
      <div class="qlab-q-head"><h2>Free playground</h2></div>
      <div class="qlab-prose">${renderMarkdown(qlabPlaygroundHelp(engine))}</div>`;
    return;
  }
  const r = DATA.state.problems[qlabRecId(engine, q.id)] || {};
  host.innerHTML = `
    <div class="qlab-q-head">
      <h2>${esc(q.title)}</h2>
      <div class="qlab-q-meta">
        <span class="pill qlab-lvl-pill" data-l="${esc(q.level)}">${esc(q.level)}</span>
        ${engine === 'sql' ? `<span class="pill">dataset: <b>${esc(q.dataset)}</b></span>` : ''}
        ${engine === 'redis' ? '' : `<span class="pill">${q.order === 'strict' ? (engine === 'sql' ? 'row order matters' : 'order matters') : (engine === 'sql' ? 'any row order' : 'any order')}</span>`}
        ${r.status === 'solved' ? '<span class="pill qlab-solved">✓ solved</span>' : ''}
      </div>
      <div class="qlab-tags">${q.tags.map(t => `<span class="qlab-tag">${esc(t)}</span>`).join('')}</div>
    </div>
    <div class="qlab-prose">${renderMarkdown(q.prompt)}</div>
    <div class="qlab-hints" id="qlabHints"></div>
    <div class="qlab-q-actions">
      ${q.hints.length ? `<button class="btn btn-ghost" id="qlabHintBtn">Show a hint</button>` : ''}
      <button class="btn btn-ghost" id="qlabSolBtn">Reveal solution</button>
      ${qlabNavLinks(engine, q)}
    </div>`;
  qlabPaintHints(q);
}

function qlabPlaygroundHelp(engine) {
  if (engine === 'sql') {
    return 'Query any of the datasets: **shop** (an online store: customers, products, orders, order_items, payments, reviews), ' +
      '**hr** (a company: departments, employees, salary_history, projects, job_applications) or **analytics** (a SaaS app: users, events, ' +
      'subscriptions, experiment_assignments), or **scratch** to create your own tables. The *Schema* tab lists every table and column.\n\n' +
      'Changes you make (INSERT, UPDATE, CREATE) stay until **Reset data**. Pick a question from the list to have your answer checked.';
  }
  if (engine === 'mongodb') {
    return 'The shop data as documents: `customers`, `products`, `orders` (with embedded `items`, a `customer` snapshot and `status_history`) and `reviews`. ' +
      'Write mongosh code: `db.orders.find(...)`, `.aggregate([...])`, `countDocuments`, `distinct`, `insertOne`, `updateMany`… ' +
      'The value of the last expression is shown. Writes stay until **Reset data**.';
  }
  return 'A Redis loaded with real-world key families: `product:*` cache hashes, `leaderboard:*` sorted sets, `session:*` keys with TTLs, ' +
    '`cart:*`, `following:*` sets, `dau:*` bitmaps, `uniques:*` HyperLogLogs, `stores` (geo) and `stream:orders`. The *Keys* tab browses them. ' +
    'Type one command per line; each reply prints like redis-cli.';
}

function qlabNavLinks(engine, q) {
  const qs = qlabBanksSync[engine];
  if (!qs) return '';
  const i = qs.findIndex(x => x.id === q.id);
  const prev = qs[i - 1], next = qs[i + 1];
  return `<span class="qlab-nav">
    ${prev ? `<a class="btn btn-ghost" href="#/query-lab/${engine}/${prev.id}" title="${esc(prev.title)}">← Previous</a>` : ''}
    ${next ? `<a class="btn btn-ghost" href="#/query-lab/${engine}/${next.id}" title="${esc(next.title)}">Next →</a>` : ''}</span>`;
}
function qlabPaintHints(q) {
  const box = $('#qlabHints');
  if (!box) return;
  box.innerHTML = q.hints.slice(0, qlabHints).map((h, i) => `<div class="qlab-hint"><b>Hint ${i + 1}</b>${renderMarkdown(h)}</div>`).join('');
  const b = $('#qlabHintBtn');
  if (b) {
    b.hidden = qlabHints >= q.hints.length;
    b.textContent = qlabHints ? `Another hint (${qlabHints + 1} of ${q.hints.length})` : `Show a hint (${q.hints.length})`;
  }
}

function qlabShowSolution(engine, q) {
  const box = $('#qlabSolution');
  box.hidden = false;
  box.innerHTML = `
    <div class="qlab-sol-head"><h3>Solution</h3><button class="btn btn-ghost" id="qlabLoadSol">Load into editor</button></div>
    <div class="code"><div class="code-head"><span class="code-lang">${esc(QLAB_ENGINES[engine].label)}</span></div>
      <pre><code class="language-${engine === 'sql' ? 'sql' : engine === 'mongodb' ? 'javascript' : 'plaintext'}">${esc(q.solution)}</code></pre></div>
    ${q.explanation ? `<div class="qlab-prose">${renderMarkdown(q.explanation)}</div>` : ''}`;
  if (typeof highlightCode === 'function' && typeof ensureHljs === 'function') {
    ensureHljs().then(ok => ok && highlightCode($('code', box), engine === 'sql' ? 'sql' : 'javascript'));
  }
  const id = qlabRecId(engine, q.id);
  if (!qlabRec(id).revealed) { qlabRec(id).revealed = true; patch(id, { revealed: true }); }
  $('#qlabSolBtn').hidden = true;
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* -------------------------------------------------------------- editor -- */
function qlabMountEditor(engine, q) {
  const host = $('#qlabEditor');
  const E = QLAB_ENGINES[engine];
  const id = qlabRecId(engine, q && q.id);
  const saved = (DATA.state.problems[id] || {}).drafts?.[E.lang];
  const initial = saved ?? (q ? qlabBlankFor(engine, q) : E.starter);
  host.innerHTML = '';
  if (typeof CodeMirror === 'undefined') {
    const ta = document.createElement('textarea');
    ta.className = 'qlab-ta'; ta.value = initial; ta.spellcheck = false;
    host.append(ta);
    qlabEditor = { getValue: () => ta.value, setValue: v => { ta.value = v; }, getSelection: () => ta.value.slice(ta.selectionStart, ta.selectionEnd), focus: () => ta.focus(), refresh() {}, replaceSelection: t => ta.setRangeText(t, ta.selectionStart, ta.selectionEnd, 'end') };
    ta.addEventListener('input', () => qlabSaveDraft());
    ta.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); qlabRun(); } });
    return;
  }
  qlabEditor = CodeMirror(host, {
    value: initial, theme: 'studio', mode: E.cmMode || 'text/plain', lineNumbers: true,
    indentUnit: 2, tabSize: 2, indentWithTabs: false, autoCloseBrackets: true, styleActiveLine: true,
    matchBrackets: true, lineWrapping: false,
    extraKeys: {
      'Cmd-Enter': () => qlabRun(), 'Ctrl-Enter': () => qlabRun(),
      'Shift-Cmd-Enter': () => qlabCheck(), 'Shift-Ctrl-Enter': () => qlabCheck(),
      'Cmd-/': cm => cm.toggleComment(), 'Ctrl-/': cm => cm.toggleComment(),
      Tab: cm => (cm.somethingSelected() ? cm.indentSelection('add') : cm.replaceSelection('  ')),
    },
  });
  qlabEditor.on('change', () => qlabSaveDraft());
  setTimeout(() => qlabEditor.refresh(), 0);
}
const qlabBlankFor = (engine, q) => (engine === 'sql' ? `-- ${q.title}\n-- dataset: ${q.dataset}\n\n`
  : engine === 'mongodb' ? `// ${q.title}\n\n` : `# ${q.title}\n`);

function qlabSaveDraft() {
  clearTimeout(qlabSaveTimer);
  const engine = qlabEngine, qid = qlabQid, code = qlabEditor.getValue();
  qlabSaveTimer = setTimeout(() => {
    const id = qlabRecId(engine, qid), r = qlabRec(id), lang = QLAB_ENGINES[engine].lang;
    r.drafts = { ...(r.drafts || {}), [lang]: code };
    if (qid && r.status === 'todo') r.status = 'attempting';
    patch(id, { drafts: r.drafts, status: r.status });
  }, 600);
}

/* -------------------------------------------------------------- output -- */
function qlabPaintOutput(out, verdict) {
  const host = $('#qlabOut');
  if (!host) return;
  if (!out && !verdict) {
    host.innerHTML = `<div class="qlab-out-empty">
      <p><b>Run</b> ${qlabKeys(QLAB_MODK, QLAB_ENTER)} executes the editor, or only the text you have selected. Results appear here.</p>
      ${qlabQid ? `<p><b>Check answer</b> ${qlabKeys(QLAB_SHIFT, QLAB_MODK, QLAB_ENTER)} compares your result with the reference solution. Anything your answer changes is thrown away afterwards.</p>` : ''}
    </div>`;
    return;
  }
  host.innerHTML = (verdict ? qlabVerdictHtml(verdict) : '') + (out ? qlabResultHtml(out) : '');
}

function qlabVerdictHtml(v) {
  if (v.error) return `<div class="qlab-verdict is-err"><b>${v.stopped ? 'Stopped' : 'Your query failed'}</b><pre>${esc(v.error)}</pre></div>`;
  if (v.ok) return `<div class="qlab-verdict is-ok"><b>✓ Correct.</b> Your result matches the reference answer.${v.firstSolve ? ' Marked as solved.' : ''}</div>`;
  let preview = '';
  if (v.expected) {
    preview = `<details class="qlab-expected"><summary>Show the expected result</summary>${qlabResultHtml(v.expected, true)}</details>`;
  }
  return `<div class="qlab-verdict is-no"><b>Not yet.</b> ${esc(v.reason)}${preview}</div>`;
}

function qlabCell(v) {
  if (v === null || v === undefined) return '<span class="qlab-null">NULL</span>';
  if (v instanceof Date) return esc(QLabCore.normValue(v));
  if (typeof v === 'object') return `<span class="qlab-json">${esc(JSON.stringify(v))}</span>`;
  if (typeof v === 'boolean') return `<span class="qlab-bool">${v}</span>`;
  return esc(String(v));
}

function qlabTable(columns, rows, limit = 500) {
  const shown = rows.slice(0, limit);
  return `<div class="qlab-grid"><table>
    <thead><tr><th class="qlab-rn">#</th>${columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
    <tbody>${shown.map((r, i) => `<tr><td class="qlab-rn">${i + 1}</td>${r.map(v => `<td>${qlabCell(v)}</td>`).join('')}</tr>`).join('')}</tbody>
  </table></div>${rows.length > limit ? `<p class="qlab-trunc">Showing ${limit} of ${rows.length.toLocaleString()} rows.</p>` : ''}`;
}

// mongosh-style JSON: dates as ISODate("..."), ids as ObjectId("...")
function qlabJson(v) {
  const json = JSON.stringify(v, (k, x) => (x && typeof x === 'object' && x.$oid ? `ObjectId("${x.$oid}")` : x), 2) ?? 'undefined';
  return esc(json.replace(/"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)"/g, 'ISODate("$1")').replace(/"(ObjectId\(\\"[0-9a-f]+\\"\))"/g, (m, x) => x.replace(/\\"/g, '"')));
}

function qlabResultHtml(out, compact = false) {
  const ms = out.ms != null ? `<span>${out.ms < 1 ? '<1' : Math.round(out.ms)} ms</span>` : '';
  if (out.kind === 'table' || (out.columns && !out.kind)) {
    if (out.note) return `<p class="qlab-trunc">${esc(out.note)}</p>` + qlabResultHtml({ ...out, note: '' }, compact);
    if (!out.columns.length) {
      return `<div class="qlab-meta"><span>${out.statements > 1 ? `${out.statements} statements ran` : 'Statement ran'}</span>
        ${out.affected != null ? `<span>${out.affected} row${out.affected === 1 ? '' : 's'} affected</span>` : ''}${ms}</div>`;
    }
    return `${compact ? '' : `<div class="qlab-meta"><span>${out.rows.length.toLocaleString()} row${out.rows.length === 1 ? '' : 's'}</span>${ms}</div>`}
      ${qlabTable(out.columns, out.rows, compact ? 20 : 500)}`;
  }
  if (out.kind === 'mongo' || out.kind === 'mongo-expected') {
    const v = out.value;
    const n = Array.isArray(v) ? `${v.length.toLocaleString()} document${v.length === 1 ? '' : 's'}` : typeof v === 'number' ? 'number' : Array.isArray(v) ? 'array' : typeof v;
    const list = Array.isArray(v) && v.length > 200 ? v.slice(0, 200) : v;
    return `${compact ? '' : `<div class="qlab-meta"><span>${n}</span>${ms}</div>`}
      <pre class="qlab-json-out">${qlabJson(list)}</pre>${Array.isArray(v) && v.length > 200 ? `<p class="qlab-trunc">Showing 200 of ${v.length.toLocaleString()} documents.</p>` : ''}`;
  }
  if (out.kind === 'redis') {
    return `${compact ? '' : `<div class="qlab-meta"><span>${out.results.length} command${out.results.length === 1 ? '' : 's'}</span>${ms}</div>`}
      <div class="qlab-cli">${out.results.map(x => `<div class="qlab-cli-cmd">redis&gt; ${esc(x.cmd)}</div>
        <pre class="qlab-cli-reply${x.ok ? '' : ' is-err'}">${esc(QLabRedis.format(x.reply))}</pre>`).join('')}</div>`;
  }
  if (out.kind === 'redis-reply') return `<pre class="qlab-cli-reply">${esc(QLabRedis.format(out.reply))}</pre>`;
  return '';
}

/* ------------------------------------------------------------- actions -- */
function qlabCode() {
  const sel = qlabEditor.getSelection && qlabEditor.getSelection();
  return (sel && sel.trim()) ? sel : qlabEditor.getValue();
}
// stoppable: an SQL run of the learner's code, so offer Stop (sqlStop) while it lasts
async function qlabWithBusy(btn, fn, stoppable = false) {
  if (qlabBusy) return;
  qlabBusy = true;
  btn && btn.classList.add('busy');
  const stop = stoppable && $('#qlabStop');
  if (stop) stop.hidden = false;
  try { await fn(); } finally {
    qlabBusy = false;
    btn && btn.classList.remove('busy');
    if (stop) stop.hidden = true;
  }
}

// After sqlStop: the fresh worker has no data, so load the dataset on screen again.
function qlabRewarmSql() {
  if (qlabEngine !== 'sql') return;
  qlabSetEngineState('loading');
  sqlLoad(qlabDataset.sql).then(() => {
    if (qlabEngine !== 'sql') return;
    qlabSetEngineState('ready');
    if (qlabSide === 'schema') qlabPaintSchema('sql');
  }).catch(e => { if (qlabEngine === 'sql') qlabSetEngineState('error', e.message); });
}
const QLAB_STOP_NOTE = '\nPGlite cannot cancel a running statement, so its engine was restarted and the dataset reloaded: changes you made to the data are gone.';

function qlabRun() {
  const engine = qlabEngine;
  return qlabWithBusy($('#qlabRun'), async () => {
    const code = qlabCode();
    if (!code.trim()) return;
    qlabSetEngineState('running');
    try {
      const out = await qlabRunPlayground(engine, code);
      qlabSetEngineState('ready');
      if (qlabEngine === engine) qlabPaintOutput(out);
      if (qlabSide === 'schema' && engine !== 'mongodb') qlabPaintSchema(engine);
    } catch (e) {
      qlabSetEngineState('ready');
      qlabPaintOutput(null, { error: qlabErrorText(e), stopped: e.stopped });
      if (e.stopped) qlabRewarmSql();
    }
  }, engine === 'sql');
}

function qlabErrorText(e) {
  let msg = e && e.message ? e.message : String(e);
  if (e && e.stopped) return msg + QLAB_STOP_NOTE;
  if (e && e.position && qlabEditor.getValue) {
    const upto = qlabEditor.getValue().slice(0, Number(e.position) - 1).split('\n');
    msg += `\n(at line ${upto.length}, column ${upto[upto.length - 1].length + 1})`;
  }
  if (/^\s*\\/m.test(qlabEditor.getValue ? qlabEditor.getValue() : '')) msg += '\nNote: psql meta-commands like \\d are not SQL; use the Schema tab instead.';
  return msg;
}

async function qlabCheck() {
  const engine = qlabEngine, bank = await qlabBank(engine);
  const q = bank.questions.find(x => x.id === qlabQid);
  if (!q) return;
  return qlabWithBusy($('#qlabCheck'), async () => {
    const code = qlabEditor.getValue();
    if (!code.replace(/^\s*(--|#|\/\/).*$/gm, '').trim()) { toast('Write your answer in the editor first.'); return; }
    qlabSetEngineState('running');
    let actual, expected;
    try {
      actual = await qlabRunIsolated(engine, q, code);
    } catch (e) {
      qlabSetEngineState('ready');
      qlabPaintOutput(null, { error: qlabErrorText(e), stopped: e.stopped });
      if (e.stopped) qlabRewarmSql();
      return;
    }
    try { expected = await qlabRunIsolated(engine, q, q.solution); } catch (e) {
      qlabSetEngineState('ready');
      qlabPaintOutput(null, { error: e.stopped ? qlabErrorText(e) : `The reference solution failed in this browser: ${e.message}`, stopped: e.stopped });
      if (e.stopped) qlabRewarmSql();
      return;
    }
    qlabSetEngineState('ready');
    const verdict = qlabCompare(engine, q, expected, actual);
    const id = qlabRecId(engine, q.id), r = qlabRec(id);
    r.attempts = (r.attempts || 0) + 1;
    if (verdict.ok && r.status !== 'solved') {
      r.status = 'solved'; r.solvedAt = new Date().toISOString(); verdict.firstSolve = true;
    }
    patch(id, { status: r.status, attempts: r.attempts, ...(r.solvedAt ? { solvedAt: r.solvedAt } : {}) });
    const wrap = v => (engine === 'sql' ? { kind: 'table', ...v } : engine === 'mongodb' ? { kind: 'mongo', value: v } : { kind: 'redis-reply', reply: v });
    if (!verdict.ok) verdict.expected = wrap(expected);
    qlabPaintOutput(wrap(actual), verdict);
    if (verdict.firstSolve) {
      qlabPaintSide(engine, bank);
      qlabPaintHead(engine, bank);
      const meta = $('.qlab-q-meta');
      if (meta && !$('.qlab-solved', meta)) meta.insertAdjacentHTML('beforeend', '<span class="pill qlab-solved">✓ solved</span>');
    }
  }, engine === 'sql');
}

async function qlabReset() {
  const engine = qlabEngine;
  return qlabWithBusy($('#qlabReset'), async () => {
    if (engine === 'sql') {
      const db = await sqlDb();
      const ds = qlabQid ? (await qlabBank('sql')).questions.find(q => q.id === qlabQid).dataset : qlabDataset.sql;
      if (ds === 'scratch') await db.exec('DROP SCHEMA public CASCADE; CREATE SCHEMA public;');
      else { QE.sql.loaded.delete(ds); await sqlLoad(ds); }
    } else if (engine === 'mongodb') {
      await mongoBase(); QE.mongodb.shell.reset();
    } else {
      await redisSeed(); QE.redis.live = qlabFreshRedis();
    }
    toast('Data reset to the original dataset.', 'ok');
    if (qlabSide === 'schema') qlabPaintSchema(engine);
  });
}

/* --------------------------------------------------------------- wiring -- */
function qlabWire(host, engine, bank) {
  const q = qlabQid ? bank.questions.find(x => x.id === qlabQid) : null;
  host.onclick = e => {
    const t = e.target;
    if (t.closest('#qlabRun')) qlabRun();
    else if (t.closest('#qlabCheck')) qlabCheck();
    else if (t.closest('#qlabStop')) sqlStop('user');
    else if (t.closest('#qlabReset')) qlabReset();
    else if (t.closest('#qlabHintBtn') && q) { qlabHints++; qlabPaintHints(q); }
    else if (t.closest('#qlabSolBtn') && q) qlabShowSolution(engine, q);
    else if (t.closest('#qlabLoadSol') && q) { qlabEditor.setValue(q.solution + '\n'); qlabEditor.focus(); }
    else if (t.closest('.qlab-side-tabs .tab')) { qlabSide = t.closest('.tab').dataset.side; qlabPaintSide(engine, bank); }
    else if (t.closest('[data-level]')) { qlabFilter.level = t.closest('[data-level]').dataset.level; qlabPaintSide(engine, bank); }
    else if (t.closest('.qlab-ins')) {
      e.preventDefault();
      qlabEditor.replaceSelection(t.closest('.qlab-ins').dataset.ins);
      qlabEditor.focus();
    }
  };
  host.oninput = e => {
    if (e.target.id === 'qlabSearch') {
      qlabFilter.q = e.target.value;
      const pos = e.target.selectionStart;
      qlabPaintSide(engine, bank);
      const s = $('#qlabSearch'); s.focus(); s.setSelectionRange(pos, pos);
    }
  };
  host.onchange = e => {
    if (e.target.id === 'qlabDs') {
      qlabDataset.sql = e.target.value;
      qlabSetEngineState('loading');
      sqlLoad(qlabDataset.sql).then(() => { qlabSetEngineState('ready'); if (qlabSide === 'schema') qlabPaintSchema('sql'); })
        .catch(err => qlabSetEngineState('error', err.message));
    }
  };
}

/* ============================================ module landing-page strip == */
function qlabStrip(mod) {
  const cards = mod === 'sql'
    ? [['sql', 'SQL Query Lab', 'PostgreSQL in your browser · shop, HR and analytics datasets · 61 interview questions checked automatically']]
    : [['mongodb', 'MongoDB Query Lab', 'mongosh syntax on the shop collections · find, aggregation pipeline, updates · 34 questions'],
       ['redis', 'Redis Query Lab', 'redis-cli commands on caches, leaderboards, sessions, bitmaps, geo and streams · 36 questions']];
  return `
    <section class="aps qlab-strip">
      <header class="aps-head">
        <h2>Practice: Query Lab</h2>
        <p>Run real queries against realistic data, right here: no database to install. Work through the questions
           interviewers ask most, check your answer, and see the reference solution explained.</p>
      </header>
      <div class="aps-grid">
        ${cards.map(([k, name, sub]) => `
          <a class="aps-card qlab-card" href="#/query-lab/${k}">
            <span class="qlab-card-ic" aria-hidden="true"><svg viewBox="0 0 24 24">${QLAB_ICON}</svg></span>
            <span class="qlab-card-body">
              <span class="aps-card-name">${name}</span>
              <span class="aps-card-counts"><span>${sub}</span></span>
            </span>
            <span class="qlab-card-go">Open the lab <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span>
          </a>`).join('')}
      </div>
    </section>`;
}

/* ============================= Run buttons on chapter code blocks == *
   SQL chapters: every ```sql block. MongoDB chapters: ```js blocks that use
   `db.` (over the shop collections). Redis chapters: ```redis / ```bash blocks
   made only of Redis commands (over the lab's seed keys).
   Each chapter page gets its own scratch session, so nothing leaks into the
   Query Lab. Running a block first runs the page's earlier blocks that haven't
   run yet, so a query never fails just because its setup block was skipped. */
const QLAB_DOC_SESSIONS = new Map();   // doc key -> { sql schema | mongo shell | redis }
const QLAB_DOC_RAN = new Map();        // doc key -> Set of block indexes already run
const QLAB_DOC_STOPPED = new Map();    // doc key -> Set of block indexes stopped (sqlStop): not re-run as setup

const qlabDocEngine = (mod, id, lang, text) =>
  QLabCore.docEngine(mod, id, lang, text, typeof QLabRedis !== 'undefined' ? QLabRedis.COMMANDS : null);
const QLAB_RUN_LABEL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z"/></svg>Run';
const QLAB_STOP_LABEL = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>Stop';
const qlabDocSchema = key => 'doc_' + key.replace(/[^a-z0-9]+/gi, '_').toLowerCase().slice(0, 50);

function qlabEnhanceDoc(prose, mod, id) {
  if (mod !== 'sql' && mod !== 'nosql') return;
  const key = `${mod}:${id}`;
  const blocks = [];
  $$('.code', prose).forEach(wrap => {
    const code = $('pre > code', wrap);
    if (!code || $('.code-run', wrap)) return;
    const lang = ([...code.classList].find(c => c.startsWith('language-')) || '').slice(9).toLowerCase();
    const engine = qlabDocEngine(mod, id, lang, code.textContent);
    if (!engine) return;
    const block = { wrap, engine, text: code.textContent, idx: blocks.length };
    blocks.push(block);
    const btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'code-run'; btn.innerHTML = QLAB_RUN_LABEL;
    btn.title = engine === 'sql' ? 'Run in PostgreSQL in your browser (this page has its own scratch database)'
      : engine === 'mongodb' ? 'Run in the in-browser MongoDB shell (shop collections loaded)' : 'Run in the in-browser Redis (lab keys loaded)';
    $('.code-head', wrap).insertBefore(btn, $('.code-copy', wrap));
    btn.onclick = () => qlabRunDocBlock(key, blocks, block, btn);
  });
  if (blocks.length) qlabDocBanner(prose, mod, id, blocks);
}

// One line at the top of the chapter, so the Run buttons and the lab are never a surprise.
function qlabDocBanner(prose, mod, id, blocks) {
  if ($('.qlab-doc-banner', prose)) return;
  const engine = blocks[0].engine;
  const what = engine === 'sql' ? 'a real PostgreSQL' : engine === 'mongodb' ? 'a MongoDB shell' : 'Redis';
  const lab = engine === 'sql' ? 'sql' : id.startsWith('redis/') ? 'redis' : 'mongodb';
  const el = document.createElement('div');
  el.className = 'qlab-doc-banner';
  el.innerHTML = `<span class="qlab-doc-banner-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5l12 7-12 7z"/></svg></span>
    <span class="qlab-doc-banner-text"><b>${blocks.length} runnable example${blocks.length === 1 ? '' : 's'} on this page.</b>
    Press <b>Run</b> on a code block to execute it in ${what} inside your browser and see the output, no install needed.
    To write your own queries against real datasets and practise interview questions, open the Query Lab.</span>
    <a class="qlab-doc-banner-go" href="#/query-lab/${lab}">${QLAB_ENGINES[lab].label} Query Lab
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>`;
  const h1 = $('h1', prose);
  (h1 && h1.nextElementSibling) ? h1.nextElementSibling.after(el) : prose.prepend(el);
}

async function qlabDocSession(key, engine) {
  let s = QLAB_DOC_SESSIONS.get(key);
  if (s) return s;
  if (engine === 'sql') {
    const db = await sqlDb();
    const schema = qlabDocSchema(key);
    await db.exec(`DROP SCHEMA IF EXISTS ${schema} CASCADE; CREATE SCHEMA ${schema};`);
    s = { schema };
  } else if (engine === 'mongodb') {
    await mongoBase();
    s = QLabCore.createMongoShell(mingo, QE.mongodb.base);
  } else {
    await redisSeed();
    s = qlabFreshRedis();
  }
  QLAB_DOC_SESSIONS.set(key, s);
  return s;
}

async function qlabDocExec(key, engine, text) {
  const s = await qlabDocSession(key, engine);
  const src = QLabCore.docRunnable(engine, text);
  if (engine === 'sql') {
    const db = await sqlDb();
    await db.exec(`SET search_path TO ${s.schema}, public`);
    try {
      const r = await db.exec(src, { limit: true });
      return { kind: 'table', statements: r.length, ...QLabCore.sqlLastResult(r), note: await sqlCloseTxn(db) };
    } finally {
      await sqlCloseTxn(db);
    }
  }
  if (engine === 'mongodb') return { kind: 'mongo', value: s.run(src) };
  return { kind: 'redis', results: QLabRedis.runScript(s, src) };
}

async function qlabResetDoc(key) {
  const s = QLAB_DOC_SESSIONS.get(key);
  if (s && s.schema && QE.sql.db) await QE.sql.db.exec(`DROP SCHEMA IF EXISTS ${s.schema} CASCADE`);
  QLAB_DOC_SESSIONS.delete(key);
  QLAB_DOC_RAN.delete(key);
  QLAB_DOC_STOPPED.delete(key);
}

async function qlabRunDocBlock(key, blocks, block, btn) {
  const { wrap, engine } = block;
  let out = wrap.nextElementSibling;
  if (!out || !out.classList.contains('qlab-doc-out')) {
    out = document.createElement('div');
    out.className = 'qlab-doc-out';
    out.setAttribute('aria-live', 'polite');
    wrap.after(out);
  }
  wrap.classList.add('has-run-out');            // code block and its output read as one card
  out.innerHTML = `<div class="qlab-meta"><span>Running…${engine === 'sql' && !QE.sql.db ? ' (starting PostgreSQL, a few seconds the first time)' : ''}</span></div>`;
  btn.setAttribute('aria-busy', 'true');
  // SQL: the button becomes Stop while the block runs (sqlStop restarts the database)
  const idle = { title: btn.title, onclick: btn.onclick };
  if (engine === 'sql') {
    btn.innerHTML = QLAB_STOP_LABEL; btn.title = 'Stop this query (restarts PostgreSQL in your browser)';
    btn.classList.add('is-stop');
    btn.onclick = () => sqlStop('user');
  } else {
    btn.disabled = true;
    btn.textContent = 'Running…';
  }
  const ran = QLAB_DOC_RAN.get(key) || new Set();
  QLAB_DOC_RAN.set(key, ran);
  const stopped = QLAB_DOC_STOPPED.get(key) || new Set();
  QLAB_DOC_STOPPED.set(key, stopped);
  let current = null;                           // the block executing, if it gets stopped
  const tools = `<button type="button" class="qlab-doc-reset" title="Throw away this page's scratch data and start again">↺ Reset page data</button>`;
  try {
    // Earlier blocks first (setup, inserts), once each; their own errors don't stop this one.
    let before = 0;
    for (const b of blocks) {
      if (b.idx >= block.idx) break;
      if (b.engine !== engine || ran.has(b.idx) || stopped.has(b.idx)) continue;
      ran.add(b.idx);
      before++;
      current = b;
      try { await qlabDocExec(key, engine, b.text); } catch (e) { if (e.stopped) throw e; /* else an earlier demo of an error */ }
    }
    const t0 = performance.now();
    ran.add(block.idx);
    current = block;
    const res = await qlabDocExec(key, engine, block.text);
    res.ms = performance.now() - t0;
    const scaled = QLabCore.docScaled(engine, block.text);
    if (scaled) res.note = [`Scaled down for the browser: ${QLabCore.DOC_MAX_ROWS.toLocaleString()} rows instead of ${scaled.toLocaleString()}, so counts and timings on this page will be smaller than the text describes.`, res.note].filter(Boolean).join(' ');
    out.innerHTML = qlabResultHtml(res)
      + `<div class="qlab-doc-foot">${before ? `<span>Ran ${before} earlier block${before === 1 ? '' : 's'} on this page first, so their setup is in place.</span>` : '<span></span>'}${tools}</div>`;
  } catch (e) {
    if (e.stopped && current) stopped.add(current.idx);
    out.innerHTML = `<div class="qlab-verdict is-err"><b>${e.stopped ? 'Stopped' : 'Error'}</b><pre>${esc(e.message || String(e))}</pre>
      <p class="qlab-trunc">${e.stopped
        ? 'PGlite cannot cancel a running statement, so it was restarted and this page\'s scratch data was cleared. The next Run sets it up again.'
        : engine === 'sql'
        ? 'This page has one scratch database shared by its blocks. If a table already exists because a block ran twice, reset the page data and run again.'
        : 'This page has its own scratch data. Reset it to start from the original data.'}</p></div>
      <div class="qlab-doc-foot"><span></span>${tools}</div>`;
  } finally {
    btn.disabled = false;
    btn.removeAttribute('aria-busy');
    btn.innerHTML = QLAB_RUN_LABEL;
    btn.title = idle.title; btn.onclick = idle.onclick;
    btn.classList.remove('is-stop');
  }
  const reset = $('.qlab-doc-reset', out);
  if (reset) reset.onclick = async () => {
    await qlabResetDoc(key);
    const page = wrap.closest('.doc-prose') || document;
    $$('.qlab-doc-out', page).forEach(o => o.remove());
    $$('.code.has-run-out', page).forEach(c => c.classList.remove('has-run-out'));
    toast('Page data reset: blocks will run from a clean start');
  };
}
