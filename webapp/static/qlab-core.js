/* ============================================================================
   Query Lab core — engine-independent pieces shared by the lab UI (qlab.js)
   and the validator (webapp/scripts/validate_query_labs.mjs):

     normValue / compareResults   check an answer against the reference
     sqlLastResult                pick what a multi-statement SQL run returns
     createMongoShell             a mongosh-style `db` over mingo
     runRedisCheck                the last reply of a Redis script, for checks

   Browser: one global, QLabCore. Node: module.exports.
   ========================================================================= */
(function (root) {
  'use strict';

  /* --------------------------------------------------------- comparing -- */
  const NUMERIC = /^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i;
  const stable = v => {
    if (Array.isArray(v)) return `[${v.map(stable).join(',')}]`;
    if (v && typeof v === 'object' && !(v instanceof Date)) {
      return `{${Object.keys(v).sort().map(k => `${JSON.stringify(k)}:${stable(v[k])}`).join(',')}}`;
    }
    return JSON.stringify(normValue(v));
  };

  /* One canonical form per value, so "12.50" (numeric), 12.5 (float) and 12.5000 compare equal,
     a date compares equal to midnight UTC of that date, and JSON compares by content. */
  function normValue(v) {
    if (v === null || v === undefined) return null;
    if (v instanceof Date) {
      const iso = v.toISOString();
      return iso.endsWith('T00:00:00.000Z') ? iso.slice(0, 10) : iso.replace('.000Z', 'Z');
    }
    if (typeof v === 'bigint') v = Number(v);
    if (typeof v === 'number') return Number.isFinite(v) ? String(Math.round(v * 100) / 100) : String(v);
    if (typeof v === 'string') {
      const s = v.trim();
      if (NUMERIC.test(s)) return String(Math.round(Number(s) * 100) / 100);
      if (/^\d{4}-\d{2}-\d{2}T00:00:00(\.000)?Z$/.test(s)) return s.slice(0, 10);
      return v.replace(/\s+$/, '');            // char(n) padding
    }
    if (typeof v === 'boolean') return v;
    if (typeof v === 'object') return stable(v);
    return String(v);
  }

  const rowKey = row => JSON.stringify(row);

  /* expected/actual: { columns: [...], rows: [[...], ...] }. ordered: row order matters. */
  function compareResults(expected, actual, ordered) {
    const E = expected.rows.map(r => r.map(normValue));
    const A = actual.rows.map(r => r.map(normValue));
    const ec = expected.columns.length, ac = actual.columns.length;
    if (ec !== ac) {
      return { ok: false, reason: `Expected ${ec} column${ec === 1 ? '' : 's'} (${expected.columns.join(', ')}), got ${ac}.` };
    }
    if (E.length !== A.length) {
      return { ok: false, reason: `Expected ${E.length} row${E.length === 1 ? '' : 's'}, got ${A.length}.` };
    }
    if (ordered) {
      for (let i = 0; i < E.length; i++) {
        if (rowKey(E[i]) !== rowKey(A[i])) {
          const sameSet = rowKey([...E].map(rowKey).sort()) === rowKey([...A].map(rowKey).sort());
          return sameSet
            ? { ok: false, reason: 'Right rows, wrong order. Check your ORDER BY (and its tie-breaker).', row: i }
            : { ok: false, reason: `Row ${i + 1} differs.`, row: i, expectedRow: expected.rows[i], actualRow: actual.rows[i] };
        }
      }
      return { ok: true };
    }
    const count = new Map();
    for (const r of E) count.set(rowKey(r), (count.get(rowKey(r)) || 0) + 1);
    for (let i = 0; i < A.length; i++) {
      const k = rowKey(A[i]);
      if (!count.get(k)) return { ok: false, reason: `Row ${i + 1} is not in the expected result.`, row: i, actualRow: actual.rows[i] };
      count.set(k, count.get(k) - 1);
    }
    return { ok: true };
  }

  /* ---------------------------------------------------------------- SQL -- */
  // PGlite exec() returns one result per statement; show the last one that returned rows,
  // else the last statement's affected-row count.
  function sqlLastResult(results) {
    const withRows = [...results].reverse().find(r => r.fields && r.fields.length);
    if (withRows) {
      return { columns: withRows.fields.map(f => f.name), rows: withRows.rows.map(r => withRows.fields.map(f => r[f.name])) };
    }
    const last = results[results.length - 1];
    return { columns: [], rows: [], affected: last ? last.affectedRows ?? 0 : 0 };
  }

  /* ------------------------------------------------------------ MongoDB -- */
  // EJSON from the dataset files ({"$date": "..."}) -> real Dates, recursively.
  function reviveEjson(v) {
    if (Array.isArray(v)) return v.map(reviveEjson);
    if (v && typeof v === 'object') {
      if (typeof v.$date === 'string' && Object.keys(v).length === 1) return new Date(v.$date);
      const o = {};
      for (const k of Object.keys(v)) o[k] = reviveEjson(v[k]);
      return o;
    }
    return v;
  }
  // Deep copy that keeps Dates as Dates (a JSON round-trip would turn them into strings).
  function clone(v) {
    if (v instanceof Date) return new Date(v.getTime());
    if (Array.isArray(v)) return v.map(clone);
    if (v && typeof v === 'object') {
      if (v.constructor && v.constructor.name === 'ObjectId') return v;
      const o = {};
      for (const k of Object.keys(v)) o[k] = clone(v[k]);
      return o;
    }
    return v;
  }

  let oidCounter = 0;
  class ObjectId {
    constructor(hex) {
      this.hex = hex || (Math.floor(Date.now() / 1000).toString(16) + (++oidCounter).toString(16).padStart(16, '0')).slice(0, 24);
    }
    toString() { return this.hex; }
    toJSON() { return { $oid: this.hex }; }
  }

  /* A mongosh-like `db` over in-memory arrays. Reads see the base data; the first write to a
     collection copies it (copy-on-write), so base datasets are never mutated and a reset is
     just "drop the copies". */
  function createMongoShell(mingo, base) {
    const data = {};          // name -> working array (only for collections written to)
    const docs = name => data[name] || base[name] || (data[name] = []);
    const writable = name => (data[name] ||= base[name] ? clone(base[name]) : []);
    const resolver = name => docs(name);
    const opts = () => ({ collectionResolver: resolver, idKey: '_id' });
    const proj = p => (p && Object.keys(p).length ? p : undefined);

    class Cursor {
      constructor(fn) { this.fn = fn; this._sort = null; this._skip = 0; this._limit = 0; }
      sort(s) { this._sort = s; return this; }
      skip(n) { this._skip = n; return this; }
      limit(n) { this._limit = n; return this; }
      toArray() {
        let c = this.fn();
        if (this._sort) c = c.sort(this._sort);
        if (this._skip) c = c.skip(this._skip);
        if (this._limit) c = c.limit(this._limit);
        return c.all();
      }
      count() { return this.toArray().length; }
      size() { return this.count(); }
      map(f) { return this.toArray().map(f); }
      forEach(f) { this.toArray().forEach(f); }
      hasNext() { return this.toArray().length > 0; }
      next() { return this.toArray()[0] ?? null; }
      pretty() { return this; }
      explain() { return { note: 'explain() is not available in the in-browser lab; run it on a real MongoDB.' }; }
    }
    class AggCursor extends Cursor {
      constructor(rows) { super(null); this.rows = rows; }
      toArray() { return this.rows; }
    }

    const matchIdx = (arr, filter) => {
      const q = new mingo.Query(filter || {});
      const out = [];
      arr.forEach((d, i) => { if (q.test(d)) out.push(i); });
      return out;
    };
    const applyUpdate = (arr, i, update) => {
      if (Array.isArray(update)) {                       // aggregation-pipeline update
        arr[i] = mingo.aggregate([arr[i]], update, opts())[0];
        return true;
      }
      if (!Object.keys(update).some(k => k.startsWith('$'))) throw new Error('Update document requires atomic operators (use replaceOne to replace a whole document)');
      const one = [arr[i]];
      const r = mingo.updateOne(one, { _id: arr[i]._id }, update);
      arr[i] = one[0];
      return (r && (r.modifiedCount ?? r.modified ?? 1)) > 0;
    };
    const upsertDoc = (filter, update) => {
      const d = {};
      for (const [k, v] of Object.entries(filter || {})) if (!k.startsWith('$') && (v === null || typeof v !== 'object' || v instanceof Date)) d[k] = v;
      const arr = [d];
      if (update.$setOnInsert) mingo.updateOne(arr, {}, { $set: update.$setOnInsert });
      const rest = { ...update }; delete rest.$setOnInsert;
      if (Object.keys(rest).length) mingo.updateOne(arr, {}, rest);
      if (arr[0]._id === undefined) arr[0]._id = new ObjectId();
      return arr[0];
    };

    function collection(name) {
      return {
        find: (filter = {}, projection) => new Cursor(() => new mingo.Query(filter).find(docs(name), proj(projection))),
        findOne: (filter = {}, projection) => new mingo.Query(filter).find(docs(name), proj(projection)).limit(1).all()[0] ?? null,
        aggregate: (pipeline = []) => new AggCursor(mingo.aggregate(docs(name), pipeline, opts())),
        countDocuments: (filter = {}) => new mingo.Query(filter).find(docs(name)).all().length,
        estimatedDocumentCount: () => docs(name).length,
        distinct: (field, filter = {}) => {
          const vals = mingo.aggregate(new mingo.Query(filter).find(docs(name)).all(),
            [{ $unwind: { path: `$${field}`, preserveNullAndEmptyArrays: false } }, { $group: { _id: `$${field}` } }]).map(g => g._id);
          return vals.sort((a, b) => (normValue(a) > normValue(b) ? 1 : -1));
        },
        insertOne: doc => {
          const d = clone(doc); if (d._id === undefined) d._id = new ObjectId();
          if (docs(name).some(x => normValue(x._id) === normValue(d._id))) throw new Error(`E11000 duplicate key error collection: lab.${name} index: _id_ dup key: { _id: ${JSON.stringify(d._id)} }`);
          writable(name).push(d);
          return { acknowledged: true, insertedId: d._id };
        },
        insertMany: list => {
          const ids = list.map(doc => collection(name).insertOne(doc).insertedId);
          return { acknowledged: true, insertedCount: ids.length, insertedIds: ids };
        },
        updateOne: (filter, update, o = {}) => {
          const arr = writable(name); const idx = matchIdx(arr, filter);
          if (!idx.length) {
            if (o.upsert) { const d = upsertDoc(filter, update); arr.push(d); return { acknowledged: true, matchedCount: 0, modifiedCount: 0, upsertedId: d._id }; }
            return { acknowledged: true, matchedCount: 0, modifiedCount: 0 };
          }
          const changed = applyUpdate(arr, idx[0], update);
          return { acknowledged: true, matchedCount: 1, modifiedCount: changed ? 1 : 0 };
        },
        updateMany: (filter, update, o = {}) => {
          const arr = writable(name); const idx = matchIdx(arr, filter);
          if (!idx.length && o.upsert) { const d = upsertDoc(filter, update); arr.push(d); return { acknowledged: true, matchedCount: 0, modifiedCount: 0, upsertedId: d._id }; }
          let modified = 0;
          idx.forEach(i => { if (applyUpdate(arr, i, update)) modified++; });
          return { acknowledged: true, matchedCount: idx.length, modifiedCount: modified };
        },
        replaceOne: (filter, doc, o = {}) => {
          const arr = writable(name); const idx = matchIdx(arr, filter);
          if (!idx.length) {
            if (o.upsert) { const d = clone(doc); d._id ??= new ObjectId(); arr.push(d); return { acknowledged: true, matchedCount: 0, modifiedCount: 0, upsertedId: d._id }; }
            return { acknowledged: true, matchedCount: 0, modifiedCount: 0 };
          }
          arr[idx[0]] = { _id: arr[idx[0]]._id, ...clone(doc) };
          return { acknowledged: true, matchedCount: 1, modifiedCount: 1 };
        },
        findOneAndUpdate: (filter, update, o = {}) => {
          const arr = writable(name); const idx = matchIdx(arr, filter);
          if (!idx.length) return null;
          const before = clone(arr[idx[0]]);
          applyUpdate(arr, idx[0], update);
          const after = arr[idx[0]];
          const doc = o.returnNewDocument || o.returnDocument === 'after' ? after : before;
          return o.projection ? new mingo.Query({}).find([doc], o.projection).all()[0] : doc;
        },
        deleteOne: filter => {
          const arr = writable(name); const idx = matchIdx(arr, filter);
          if (idx.length) arr.splice(idx[0], 1);
          return { acknowledged: true, deletedCount: idx.length ? 1 : 0 };
        },
        deleteMany: filter => {
          const arr = writable(name); const idx = new Set(matchIdx(arr, filter));
          data[name] = arr.filter((_, i) => !idx.has(i));
          return { acknowledged: true, deletedCount: idx.size };
        },
        drop: () => { data[name] = []; return true; },
        createIndex: (keys, o = {}) => o.name || Object.entries(keys).map(([k, v]) => `${k}_${v}`).join('_'),
        getIndexes: () => [{ v: 2, key: { _id: 1 }, name: '_id_' }],
        stats: () => ({ ns: `lab.${name}`, count: docs(name).length }),
      };
    }

    const db = new Proxy({}, {
      get(_, prop) {
        if (prop === 'getCollectionNames') return () => [...new Set([...Object.keys(base), ...Object.keys(data)])].sort();
        if (prop === 'getCollection' || prop === 'collection') return n => collection(n);
        if (prop === 'getName') return () => 'lab';
        if (typeof prop === 'symbol' || prop === 'then' || prop === 'toJSON') return undefined;
        return collection(prop);
      },
    });

    const helpers = {
      ISODate: s => (s === undefined ? new Date() : new Date(s)),
      ObjectId: h => new ObjectId(h),
      NumberInt: n => Number(n), NumberLong: n => Number(n), NumberDecimal: n => Number(n), Double: n => Number(n),
    };
    const names = Object.keys(helpers);

    /* Run mongosh-style code: statements separated by ; or newlines, the value of the last
       expression is the result. Cursors are drained so the UI gets plain documents. */
    function run(code) {
      const src = String(code).replace(/^\s*use\s+\w+\s*;?\s*$/gm, '');   // `use shop` is a no-op here
      // eslint-disable-next-line no-new-func
      const fn = new Function('db', ...names, '__src', '"use strict"; return eval(__src);');
      let out = fn(db, ...names.map(n => helpers[n]), src);
      if (out instanceof Cursor) out = out.toArray();
      return out;
    }
    const reset = () => { for (const k of Object.keys(data)) delete data[k]; };
    return { db, run, reset, collectionNames: () => db.getCollectionNames() };
  }

  /* MongoDB results -> table shape for comparing: one row per document, columns = union of keys.
     A scalar (count, distinct value list, update result) becomes a one-cell table. */
  function mongoToTable(out) {
    if (Array.isArray(out) && out.every(d => d && typeof d === 'object' && !Array.isArray(d) && !(d instanceof Date))) {
      const cols = [...new Set(out.flatMap(d => Object.keys(d)))];
      return { columns: cols, rows: out.map(d => cols.map(c => (d[c] === undefined ? null : d[c]))) };
    }
    if (Array.isArray(out)) return { columns: ['value'], rows: out.map(v => [v]) };
    if (out && typeof out === 'object' && !(out instanceof Date)) {
      const cols = Object.keys(out);
      return { columns: cols, rows: [cols.map(c => out[c])] };
    }
    return { columns: ['value'], rows: [[out]] };
  }
  // Document results compare by content (key order and column order don't matter).
  function compareMongo(expected, actual, ordered) {
    const docRows = out => (Array.isArray(out) ? out : [out]).map(d => [stable(d)]);
    return compareResults({ columns: ['doc'], rows: docRows(expected) }, { columns: ['doc'], rows: docRows(actual) }, ordered);
  }

  /* -------------------------------------------------------------- Redis -- */
  // The reply that a Redis exercise is judged on: the last command's reply.
  function redisLastReply(results) {
    const last = results[results.length - 1];
    return last ? last.reply : null;
  }

  /* ------------------------------------------------- chapter code blocks -- */
  // Which engine runs a chapter's code block, or null. Shared by the reader's Run buttons
  // and validate_doc_runs.mjs, so the validator checks exactly the blocks a learner can run.
  //   SQL chapters:     ```sql
  //   MongoDB chapters: ```js / ```javascript that use db.<collection>
  //   Redis chapters:   ```redis / ```bash made only of Redis commands
  function docEngine(mod, id, lang, text, redisCommands) {
    lang = (lang || '').toLowerCase();
    if (mod === 'sql' && lang === 'sql') return 'sql';
    if (mod === 'nosql' && id.startsWith('mongodb/') && (lang === 'javascript' || lang === 'js') && /\bdb\.\w+/.test(text)) return 'mongodb';
    if (mod === 'nosql' && id.startsWith('redis/') && (lang === 'bash' || lang === 'redis') && redisCommands) {
      const lines = text.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));
      if (lines.length && lines.every(l => redisCommands[l.split(/\s+/)[0].toUpperCase()])) return 'redis';
    }
    return null;
  }
  // The text an engine actually runs: psql meta-commands (\d, \timing) and redis "# -> 1"
  // notes are documentation, not input.
  // Tables the chapters fill with up to 2M rows (for realistic EXPLAIN plans) are capped at
  // 1,000 rows in the browser: plenty to see what a query returns, instead of a WASM Postgres
  // spending minutes and gigabytes building them.
  const DOC_MAX_ROWS = 1000;
  const BIG_SERIES = /generate_series\(\s*1\s*,\s*([\d_]+)\s*\)/gi;
  function docScaled(engine, text) {
    if (engine !== 'sql') return 0;
    let n = 0;
    for (const m of text.matchAll(BIG_SERIES)) n = Math.max(n, +m[1].replace(/_/g, ''));
    return n > DOC_MAX_ROWS ? n : 0;
  }
  function docRunnable(engine, text) {
    if (engine === 'sql') {
      return text.split('\n').filter(l => !/^\s*\\/.test(l)).join('\n')
        .replace(BIG_SERIES, (m, n) => (+n.replace(/_/g, '') > DOC_MAX_ROWS ? `generate_series(1, ${DOC_MAX_ROWS})` : m));
    }
    if (engine === 'redis') return text.split('\n').map(l => l.replace(/\s+#\s.*$/, '')).join('\n');
    return text;
  }

  const api = { docEngine, docRunnable, docScaled, DOC_MAX_ROWS, normValue, compareResults, sqlLastResult, reviveEjson, createMongoShell, mongoToTable, compareMongo, redisLastReply, stable };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.QLabCore = api;
})(typeof window !== 'undefined' ? window : globalThis);
