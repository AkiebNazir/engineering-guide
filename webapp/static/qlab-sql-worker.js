/* ============================================================================
   Query Lab — PGlite in a dedicated Web Worker (module worker).

   PGlite runs PostgreSQL synchronously inside WebAssembly and ignores
   statement_timeout, so a query that never ends (a recursive CTE with no
   termination condition) would freeze the page if it ran on the main thread.
   Here it only blocks this worker; qlab.js can terminate() the worker and start
   a fresh one (sqlStop in qlab.js).

   Protocol (one request at a time; qlab.js serialises them):
     → { id, op: 'exec',  sql }            ← { id, ok: true, result: Results[] }
     → { id, op: 'query', sql, params }    ← { id, ok: true, result: Results }
     → { id, op: 'inTxn' }                 ← { id, ok: true, result: boolean }
     any failure                           ← { id, ok: false, error: { message, position, code, … } }
   On start-up it posts { ready: true }, or { ready: false, error } if PGlite failed to boot.
   ========================================================================= */
import { PGlite } from './vendor/pglite/0.5.8/index.js';

const boot = PGlite.create();

// DatabaseError carries position / code / detail / hint as own properties; a
// structured clone of an Error would keep only its message, so copy them over.
function plainError(e) {
  const out = { message: e && e.message ? e.message : String(e), name: e && e.name ? e.name : 'Error' };
  if (e && typeof e === 'object') {
    for (const [k, v] of Object.entries(e)) {
      if (v == null || typeof v === 'function' || typeof v === 'object') continue;
      out[k] = v;
    }
  }
  return out;
}

boot.then(() => postMessage({ ready: true }), e => postMessage({ ready: false, error: plainError(e) }));

onmessage = async ({ data: m }) => {
  try {
    const db = await boot;
    let result;
    if (m.op === 'exec') result = await db.exec(m.sql);
    else if (m.op === 'query') result = await db.query(m.sql, m.params || []);
    else if (m.op === 'inTxn') result = await db.isInTransaction();
    else throw new Error(`Unknown op ${m.op}`);
    postMessage({ id: m.id, ok: true, result });
  } catch (e) {
    postMessage({ id: m.id, ok: false, error: plainError(e) });
  }
};
