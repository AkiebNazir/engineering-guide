/* ============================================================================
   MiniRedis — an in-browser Redis for the Query Lab.

   Implements the commands a learner meets in NoSQL/redis/ and in interviews:
   keys + expiry, strings and counters, hashes, lists, sets, sorted sets,
   bitmaps, HyperLogLog, geo, streams (with consumer groups), MULTI/EXEC and
   WATCH. Replies are plain JS values and format() prints them exactly the way
   redis-cli does. Anything outside that set answers with a clear error that
   points to the real server (docker-compose.databases.yml).

   Same file in the browser (one global, QLabRedis) and in Node (module.exports),
   so webapp/scripts/validate_query_labs.mjs can test it.
   ========================================================================= */
(function (root) {
  'use strict';

  class RedisError extends Error {}
  const err = msg => { throw new RedisError(msg); };
  const WRONGTYPE = 'WRONGTYPE Operation against a key holding the wrong kind of value';
  const NOT_INT = 'ERR value is not an integer or out of range';
  const NOT_FLOAT = 'ERR value is not a valid float';
  const SYNTAX = 'ERR syntax error';

  // One reply type per Redis reply kind, so format() can print like redis-cli.
  class Status { constructor(s) { this.s = s; } }
  const OK = new Status('OK');
  const QUEUED = new Status('QUEUED');

  const toInt = s => {
    if (typeof s === 'number' && Number.isInteger(s)) return s;
    if (!/^[+-]?\d+$/.test(String(s))) err(NOT_INT);
    const n = Number(s);
    if (!Number.isSafeInteger(n)) err(NOT_INT);
    return n;
  };
  const toFloat = s => {
    const t = String(s).toLowerCase();
    if (t === '+inf' || t === 'inf') return Infinity;
    if (t === '-inf') return -Infinity;
    const n = Number(s);
    if (String(s).trim() === '' || Number.isNaN(n)) err(NOT_FLOAT);
    return n;
  };
  // Redis prints doubles in the shortest form that round-trips ("3", "1.5", "inf").
  const fmtFloat = n => (n === Infinity ? 'inf' : n === -Infinity ? '-inf' : String(Number(n.toPrecision(17))));

  // Glob matching for KEYS / SCAN MATCH / HSCAN: * ? [abc] [^a] \x
  const globRe = pat => {
    let re = '';
    for (let i = 0; i < pat.length; i++) {
      const c = pat[i];
      if (c === '*') re += '.*';
      else if (c === '?') re += '.';
      else if (c === '[') {
        const j = pat.indexOf(']', i + 1);
        if (j < 0) { re += '\\['; continue; }
        let set = pat.slice(i + 1, j);
        if (set[0] === '^') set = '^' + set.slice(1).replace(/[\\\]]/g, '\\$&');
        else set = set.replace(/[\\\]]/g, '\\$&');
        re += `[${set}]`; i = j;
      } else if (c === '\\' && i + 1 < pat.length) re += pat[++i].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      else re += c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    return new RegExp(`^${re}$`, 's');
  };

  /* Split one command line the way redis-cli does: whitespace separates
     arguments; "double quotes" support \n \t \" \\ \xHH escapes; 'single
     quotes' are literal except \'. */
  function tokenize(line) {
    const out = [];
    let i = 0;
    while (i < line.length) {
      while (i < line.length && /\s/.test(line[i])) i++;
      if (i >= line.length) break;
      let tok = '';
      if (line[i] === '"') {
        i++;
        for (;;) {
          if (i >= line.length) err('ERR unbalanced quotes in request');
          const c = line[i];
          if (c === '\\' && i + 1 < line.length) {
            const n = line[i + 1];
            if (n === 'x' && /^[0-9a-fA-F]{2}$/.test(line.slice(i + 2, i + 4))) { tok += String.fromCharCode(parseInt(line.slice(i + 2, i + 4), 16)); i += 4; continue; }
            tok += { n: '\n', r: '\r', t: '\t', b: '\b', a: '\x07' }[n] ?? n; i += 2; continue;
          }
          if (c === '"') { i++; break; }
          tok += c; i++;
        }
        if (i < line.length && !/\s/.test(line[i])) err('ERR unbalanced quotes in request');
      } else if (line[i] === "'") {
        i++;
        for (;;) {
          if (i >= line.length) err('ERR unbalanced quotes in request');
          if (line[i] === '\\' && line[i + 1] === "'") { tok += "'"; i += 2; continue; }
          if (line[i] === "'") { i++; break; }
          tok += line[i++];
        }
        if (i < line.length && !/\s/.test(line[i])) err('ERR unbalanced quotes in request');
      } else {
        while (i < line.length && !/\s/.test(line[i])) tok += line[i++];
      }
      out.push(tok);
    }
    return out;
  }

  // Sorted-set ordering: by score, then by member (binary-safe string order).
  const zcmp = (a, b) => (a.score - b.score) || (a.member < b.member ? -1 : a.member > b.member ? 1 : 0);

  // Stream ids "ms-seq"
  const parseId = (s, missingSeq = 0) => {
    if (s === '-') return [0, 0];
    if (s === '+') return [Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER];
    const m = String(s).match(/^(\d+)(?:-(\d+))?$/);
    if (!m) err('ERR Invalid stream ID specified as stream command argument');
    return [Number(m[1]), m[2] === undefined ? missingSeq : Number(m[2])];
  };
  const idCmp = (a, b) => (a[0] - b[0]) || (a[1] - b[1]);
  const idStr = id => `${id[0]}-${id[1]}`;

  // Geo: haversine on the Earth radius Redis uses.
  const EARTH_R = 6372797.560856;
  const rad = d => (d * Math.PI) / 180;
  const haversine = (lon1, lat1, lon2, lat2) => {
    const a = Math.sin(rad(lat2 - lat1) / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lon2 - lon1) / 2) ** 2;
    return 2 * EARTH_R * Math.asin(Math.sqrt(a));
  };
  const UNIT = { m: 1, km: 1000, mi: 1609.34, ft: 0.3048 };

  class MiniRedis {
    constructor({ now = () => Date.now() } = {}) {
      this.now = now;
      this.db = new Map();        // key -> { type, value, expireAt }
      this.versions = new Map();  // key -> write counter, for WATCH
      this.tx = null;             // queued commands inside MULTI
      this.txError = false;
      this.watched = null;        // Map key -> version at WATCH time
      this.lastStreamMs = 0;
    }

    /* -------------------------------------------------------- key store -- */
    _get(key) {
      const e = this.db.get(key);
      if (!e) return null;
      if (e.expireAt != null && e.expireAt <= this.now()) { this.db.delete(key); this._touch(key); return null; }
      return e;
    }
    _touch(key) { this.versions.set(key, (this.versions.get(key) || 0) + 1); }
    _typed(key, type) {
      const e = this._get(key);
      if (e && e.type !== type) err(WRONGTYPE);
      return e;
    }
    _make(key, type, value) {
      const e = { type, value, expireAt: null };
      this.db.set(key, e);
      return e;
    }
    _getOrMake(key, type, init) {
      return this._typed(key, type) || this._make(key, type, init());
    }
    // Drop containers that became empty, like Redis does.
    _cleanup(key) {
      const e = this.db.get(key);
      if (!e) return;
      const v = e.value;
      const size = e.type === 'string' ? 1 : e.type === 'stream' ? 1 : v instanceof Map || v instanceof Set ? v.size : Array.isArray(v) ? v.length : 1;
      if (size === 0) this.db.delete(key);
    }
    _str(key) {
      const e = this._typed(key, 'string');
      return e ? e.value : null;
    }
    _setStr(key, value, keepTtl = false) {
      const prev = this._get(key);
      const e = this._make(key, 'string', String(value));
      if (keepTtl && prev) e.expireAt = prev.expireAt;
      this._touch(key);
    }

    /* ---------------------------------------------------------- dispatch -- */
    exec(line) {
      const argv = Array.isArray(line) ? line.map(String) : tokenize(line);
      if (!argv.length) return null;
      return this.command(argv);
    }

    command(argv) {
      const name = argv[0].toUpperCase();
      const args = argv.slice(1);
      if (this.tx && !['EXEC', 'DISCARD', 'MULTI', 'WATCH', 'UNWATCH'].includes(name)) {
        const spec = COMMANDS[name];
        if (!spec) { this.txError = true; err(`ERR unknown command '${argv[0]}'`); }
        if (!arityOk(spec, args.length)) { this.txError = true; err(`ERR wrong number of arguments for '${name.toLowerCase()}' command`); }
        this.tx.push(argv);
        return QUEUED;
      }
      const spec = COMMANDS[name];
      if (!spec) {
        err(UNSUPPORTED.has(name)
          ? `ERR '${name}' is not available in the in-browser lab; run it on a real Redis (docker compose -f docker-compose.databases.yml up -d)`
          : `ERR unknown command '${argv[0]}', with args beginning with: ${args.slice(0, 3).map(a => `'${a}'`).join(' ')}`);
      }
      if (!arityOk(spec, args.length)) err(`ERR wrong number of arguments for '${name.toLowerCase()}' command`);
      return spec.fn.call(this, args, name);
    }

    /* Load many commands (one per line, # comments allowed). Returns count. */
    load(script) {
      let n = 0;
      for (const raw of script.split('\n')) {
        const line = raw.trim();
        if (!line || line.startsWith('#')) continue;
        this.exec(line); n++;
      }
      return n;
    }

    // Read-only snapshot for the lab's key browser.
    keys() {
      const out = [];
      for (const k of [...this.db.keys()].sort()) {
        const e = this._get(k);
        if (!e) continue;
        const v = e.value;
        const size = e.type === 'string' ? v.length : e.type === 'stream' ? v.entries.length : v.size ?? v.length;
        out.push({ key: k, type: e.type, size, ttl: e.expireAt == null ? -1 : Math.ceil((e.expireAt - this.now()) / 1000) });
      }
      return out;
    }
  }

  const arityOk = (spec, n) => (spec.min == null || n >= spec.min) && (spec.max == null || n <= spec.max) && (!spec.even || n % 2 === 0) && (!spec.odd || n % 2 === 1);

  const UNSUPPORTED = new Set(['EVAL', 'EVALSHA', 'SCRIPT', 'FUNCTION', 'FCALL', 'SUBSCRIBE', 'PSUBSCRIBE', 'PUBLISH',
    'UNSUBSCRIBE', 'MONITOR', 'CLIENT', 'CONFIG', 'SAVE', 'BGSAVE', 'BGREWRITEAOF', 'REPLICAOF', 'SLAVEOF', 'CLUSTER',
    'BLPOP', 'BRPOP', 'BLMOVE', 'BZPOPMIN', 'BZPOPMAX', 'WAIT', 'OBJECT', 'MEMORY', 'SLOWLOG', 'LATENCY', 'ACL', 'AUTH',
    'SELECT', 'SWAPDB', 'MIGRATE', 'DUMP', 'RESTORE', 'SORT', 'SORT_RO']);

  /* ------------------------------------------------------------ helpers -- */
  function zrangeGeneric(self, key, startArg, stopArg, opts) {
    const e = self._typed(key, 'zset');
    if (!e) return [];
    let items = [...e.value.entries()].map(([member, score]) => ({ member, score })).sort(zcmp);
    if (opts.byScore) {
      let [lo, hi] = [startArg, stopArg];
      if (opts.rev) [lo, hi] = [hi, lo];
      const bound = s => {
        const ex = String(s).startsWith('(');
        return { v: toFloat(ex ? String(s).slice(1) : s), ex };
      };
      const L = bound(lo), H = bound(hi);
      items = items.filter(({ score }) => (L.ex ? score > L.v : score >= L.v) && (H.ex ? score < H.v : score <= H.v));
      if (opts.rev) items.reverse();
      if (opts.limit) items = items.slice(opts.limit[0], opts.limit[1] < 0 ? undefined : opts.limit[0] + opts.limit[1]);
    } else if (opts.byLex) {
      let [lo, hi] = [startArg, stopArg];
      if (opts.rev) [lo, hi] = [hi, lo];
      const ok = (m, b, low) => {
        if (b === '-') return low; if (b === '+') return !low;
        const v = b.slice(1), inc = b[0] === '[';
        if (b[0] !== '[' && b[0] !== '(') err('ERR min or max not valid string range item');
        return low ? (inc ? m >= v : m > v) : (inc ? m <= v : m < v);
      };
      items = items.filter(({ member }) => ok(member, lo, true) && ok(member, hi, false));
      if (opts.rev) items.reverse();
      if (opts.limit) items = items.slice(opts.limit[0], opts.limit[1] < 0 ? undefined : opts.limit[0] + opts.limit[1]);
    } else {
      if (opts.rev) items.reverse();
      const n = items.length;
      let a = toInt(startArg), b = toInt(stopArg);
      if (a < 0) a = Math.max(n + a, 0);
      if (b < 0) b = n + b;
      if (b >= n) b = n - 1;
      items = a > b ? [] : items.slice(a, b + 1);
    }
    return opts.withScores ? items.flatMap(i => [i.member, fmtFloat(i.score)]) : items.map(i => i.member);
  }

  function parseZrangeOpts(args, from, base) {
    const o = { ...base };
    for (let i = from; i < args.length; i++) {
      const a = args[i].toUpperCase();
      if (a === 'WITHSCORES') o.withScores = true;
      else if (a === 'BYSCORE') o.byScore = true;
      else if (a === 'BYLEX') o.byLex = true;
      else if (a === 'REV') o.rev = true;
      else if (a === 'LIMIT' && i + 2 < args.length + 0 && args[i + 2] !== undefined) { o.limit = [toInt(args[i + 1]), toInt(args[i + 2])]; i += 2; }
      else err(SYNTAX);
    }
    if (o.limit && !o.byScore && !o.byLex) err('ERR syntax error, LIMIT is only supported in combination with either BYSCORE or BYLEX');
    return o;
  }

  function setOp(self, keys, op) {
    const sets = keys.map(k => { const e = self._typed(k, 'set'); return e ? e.value : new Set(); });
    let out;
    if (op === 'union') { out = new Set(); sets.forEach(s => s.forEach(x => out.add(x))); }
    else if (op === 'inter') { out = new Set([...sets[0]].filter(x => sets.every(s => s.has(x)))); }
    else { out = new Set([...sets[0]].filter(x => !sets.slice(1).some(s => s.has(x)))); }
    return out;
  }
  const sortedMembers = s => [...s].sort();   // deterministic order for the lab (real Redis is unordered)

  function storeSet(self, dest, set) {
    self.db.delete(dest);
    if (set.size) self._make(dest, 'set', set);
    self._touch(dest);
    return set.size;
  }

  function zstore(self, args, op) {
    const dest = args[0], n = toInt(args[1]);
    if (n < 1) err('ERR at least 1 input key is needed for ZUNIONSTORE/ZINTERSTORE');
    const keys = args.slice(2, 2 + n);
    if (keys.length < n) err(SYNTAX);
    let weights = keys.map(() => 1), agg = 'SUM';
    for (let i = 2 + n; i < args.length; i++) {
      const a = args[i].toUpperCase();
      if (a === 'WEIGHTS') { weights = keys.map((_, j) => toFloat(args[i + 1 + j])); i += n; }
      else if (a === 'AGGREGATE') { agg = (args[++i] || '').toUpperCase(); if (!['SUM', 'MIN', 'MAX'].includes(agg)) err(SYNTAX); }
      else err(SYNTAX);
    }
    const maps = keys.map(k => {
      const e = self._get(k);
      if (!e) return new Map();
      if (e.type === 'set') return new Map([...e.value].map(m => [m, 1]));
      if (e.type !== 'zset') err(WRONGTYPE);
      return e.value;
    });
    const combine = (a, b) => (agg === 'SUM' ? a + b : agg === 'MIN' ? Math.min(a, b) : Math.max(a, b));
    const out = new Map();
    if (op === 'union') {
      maps.forEach((m, j) => m.forEach((s, mem) => out.set(mem, out.has(mem) ? combine(out.get(mem), s * weights[j]) : s * weights[j])));
    } else {
      for (const [mem, s] of maps[0]) {
        if (maps.every(m => m.has(mem))) out.set(mem, maps.slice(1).reduce((acc, m, j) => combine(acc, m.get(mem) * weights[j + 1]), s * weights[0]));
      }
    }
    self.db.delete(dest);
    if (out.size) self._make(dest, 'zset', out);
    self._touch(dest);
    return out.size;
  }

  function streamOf(self, key, create) {
    const e = self._typed(key, 'stream');
    if (e) return e.value;
    if (!create) return null;
    return self._make(key, 'stream', { entries: [], last: [0, 0], groups: new Map() }).value;
  }
  const entryReply = e => [idStr(e.id), e.fields.slice()];

  function scanGeneric(items, args, from, label) {
    const cursor = toInt(args[from - 1]);
    let match = null, count = 10, type = null;
    for (let i = from; i < args.length; i++) {
      const a = args[i].toUpperCase();
      if (a === 'MATCH') match = globRe(args[++i] ?? err(SYNTAX));
      else if (a === 'COUNT') count = toInt(args[++i] ?? err(SYNTAX));
      else if (a === 'TYPE' && label === 'keys') type = (args[++i] ?? err(SYNTAX)).toLowerCase();
      else err(SYNTAX);
    }
    const page = items.slice(cursor, cursor + count);
    const next = cursor + count >= items.length ? 0 : cursor + count;
    return { next: String(next), page, match, type };
  }

  /* ------------------------------------------------------------ commands -- */
  const C = {};
  const def = (names, spec, fn) => names.split(' ').forEach(n => { C[n] = { ...spec, fn }; });

  // server / connection
  def('PING', { max: 1 }, a => (a.length ? a[0] : new Status('PONG')));
  def('ECHO', { min: 1, max: 1 }, a => a[0]);
  def('TIME', { max: 0 }, function () { const t = this.now(); return [String(Math.floor(t / 1000)), String((t % 1000) * 1000)]; });
  def('DBSIZE', { max: 0 }, function () { return [...this.db.keys()].filter(k => this._get(k)).length; });
  def('FLUSHDB FLUSHALL', { max: 1 }, function () { for (const k of this.db.keys()) this._touch(k); this.db.clear(); return OK; });
  def('COMMAND', {}, () => Object.keys(C).sort().map(c => c.toLowerCase()));
  def('INFO', { max: 1 }, function () {
    return `# Server\r\nredis_version:7.2.0-lab\r\nredis_mode:standalone (in-browser MiniRedis)\r\n# Keyspace\r\ndb0:keys=${this.command(['DBSIZE'])}\r\n`;
  });

  // keys
  def('DEL UNLINK', { min: 1 }, function (a) { let n = 0; for (const k of a) if (this._get(k)) { this.db.delete(k); this._touch(k); n++; } return n; });
  def('EXISTS', { min: 1 }, function (a) { return a.filter(k => this._get(k)).length; });
  def('TYPE', { min: 1, max: 1 }, function (a) { const e = this._get(a[0]); return new Status(e ? e.type : 'none'); });
  def('KEYS', { min: 1, max: 1 }, function (a) { const re = globRe(a[0]); return [...this.db.keys()].filter(k => this._get(k) && re.test(k)).sort(); });
  def('SCAN', { min: 1 }, function (a) {
    const all = [...this.db.keys()].filter(k => this._get(k)).sort();
    const { next, page, match, type } = scanGeneric(all, a, 1, 'keys');
    return [next, page.filter(k => (!match || match.test(k)) && (!type || this._get(k).type === type))];
  });
  def('RENAME RENAMENX', { min: 2, max: 2 }, function (a, name) {
    const e = this._get(a[0]);
    if (!e) err('ERR no such key');
    if (name === 'RENAMENX' && this._get(a[1])) return 0;
    this.db.delete(a[0]); this.db.set(a[1], e); this._touch(a[0]); this._touch(a[1]);
    return name === 'RENAMENX' ? 1 : OK;
  });
  def('EXPIRE PEXPIRE EXPIREAT PEXPIREAT', { min: 2, max: 3 }, function (a, name) {
    const e = this._get(a[0]);
    const n = toInt(a[1]);
    const at = name === 'EXPIRE' ? this.now() + n * 1000 : name === 'PEXPIRE' ? this.now() + n : name === 'EXPIREAT' ? n * 1000 : n;
    if (!e) return 0;
    const flag = (a[2] || '').toUpperCase();
    if (flag === 'NX' && e.expireAt != null) return 0;
    if (flag === 'XX' && e.expireAt == null) return 0;
    if (flag === 'GT' && (e.expireAt == null || at <= e.expireAt)) return 0;
    if (flag === 'LT' && e.expireAt != null && at >= e.expireAt) return 0;
    if (flag && !['NX', 'XX', 'GT', 'LT'].includes(flag)) err(`ERR Unsupported option ${a[2]}`);
    if (at <= this.now()) { this.db.delete(a[0]); this._touch(a[0]); return 1; }
    e.expireAt = at; this._touch(a[0]);
    return 1;
  });
  def('TTL PTTL', { min: 1, max: 1 }, function (a, name) {
    const e = this._get(a[0]);
    if (!e) return -2;
    if (e.expireAt == null) return -1;
    const ms = e.expireAt - this.now();
    return name === 'TTL' ? Math.round(ms / 1000) : ms;
  });
  def('PERSIST', { min: 1, max: 1 }, function (a) { const e = this._get(a[0]); if (!e || e.expireAt == null) return 0; e.expireAt = null; return 1; });

  // strings
  def('GET', { min: 1, max: 1 }, function (a) { return this._str(a[0]); });
  def('SET', { min: 2 }, function (a) {
    const [key, val] = a;
    let nx = false, xx = false, get = false, keep = false, at = null;
    for (let i = 2; i < a.length; i++) {
      const o = a[i].toUpperCase();
      if (o === 'NX') nx = true; else if (o === 'XX') xx = true; else if (o === 'GET') get = true; else if (o === 'KEEPTTL') keep = true;
      else if (['EX', 'PX', 'EXAT', 'PXAT'].includes(o)) {
        const n = toInt(a[++i] ?? err(SYNTAX));
        if (n <= 0 && (o === 'EX' || o === 'PX')) err("ERR invalid expire time in 'set' command");
        at = o === 'EX' ? this.now() + n * 1000 : o === 'PX' ? this.now() + n : o === 'EXAT' ? n * 1000 : n;
      } else err(SYNTAX);
    }
    if (nx && xx) err(SYNTAX);
    const prev = get ? this._str(key) : undefined;
    const exists = !!this._get(key);
    if ((nx && exists) || (xx && !exists)) return get ? prev : null;
    this._setStr(key, val, keep);
    if (at != null) this.db.get(key).expireAt = at;
    return get ? prev : OK;
  });
  def('SETNX', { min: 2, max: 2 }, function (a) { if (this._get(a[0])) return 0; this._setStr(a[0], a[1]); return 1; });
  def('SETEX PSETEX', { min: 3, max: 3 }, function (a, name) {
    const n = toInt(a[1]);
    if (n <= 0) err(`ERR invalid expire time in '${name.toLowerCase()}' command`);
    this._setStr(a[0], a[2]);
    this.db.get(a[0]).expireAt = this.now() + (name === 'SETEX' ? n * 1000 : n);
    return OK;
  });
  def('GETSET', { min: 2, max: 2 }, function (a) { const p = this._str(a[0]); this._setStr(a[0], a[1]); return p; });
  def('GETDEL', { min: 1, max: 1 }, function (a) { const p = this._str(a[0]); if (p !== null) { this.db.delete(a[0]); this._touch(a[0]); } return p; });
  def('GETEX', { min: 1 }, function (a) {
    const p = this._str(a[0]);
    if (p === null) return null;
    const e = this.db.get(a[0]); const o = (a[1] || '').toUpperCase();
    if (o === 'PERSIST') e.expireAt = null;
    else if (o === 'EX') e.expireAt = this.now() + toInt(a[2]) * 1000;
    else if (o === 'PX') e.expireAt = this.now() + toInt(a[2]);
    else if (o) err(SYNTAX);
    return p;
  });
  def('MGET', { min: 1 }, function (a) { return a.map(k => { const e = this._get(k); return e && e.type === 'string' ? e.value : null; }); });
  def('MSET', { min: 2, even: true }, function (a) { for (let i = 0; i < a.length; i += 2) this._setStr(a[i], a[i + 1]); return OK; });
  def('MSETNX', { min: 2, even: true }, function (a) {
    for (let i = 0; i < a.length; i += 2) if (this._get(a[i])) return 0;
    for (let i = 0; i < a.length; i += 2) this._setStr(a[i], a[i + 1]);
    return 1;
  });
  def('INCR DECR INCRBY DECRBY', { min: 1, max: 2 }, function (a, name) {
    const by = name === 'INCR' ? 1 : name === 'DECR' ? -1 : (name === 'INCRBY' ? 1 : -1) * toInt(a[1] ?? err(`ERR wrong number of arguments for '${name.toLowerCase()}' command`));
    const cur = this._str(a[0]);
    const n = (cur === null ? 0 : toInt(cur)) + by;
    if (!Number.isSafeInteger(n)) err('ERR increment or decrement would overflow');
    this._setStr(a[0], n, true);
    return n;
  });
  def('INCRBYFLOAT', { min: 2, max: 2 }, function (a) {
    const cur = this._str(a[0]);
    const n = (cur === null ? 0 : toFloat(cur)) + toFloat(a[1]);
    const s = fmtFloat(n);
    this._setStr(a[0], s, true);
    return s;
  });
  def('APPEND', { min: 2, max: 2 }, function (a) { const v = (this._str(a[0]) ?? '') + a[1]; this._setStr(a[0], v, true); return v.length; });
  def('STRLEN', { min: 1, max: 1 }, function (a) { return (this._str(a[0]) ?? '').length; });
  def('GETRANGE', { min: 3, max: 3 }, function (a) {
    const s = this._str(a[0]) ?? ''; const n = s.length;
    let st = toInt(a[1]), en = toInt(a[2]);
    if (st < 0) st = Math.max(n + st, 0); if (en < 0) en = n + en; en = Math.min(en, n - 1);
    return st > en ? '' : s.slice(st, en + 1);
  });

  // bitmaps (stored as a string of '0'/'1' bits for clarity; BITCOUNT works on whole value)
  def('SETBIT', { min: 3, max: 3 }, function (a) {
    const off = toInt(a[1]); const bit = a[2];
    if (off < 0 || off > 2 ** 24) err('ERR bit offset is not an integer or out of range');
    if (bit !== '0' && bit !== '1') err('ERR bit is not an integer or out of range');
    const e = this._getOrMake(a[0], 'bitmap', () => []);
    const prev = e.value[off] ? 1 : 0;
    e.value[off] = bit === '1' ? 1 : 0;
    this._touch(a[0]);
    return prev;
  });
  def('GETBIT', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'bitmap'); return e && e.value[toInt(a[1])] ? 1 : 0; });
  def('BITCOUNT', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'bitmap'); return e ? e.value.reduce((s, b) => s + (b ? 1 : 0), 0) : 0; });
  def('BITOP', { min: 3 }, function (a) {
    const op = a[0].toUpperCase(), dest = a[1];
    const vs = a.slice(2).map(k => { const e = this._typed(k, 'bitmap'); return e ? e.value : []; });
    const len = Math.max(0, ...vs.map(v => v.length));
    const out = [];
    for (let i = 0; i < len; i++) {
      const bits = vs.map(v => (v[i] ? 1 : 0));
      out[i] = op === 'AND' ? bits.every(Boolean) | 0 : op === 'OR' ? bits.some(Boolean) | 0 : op === 'XOR' ? bits.reduce((x, y) => x ^ y, 0) : op === 'NOT' ? 1 - bits[0] : err(SYNTAX);
    }
    this.db.delete(dest);
    if (out.some(Boolean)) this._make(dest, 'bitmap', out);
    this._touch(dest);
    return Math.ceil(len / 8);
  });

  // HyperLogLog (exact under the hood; the lab notes Redis's ~0.81% error)
  def('PFADD', { min: 1 }, function (a) {
    const e = this._getOrMake(a[0], 'hyperloglog', () => new Set());
    const before = e.value.size;
    a.slice(1).forEach(x => e.value.add(x));
    this._touch(a[0]);
    return e.value.size !== before || (a.length === 1 && before === 0) ? 1 : 0;
  });
  def('PFCOUNT', { min: 1 }, function (a) {
    const u = new Set();
    a.forEach(k => { const e = this._typed(k, 'hyperloglog'); if (e) e.value.forEach(x => u.add(x)); });
    return u.size;
  });
  def('PFMERGE', { min: 1 }, function (a) {
    const u = new Set();
    a.forEach(k => { const e = this._typed(k, 'hyperloglog'); if (e) e.value.forEach(x => u.add(x)); });
    this._make(a[0], 'hyperloglog', u); this._touch(a[0]);
    return OK;
  });

  // hashes
  def('HSET HMSET', { min: 3, odd: true }, function (a, name) {
    const e = this._getOrMake(a[0], 'hash', () => new Map());
    let added = 0;
    for (let i = 1; i < a.length; i += 2) { if (!e.value.has(a[i])) added++; e.value.set(a[i], a[i + 1]); }
    this._touch(a[0]);
    return name === 'HMSET' ? OK : added;
  });
  def('HSETNX', { min: 3, max: 3 }, function (a) {
    const e = this._getOrMake(a[0], 'hash', () => new Map());
    if (e.value.has(a[1])) return 0;
    e.value.set(a[1], a[2]); this._touch(a[0]); return 1;
  });
  def('HGET', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? e.value.get(a[1]) ?? null : null; });
  def('HMGET', { min: 2 }, function (a) { const e = this._typed(a[0], 'hash'); return a.slice(1).map(f => (e ? e.value.get(f) ?? null : null)); });
  def('HGETALL', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? [...e.value].flat() : []; });
  def('HKEYS', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? [...e.value.keys()] : []; });
  def('HVALS', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? [...e.value.values()] : []; });
  def('HLEN', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? e.value.size : 0; });
  def('HEXISTS', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'hash'); return e && e.value.has(a[1]) ? 1 : 0; });
  def('HSTRLEN', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'hash'); return e ? (e.value.get(a[1]) ?? '').length : 0; });
  def('HDEL', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'hash');
    if (!e) return 0;
    let n = 0; a.slice(1).forEach(f => { if (e.value.delete(f)) n++; });
    this._cleanup(a[0]); this._touch(a[0]);
    return n;
  });
  def('HINCRBY', { min: 3, max: 3 }, function (a) {
    const e = this._getOrMake(a[0], 'hash', () => new Map());
    const cur = e.value.get(a[1]);
    if (cur !== undefined && !/^[+-]?\d+$/.test(cur)) err('ERR hash value is not an integer');
    const n = (cur === undefined ? 0 : Number(cur)) + toInt(a[2]);
    e.value.set(a[1], String(n)); this._touch(a[0]);
    return n;
  });
  def('HINCRBYFLOAT', { min: 3, max: 3 }, function (a) {
    const e = this._getOrMake(a[0], 'hash', () => new Map());
    const cur = e.value.get(a[1]);
    const n = (cur === undefined ? 0 : toFloat(cur)) + toFloat(a[2]);
    const s = fmtFloat(n); e.value.set(a[1], s); this._touch(a[0]);
    return s;
  });
  def('HSCAN', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'hash');
    const fields = e ? [...e.value.keys()] : [];
    const { next, page, match } = scanGeneric(fields, a, 2, 'hash');
    return [next, page.filter(f => !match || match.test(f)).flatMap(f => [f, e.value.get(f)])];
  });
  def('HRANDFIELD', { min: 1, max: 3 }, function (a) {
    const e = this._typed(a[0], 'hash');
    if (!e) return a.length > 1 ? [] : null;
    const fields = [...e.value.keys()];
    if (a.length === 1) return fields[Math.floor(Math.random() * fields.length)];
    const n = Math.min(toInt(a[1]), fields.length);
    const pick = fields.slice().sort(() => Math.random() - 0.5).slice(0, n);
    return (a[2] || '').toUpperCase() === 'WITHVALUES' ? pick.flatMap(f => [f, e.value.get(f)]) : pick;
  });

  // lists
  def('LPUSH RPUSH LPUSHX RPUSHX', { min: 2 }, function (a, name) {
    if (name.endsWith('X') && !this._typed(a[0], 'list')) return 0;
    const e = this._getOrMake(a[0], 'list', () => []);
    for (const v of a.slice(1)) name.startsWith('L') ? e.value.unshift(v) : e.value.push(v);
    this._touch(a[0]);
    return e.value.length;
  });
  def('LPOP RPOP', { min: 1, max: 2 }, function (a, name) {
    const e = this._typed(a[0], 'list');
    if (!e) return null;
    const take = () => (name === 'LPOP' ? e.value.shift() : e.value.pop());
    let out;
    if (a.length === 2) { const n = toInt(a[1]); out = []; for (let i = 0; i < n && e.value.length; i++) out.push(take()); }
    else out = take();
    this._cleanup(a[0]); this._touch(a[0]);
    return out;
  });
  def('LLEN', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'list'); return e ? e.value.length : 0; });
  def('LRANGE', { min: 3, max: 3 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) return [];
    const n = e.value.length; let s = toInt(a[1]), t = toInt(a[2]);
    if (s < 0) s = Math.max(n + s, 0); if (t < 0) t = n + t; t = Math.min(t, n - 1);
    return s > t ? [] : e.value.slice(s, t + 1);
  });
  def('LINDEX', { min: 2, max: 2 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) return null;
    let i = toInt(a[1]); if (i < 0) i += e.value.length;
    return e.value[i] ?? null;
  });
  def('LSET', { min: 3, max: 3 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) err('ERR no such key');
    let i = toInt(a[1]); if (i < 0) i += e.value.length;
    if (i < 0 || i >= e.value.length) err('ERR index out of range');
    e.value[i] = a[2]; this._touch(a[0]); return OK;
  });
  def('LTRIM', { min: 3, max: 3 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) return OK;
    const n = e.value.length; let s = toInt(a[1]), t = toInt(a[2]);
    if (s < 0) s = Math.max(n + s, 0); if (t < 0) t = n + t; t = Math.min(t, n - 1);
    e.value = s > t ? [] : e.value.slice(s, t + 1);
    this._cleanup(a[0]); this._touch(a[0]);
    return OK;
  });
  def('LREM', { min: 3, max: 3 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) return 0;
    let count = toInt(a[1]); const v = a[2]; let removed = 0;
    const idx = e.value.map((x, i) => (x === v ? i : -1)).filter(i => i >= 0);
    const pick = count > 0 ? idx.slice(0, count) : count < 0 ? idx.slice(count) : idx;
    const drop = new Set(pick); removed = drop.size;
    e.value = e.value.filter((_, i) => !drop.has(i));
    this._cleanup(a[0]); this._touch(a[0]);
    return removed;
  });
  def('LINSERT', { min: 4, max: 4 }, function (a) {
    const e = this._typed(a[0], 'list'); if (!e) return 0;
    const where = a[1].toUpperCase(); if (where !== 'BEFORE' && where !== 'AFTER') err(SYNTAX);
    const i = e.value.indexOf(a[2]); if (i < 0) return -1;
    e.value.splice(where === 'BEFORE' ? i : i + 1, 0, a[3]); this._touch(a[0]);
    return e.value.length;
  });
  def('LPOS', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'list'); const list = e ? e.value : [];
    let rank = 1, count = null;
    for (let i = 2; i < a.length; i++) {
      const o = a[i].toUpperCase();
      if (o === 'RANK') rank = toInt(a[++i]); else if (o === 'COUNT') count = toInt(a[++i]); else if (o === 'MAXLEN') i++; else err(SYNTAX);
    }
    let idx = list.map((x, i) => (x === a[1] ? i : -1)).filter(i => i >= 0);
    if (rank < 0) idx = idx.reverse();
    idx = idx.slice(Math.abs(rank) - 1);
    if (count === null) return idx.length ? idx[0] : null;
    return count === 0 ? idx : idx.slice(0, count);
  });
  def('LMOVE', { min: 4, max: 4 }, function (a) {
    const src = this._typed(a[0], 'list'); if (!src) return null;
    const from = a[2].toUpperCase(), to = a[3].toUpperCase();
    const v = from === 'LEFT' ? src.value.shift() : src.value.pop();
    this._cleanup(a[0]);
    const dst = this._getOrMake(a[1], 'list', () => []);
    to === 'LEFT' ? dst.value.unshift(v) : dst.value.push(v);
    this._touch(a[0]); this._touch(a[1]);
    return v;
  });
  def('RPOPLPUSH', { min: 2, max: 2 }, function (a) { return this.command(['LMOVE', a[0], a[1], 'RIGHT', 'LEFT']); });

  // sets
  def('SADD', { min: 2 }, function (a) {
    const e = this._getOrMake(a[0], 'set', () => new Set());
    let n = 0; a.slice(1).forEach(m => { if (!e.value.has(m)) { e.value.add(m); n++; } });
    this._touch(a[0]); return n;
  });
  def('SREM', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'set'); if (!e) return 0;
    let n = 0; a.slice(1).forEach(m => { if (e.value.delete(m)) n++; });
    this._cleanup(a[0]); this._touch(a[0]); return n;
  });
  def('SMEMBERS', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'set'); return e ? sortedMembers(e.value) : []; });
  def('SISMEMBER', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'set'); return e && e.value.has(a[1]) ? 1 : 0; });
  def('SMISMEMBER', { min: 2 }, function (a) { const e = this._typed(a[0], 'set'); return a.slice(1).map(m => (e && e.value.has(m) ? 1 : 0)); });
  def('SCARD', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'set'); return e ? e.value.size : 0; });
  def('SINTER', { min: 1 }, function (a) { return sortedMembers(setOp(this, a, 'inter')); });
  def('SUNION', { min: 1 }, function (a) { return sortedMembers(setOp(this, a, 'union')); });
  def('SDIFF', { min: 1 }, function (a) { return sortedMembers(setOp(this, a, 'diff')); });
  def('SINTERSTORE', { min: 2 }, function (a) { return storeSet(this, a[0], setOp(this, a.slice(1), 'inter')); });
  def('SUNIONSTORE', { min: 2 }, function (a) { return storeSet(this, a[0], setOp(this, a.slice(1), 'union')); });
  def('SDIFFSTORE', { min: 2 }, function (a) { return storeSet(this, a[0], setOp(this, a.slice(1), 'diff')); });
  def('SINTERCARD', { min: 2 }, function (a) {
    const n = toInt(a[0]); const keys = a.slice(1, 1 + n);
    let limit = 0; if ((a[1 + n] || '').toUpperCase() === 'LIMIT') limit = toInt(a[2 + n]);
    const size = setOp(this, keys, 'inter').size;
    return limit ? Math.min(limit, size) : size;
  });
  def('SPOP', { min: 1, max: 2 }, function (a) {
    const e = this._typed(a[0], 'set'); if (!e) return a.length > 1 ? [] : null;
    const pickOne = () => { const arr = [...e.value]; const m = arr[Math.floor(Math.random() * arr.length)]; e.value.delete(m); return m; };
    const out = a.length > 1 ? Array.from({ length: Math.min(toInt(a[1]), e.value.size) }, pickOne) : pickOne();
    this._cleanup(a[0]); this._touch(a[0]); return out;
  });
  def('SRANDMEMBER', { min: 1, max: 2 }, function (a) {
    const e = this._typed(a[0], 'set'); const arr = e ? [...e.value] : [];
    if (a.length === 1) return arr.length ? arr[Math.floor(Math.random() * arr.length)] : null;
    const n = toInt(a[1]);
    if (n >= 0) return arr.slice().sort(() => Math.random() - 0.5).slice(0, n);
    return Array.from({ length: -n }, () => arr[Math.floor(Math.random() * arr.length)]).filter(x => x !== undefined);
  });
  def('SMOVE', { min: 3, max: 3 }, function (a) {
    const src = this._typed(a[0], 'set'); if (!src || !src.value.has(a[2])) return 0;
    this._typed(a[1], 'set');
    src.value.delete(a[2]); this._cleanup(a[0]);
    this._getOrMake(a[1], 'set', () => new Set()).value.add(a[2]);
    this._touch(a[0]); this._touch(a[1]); return 1;
  });
  def('SSCAN', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'set');
    const { next, page, match } = scanGeneric(e ? sortedMembers(e.value) : [], a, 2, 'set');
    return [next, page.filter(m => !match || match.test(m))];
  });

  // sorted sets
  def('ZADD', { min: 3 }, function (a) {
    let i = 1; const f = {};
    while (i < a.length && ['NX', 'XX', 'GT', 'LT', 'CH', 'INCR'].includes(a[i].toUpperCase())) f[a[i++].toUpperCase()] = true;
    const pairs = a.slice(i);
    if (!pairs.length || pairs.length % 2) err(SYNTAX);
    if (f.NX && (f.XX || f.GT || f.LT)) err('ERR XX and NX options at the same time are not compatible');
    if (f.INCR && pairs.length !== 2) err('ERR INCR option supports a single increment-element pair');
    const scores = pairs.filter((_, j) => j % 2 === 0).map(toFloat);
    const exists = this._typed(a[0], 'zset');
    if (!exists && f.XX) return f.INCR ? null : 0;
    const e = exists || this._make(a[0], 'zset', new Map());
    let added = 0, changed = 0, incrResult = null;
    for (let j = 0; j < pairs.length; j += 2) {
      const m = pairs[j + 1]; const has = e.value.has(m); const old = e.value.get(m);
      let s = scores[j / 2];
      if (f.INCR) s = (has ? old : 0) + s;
      if ((f.NX && has) || (f.XX && !has)) { if (f.INCR) incrResult = null; continue; }
      if (has && ((f.GT && s <= old) || (f.LT && s >= old))) { if (f.INCR) incrResult = null; continue; }
      if (!has) added++; else if (old !== s) changed++;
      e.value.set(m, s); if (f.INCR) incrResult = fmtFloat(s);
    }
    this._cleanup(a[0]); this._touch(a[0]);
    return f.INCR ? incrResult : f.CH ? added + changed : added;
  });
  def('ZINCRBY', { min: 3, max: 3 }, function (a) {
    const e = this._getOrMake(a[0], 'zset', () => new Map());
    const s = (e.value.get(a[2]) ?? 0) + toFloat(a[1]);
    e.value.set(a[2], s); this._touch(a[0]); return fmtFloat(s);
  });
  def('ZSCORE', { min: 2, max: 2 }, function (a) { const e = this._typed(a[0], 'zset'); const s = e && e.value.get(a[1]); return s === undefined || s === null || s === false ? null : fmtFloat(s); });
  def('ZMSCORE', { min: 2 }, function (a) { const e = this._typed(a[0], 'zset'); return a.slice(1).map(m => (e && e.value.has(m) ? fmtFloat(e.value.get(m)) : null)); });
  def('ZCARD', { min: 1, max: 1 }, function (a) { const e = this._typed(a[0], 'zset'); return e ? e.value.size : 0; });
  def('ZREM', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'zset'); if (!e) return 0;
    let n = 0; a.slice(1).forEach(m => { if (e.value.delete(m)) n++; });
    this._cleanup(a[0]); this._touch(a[0]); return n;
  });
  def('ZCOUNT', { min: 3, max: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], { byScore: true }).length; });
  def('ZLEXCOUNT', { min: 3, max: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], { byLex: true }).length; });
  def('ZRANGE', { min: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], parseZrangeOpts(a, 3, {})); });
  def('ZREVRANGE', { min: 3, max: 4 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], parseZrangeOpts(a, 3, { rev: true })); });
  def('ZRANGEBYSCORE', { min: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], parseZrangeOpts(a, 3, { byScore: true })); });
  def('ZREVRANGEBYSCORE', { min: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], parseZrangeOpts(a, 3, { byScore: true, rev: true })); });
  def('ZRANGEBYLEX', { min: 3 }, function (a) { return zrangeGeneric(this, a[0], a[1], a[2], parseZrangeOpts(a, 3, { byLex: true })); });
  def('ZRANK ZREVRANK', { min: 2, max: 3 }, function (a, name) {
    const e = this._typed(a[0], 'zset'); if (!e || !e.value.has(a[1])) return null;
    const order = [...e.value.entries()].map(([member, score]) => ({ member, score })).sort(zcmp);
    if (name === 'ZREVRANK') order.reverse();
    const r = order.findIndex(x => x.member === a[1]);
    return (a[2] || '').toUpperCase() === 'WITHSCORE' ? [r, fmtFloat(e.value.get(a[1]))] : r;
  });
  def('ZREMRANGEBYRANK', { min: 3, max: 3 }, function (a) {
    const doomed = zrangeGeneric(this, a[0], a[1], a[2], {});
    const e = this._typed(a[0], 'zset'); doomed.forEach(m => e.value.delete(m));
    if (e) { this._cleanup(a[0]); this._touch(a[0]); }
    return doomed.length;
  });
  def('ZREMRANGEBYSCORE', { min: 3, max: 3 }, function (a) {
    const doomed = zrangeGeneric(this, a[0], a[1], a[2], { byScore: true });
    const e = this._typed(a[0], 'zset'); doomed.forEach(m => e.value.delete(m));
    if (e) { this._cleanup(a[0]); this._touch(a[0]); }
    return doomed.length;
  });
  def('ZPOPMIN ZPOPMAX', { min: 1, max: 2 }, function (a, name) {
    const e = this._typed(a[0], 'zset'); if (!e) return [];
    const n = a.length > 1 ? toInt(a[1]) : 1;
    const order = [...e.value.entries()].map(([member, score]) => ({ member, score })).sort(zcmp);
    if (name === 'ZPOPMAX') order.reverse();
    const out = order.slice(0, n);
    out.forEach(x => e.value.delete(x.member));
    this._cleanup(a[0]); this._touch(a[0]);
    return out.flatMap(x => [x.member, fmtFloat(x.score)]);
  });
  def('ZUNIONSTORE', { min: 3 }, function (a) { return zstore(this, a, 'union'); });
  def('ZINTERSTORE', { min: 3 }, function (a) { return zstore(this, a, 'inter'); });
  def('ZSCAN', { min: 2 }, function (a) {
    const e = this._typed(a[0], 'zset');
    const members = e ? [...e.value.entries()].map(([member, score]) => ({ member, score })).sort(zcmp).map(x => x.member) : [];
    const { next, page, match } = scanGeneric(members, a, 2, 'zset');
    return [next, page.filter(m => !match || match.test(m)).flatMap(m => [m, fmtFloat(e.value.get(m))])];
  });

  // geo (members live in a sorted set, like Redis; coordinates kept alongside)
  def('GEOADD', { min: 4 }, function (a) {
    let i = 1; const f = {};
    while (['NX', 'XX', 'CH'].includes((a[i] || '').toUpperCase())) f[a[i++].toUpperCase()] = true;
    const rest = a.slice(i); if (!rest.length || rest.length % 3) err(SYNTAX);
    const e = this._getOrMake(a[0], 'zset', () => new Map());
    e.geo ??= new Map();
    let added = 0;
    for (let j = 0; j < rest.length; j += 3) {
      const lon = toFloat(rest[j]), lat = toFloat(rest[j + 1]), m = rest[j + 2];
      if (lon < -180 || lon > 180 || lat < -85.05112878 || lat > 85.05112878) err(`ERR invalid longitude,latitude pair ${rest[j]},${rest[j + 1]}`);
      const has = e.value.has(m);
      if ((f.NX && has) || (f.XX && !has)) continue;
      if (!has) added++;
      // score: a stable 52-bit-ish interleave stand-in (real Redis uses geohash); ordering only
      e.value.set(m, Math.round((lat + 90) * 1e6) * 1e3 + Math.round((lon + 180) * 1e2));
      e.geo.set(m, [lon, lat]);
    }
    this._touch(a[0]);
    return added;
  });
  def('GEOPOS', { min: 1 }, function (a) {
    const e = this._typed(a[0], 'zset');
    return a.slice(1).map(m => { const p = e && e.geo && e.geo.get(m); return p ? [p[0].toFixed(6), p[1].toFixed(6)] : null; });
  });
  def('GEODIST', { min: 3, max: 4 }, function (a) {
    const e = this._typed(a[0], 'zset');
    const p = e && e.geo && e.geo.get(a[1]), q = e && e.geo && e.geo.get(a[2]);
    if (!p || !q) return null;
    const unit = (a[3] || 'm').toLowerCase(); if (!UNIT[unit]) err('ERR unsupported unit provided. please use M, KM, FT, MI');
    return (haversine(p[0], p[1], q[0], q[1]) / UNIT[unit]).toFixed(4);
  });
  def('GEOSEARCH', { min: 4 }, function (a) {
    const e = this._typed(a[0], 'zset');
    let center = null, radius = null, box = null, unit = 'm', order = null, count = null, withDist = false, withCoord = false;
    for (let i = 1; i < a.length; i++) {
      const o = a[i].toUpperCase();
      if (o === 'FROMMEMBER') { const p = e && e.geo && e.geo.get(a[++i]); if (!p) err('ERR could not decode requested zset member'); center = p; }
      else if (o === 'FROMLONLAT') { center = [toFloat(a[++i]), toFloat(a[++i])]; }
      else if (o === 'BYRADIUS') { radius = toFloat(a[++i]); unit = a[++i].toLowerCase(); }
      else if (o === 'BYBOX') { box = [toFloat(a[++i]), toFloat(a[++i])]; unit = a[++i].toLowerCase(); }
      else if (o === 'ASC' || o === 'DESC') order = o;
      else if (o === 'COUNT') { count = toInt(a[++i]); if ((a[i + 1] || '').toUpperCase() === 'ANY') i++; }
      else if (o === 'WITHDIST') withDist = true;
      else if (o === 'WITHCOORD') withCoord = true;
      else if (o === 'WITHHASH') { /* not meaningful here */ }
      else err(SYNTAX);
    }
    if (!center || (radius == null && !box)) err('ERR exactly one of FROMMEMBER or FROMLONLAT can be specified for GEOSEARCH');
    if (!UNIT[unit]) err('ERR unsupported unit provided. please use M, KM, FT, MI');
    if (!e || !e.geo) return [];
    let hits = [...e.geo].map(([m, p]) => ({ m, p, d: haversine(center[0], center[1], p[0], p[1]) / UNIT[unit] }));
    hits = hits.filter(h => (radius != null ? h.d <= radius
      : haversine(center[0], center[1], h.p[0], center[1]) / UNIT[unit] <= box[0] / 2 && haversine(center[0], center[1], center[0], h.p[1]) / UNIT[unit] <= box[1] / 2));
    if (order === 'ASC' || (count != null && !order)) hits.sort((x, y) => x.d - y.d);
    if (order === 'DESC') hits.sort((x, y) => y.d - x.d);
    if (count != null) hits = hits.slice(0, count);
    if (!withDist && !withCoord) return hits.map(h => h.m);
    return hits.map(h => [h.m, ...(withDist ? [h.d.toFixed(4)] : []), ...(withCoord ? [[h.p[0].toFixed(6), h.p[1].toFixed(6)]] : [])]);
  });

  // streams
  def('XADD', { min: 4 }, function (a) {
    let i = 1, maxlen = null, nomk = false;
    for (;;) {
      const o = (a[i] || '').toUpperCase();
      if (o === 'NOMKSTREAM') { nomk = true; i++; }
      else if (o === 'MAXLEN') { i++; if (a[i] === '~' || a[i] === '=') i++; maxlen = toInt(a[i++]); }
      else break;
    }
    const idArg = a[i++]; const fields = a.slice(i);
    if (!fields.length || fields.length % 2) err(`ERR wrong number of arguments for 'xadd' command`);
    const s = streamOf(this, a[0], !nomk); if (!s) return null;
    let id;
    if (idArg === '*') {
      const ms = Math.max(this.now(), s.last[0]);
      id = [ms, ms === s.last[0] ? s.last[1] + 1 : 0];
    } else if (/^\d+-\*$/.test(idArg)) {
      const ms = Number(idArg.split('-')[0]);
      id = [ms, ms === s.last[0] ? s.last[1] + 1 : 0];
    } else id = parseId(idArg);
    if (idCmp(id, s.last) <= 0) err('ERR The ID specified in XADD is equal or smaller than the target stream top item');
    s.entries.push({ id, fields }); s.last = id;
    if (maxlen != null && s.entries.length > maxlen) s.entries.splice(0, s.entries.length - maxlen);
    this._touch(a[0]);
    return idStr(id);
  });
  def('XLEN', { min: 1, max: 1 }, function (a) { const s = streamOf(this, a[0]); return s ? s.entries.length : 0; });
  def('XRANGE XREVRANGE', { min: 3, max: 5 }, function (a, name) {
    const s = streamOf(this, a[0]); if (!s) return [];
    let [lo, hi] = name === 'XRANGE' ? [a[1], a[2]] : [a[2], a[1]];
    const ex = v => String(v).startsWith('(');
    const L = parseId(ex(lo) ? lo.slice(1) : lo, 0), H = parseId(ex(hi) ? hi.slice(1) : hi, Number.MAX_SAFE_INTEGER);
    let out = s.entries.filter(e => (ex(lo) ? idCmp(e.id, L) > 0 : idCmp(e.id, L) >= 0) && (ex(hi) ? idCmp(e.id, H) < 0 : idCmp(e.id, H) <= 0));
    if (name === 'XREVRANGE') out = out.reverse();
    if ((a[3] || '').toUpperCase() === 'COUNT') out = out.slice(0, toInt(a[4]));
    return out.map(entryReply);
  });
  def('XDEL', { min: 2 }, function (a) {
    const s = streamOf(this, a[0]); if (!s) return 0;
    const ids = new Set(a.slice(1).map(x => idStr(parseId(x))));
    const before = s.entries.length;
    s.entries = s.entries.filter(e => !ids.has(idStr(e.id)));
    this._touch(a[0]); return before - s.entries.length;
  });
  def('XTRIM', { min: 3 }, function (a) {
    const s = streamOf(this, a[0]); if (!s) return 0;
    let i = 1; const strat = a[i++].toUpperCase(); if (a[i] === '~' || a[i] === '=') i++;
    const before = s.entries.length;
    if (strat === 'MAXLEN') { const n = toInt(a[i]); if (s.entries.length > n) s.entries.splice(0, s.entries.length - n); }
    else if (strat === 'MINID') { const m = parseId(a[i]); s.entries = s.entries.filter(e => idCmp(e.id, m) >= 0); }
    else err(SYNTAX);
    this._touch(a[0]); return before - s.entries.length;
  });
  def('XREAD', { min: 3 }, function (a) {
    let i = 0, count = null;
    while (i < a.length && a[i].toUpperCase() !== 'STREAMS') {
      const o = a[i].toUpperCase();
      if (o === 'COUNT') { count = toInt(a[i + 1]); i += 2; } else if (o === 'BLOCK') i += 2; else err(SYNTAX);
    }
    const rest = a.slice(i + 1); if (!rest.length || rest.length % 2) err("ERR Unbalanced 'xread' list of streams: for each stream key an ID or '$' must be specified.");
    const half = rest.length / 2; const out = [];
    for (let j = 0; j < half; j++) {
      const s = streamOf(this, rest[j]); if (!s) continue;
      const from = rest[half + j] === '$' ? s.last : parseId(rest[half + j]);
      let es = s.entries.filter(e => idCmp(e.id, from) > 0);
      if (count != null) es = es.slice(0, count);
      if (es.length) out.push([rest[j], es.map(entryReply)]);
    }
    return out.length ? out : null;
  });
  def('XGROUP', { min: 2 }, function (a) {
    const sub = a[0].toUpperCase();
    if (sub === 'CREATE') {
      const mk = a.slice(4).some(x => x.toUpperCase() === 'MKSTREAM');
      const s = streamOf(this, a[1], mk);
      if (!s) err('ERR The XGROUP subcommand requires the key to exist. Note that for CREATE you may want to use the MKSTREAM option to create an empty stream automatically.');
      if (s.groups.has(a[2])) err('BUSYGROUP Consumer Group name already exists');
      s.groups.set(a[2], { last: a[3] === '$' ? s.last : parseId(a[3]), pending: new Map(), consumers: new Set() });
      return OK;
    }
    if (sub === 'DESTROY') { const s = streamOf(this, a[1]); return s && s.groups.delete(a[2]) ? 1 : 0; }
    if (sub === 'SETID') { const g = streamOf(this, a[1])?.groups.get(a[2]); if (!g) err('NOGROUP No such consumer group'); g.last = a[3] === '$' ? streamOf(this, a[1]).last : parseId(a[3]); return OK; }
    err(`ERR unknown subcommand '${a[0]}'`);
  });
  def('XREADGROUP', { min: 6 }, function (a) {
    if (a[0].toUpperCase() !== 'GROUP') err(SYNTAX);
    const group = a[1], consumer = a[2];
    let i = 3, count = null;
    while (i < a.length && a[i].toUpperCase() !== 'STREAMS') {
      const o = a[i].toUpperCase();
      if (o === 'COUNT') { count = toInt(a[i + 1]); i += 2; } else if (o === 'BLOCK') i += 2; else if (o === 'NOACK') i++; else err(SYNTAX);
    }
    const rest = a.slice(i + 1); const half = rest.length / 2; const out = [];
    for (let j = 0; j < half; j++) {
      const s = streamOf(this, rest[j]);
      const g = s && s.groups.get(group);
      if (!g) err(`NOGROUP No such key '${rest[j]}' or consumer group '${group}' in XREADGROUP with GROUP option`);
      g.consumers.add(consumer);
      let es;
      if (rest[half + j] === '>') {
        es = s.entries.filter(e => idCmp(e.id, g.last) > 0);
        if (count != null) es = es.slice(0, count);
        es.forEach(e => { g.pending.set(idStr(e.id), { consumer, deliveries: 1, at: this.now() }); });
        if (es.length) g.last = es[es.length - 1].id;
      } else {
        const from = parseId(rest[half + j]);
        es = s.entries.filter(e => idCmp(e.id, from) > 0 && g.pending.get(idStr(e.id))?.consumer === consumer);
        if (count != null) es = es.slice(0, count);
      }
      out.push([rest[j], es.map(entryReply)]);
    }
    this._touch(rest[0]);
    return out.some(x => x[1].length) ? out : null;
  });
  def('XACK', { min: 3 }, function (a) {
    const g = streamOf(this, a[0])?.groups.get(a[1]); if (!g) return 0;
    let n = 0; a.slice(2).forEach(id => { if (g.pending.delete(idStr(parseId(id)))) n++; });
    return n;
  });
  def('XPENDING', { min: 2 }, function (a) {
    const g = streamOf(this, a[0])?.groups.get(a[1]);
    if (!g) err(`NOGROUP No such key '${a[0]}' or consumer group '${a[1]}'`);
    const ids = [...g.pending.keys()].sort((x, y) => idCmp(parseId(x), parseId(y)));
    if (a.length === 2) {
      if (!ids.length) return [0, null, null, null];
      const per = {}; g.pending.forEach(p => { per[p.consumer] = (per[p.consumer] || 0) + 1; });
      return [ids.length, ids[0], ids[ids.length - 1], Object.entries(per).map(([c, n]) => [c, String(n)])];
    }
    const lo = parseId(a[2], 0), hi = parseId(a[3], Number.MAX_SAFE_INTEGER), cnt = toInt(a[4] ?? '10');
    return ids.filter(x => idCmp(parseId(x), lo) >= 0 && idCmp(parseId(x), hi) <= 0)
      .filter(x => !a[5] || g.pending.get(x).consumer === a[5]).slice(0, cnt)
      .map(x => { const p = g.pending.get(x); return [x, p.consumer, this.now() - p.at, p.deliveries]; });
  });
  def('XCLAIM', { min: 5 }, function (a) {
    const s = streamOf(this, a[0]); const g = s?.groups.get(a[1]); if (!g) err('NOGROUP No such consumer group');
    const minIdle = toInt(a[3]); const out = [];
    for (const raw of a.slice(4)) {
      if (/^[A-Z]+$/i.test(raw)) break;
      const k = idStr(parseId(raw)); const p = g.pending.get(k);
      if (p && this.now() - p.at >= minIdle) {
        g.pending.set(k, { consumer: a[2], deliveries: p.deliveries + 1, at: this.now() });
        const e = s.entries.find(x => idStr(x.id) === k); if (e) out.push(entryReply(e));
      }
    }
    return out;
  });

  // transactions
  def('MULTI', { max: 0 }, function () { if (this.tx) err('ERR MULTI calls can not be nested'); this.tx = []; this.txError = false; return OK; });
  def('DISCARD', { max: 0 }, function () { if (!this.tx) err('ERR DISCARD without MULTI'); this.tx = null; this.watched = null; return OK; });
  def('WATCH', { min: 1 }, function (a) {
    if (this.tx) err('ERR WATCH inside MULTI is not allowed');
    this.watched ??= new Map();
    a.forEach(k => { this._get(k); this.watched.set(k, this.versions.get(k) || 0); });
    return OK;
  });
  def('UNWATCH', { max: 0 }, function () { this.watched = null; return OK; });
  def('EXEC', { max: 0 }, function () {
    if (!this.tx) err('ERR EXEC without MULTI');
    const queued = this.tx; this.tx = null;
    if (this.txError) { this.txError = false; this.watched = null; err('EXECABORT Transaction discarded because of previous errors.'); }
    const dirty = this.watched && [...this.watched].some(([k, v]) => { this._get(k); return (this.versions.get(k) || 0) !== v; });
    this.watched = null;
    if (dirty) return null;
    return queued.map(argv => { try { return this.command(argv); } catch (e) { if (e instanceof RedisError) return new RedisError(e.message); throw e; } });
  });

  const COMMANDS = C;

  /* --------------------------------------------------- redis-cli format -- */
  function format(reply, indent = '') {
    if (reply instanceof RedisError) return `(error) ${reply.message}`;
    if (reply instanceof Status) return reply.s;
    if (reply === null || reply === undefined) return '(nil)';
    if (typeof reply === 'number') return `(integer) ${reply}`;
    if (typeof reply === 'string') return JSON.stringify(reply);
    if (Array.isArray(reply)) {
      if (!reply.length) return '(empty array)';
      const w = String(reply.length).length;
      return reply.map((r, i) => {
        const label = `${String(i + 1).padStart(w)}) `;
        const body = format(r, indent + ' '.repeat(label.length));
        return (i ? indent : '') + label + body;
      }).join('\n');
    }
    return String(reply);
  }

  // Run a multi-line script: one reply per non-empty, non-comment line.
  function runScript(redis, text) {
    const out = [];
    for (const raw of text.split('\n')) {
      const line = raw.trim();
      if (!line || line.startsWith('#') || line.startsWith('//')) continue;
      const cmd = line.replace(/^(127\.0\.0\.1:\d+>|redis>|>)\s*/, '');
      try { out.push({ cmd, reply: redis.exec(cmd), ok: true }); }
      catch (e) {
        if (!(e instanceof RedisError)) throw e;
        out.push({ cmd, reply: e, ok: false });
      }
    }
    return out;
  }

  const api = { MiniRedis, RedisError, Status, format, tokenize, runScript, COMMANDS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.QLabRedis = api;
})(typeof window !== 'undefined' ? window : globalThis);
