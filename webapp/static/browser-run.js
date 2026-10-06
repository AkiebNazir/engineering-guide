/* ============================================================================
   Running code without the local server — used by the static build only
   (GitHub Pages and other static hosts; see staticPost in app.js).

     Python  Pyodide (CPython in WebAssembly) in a Web Worker: py-worker.js.
             The runtime (~10 MB) downloads from the jsDelivr CDN on the first
             run, then stays cached by the browser.
     Go      The official Go Playground (play.golang.org), which accepts
             cross-origin requests. The code is compiled and run on Google's
             servers; the Playground clock is simulated, so time.Since() and
             time.Now() do not measure real time there.

   Every runner resolves to the same shape the server's /api/run returns:
     { ok, stdout, stderr, exitCode, ms, timeout?, via }
   ========================================================================= */
window.BrowserRun = (() => {
  const GO_PLAYGROUND = 'https://play.golang.org';
  const PY_TIMEOUT_S = 15;      // same budget as server.py RUN_TIMEOUT_PY
  const GO_TIMEOUT_S = 40;      //                         RUN_TIMEOUT_GO
  const BOOT_TIMEOUT_S = 120;   // first run on a slow mobile connection

  const fail = (stderr, extra = {}) =>
    ({ ok: false, stdout: '', stderr, exitCode: -1, ms: 0, ...extra });

  /* ---------------------------------------------------------- Python -- */
  let worker = null;
  let pyReady = false;
  let seq = 0;
  let queue = Promise.resolve();

  const freshWorker = () => {
    if (worker) worker.terminate();
    worker = new Worker(assetUrl('./py-worker.js'));
    pyReady = false;
  };

  const runPyOnce = (code, timeoutS) => new Promise(resolve => {
    if (!worker) freshWorker();
    const w = worker, id = ++seq;
    let timer = null;
    const finish = r => {
      clearTimeout(timer);
      w.removeEventListener('message', onMsg);
      w.removeEventListener('error', onErr);
      resolve({ ...r, via: 'in browser' });
    };
    const kill = r => { if (worker === w) { w.terminate(); worker = null; pyReady = false; } finish(r); };
    const onMsg = ({ data: m }) => {
      if (m.id !== id) return;
      if (m.bootError) {
        kill(fail(`Could not load the Python runtime (Pyodide): ${m.bootError}\n` +
                  'Check the internet connection and run again.'));
      } else if (m.started) {
        pyReady = true;
        clearTimeout(timer);
        timer = setTimeout(() => kill(fail(
          `Timed out after ${timeoutS}s — likely an infinite loop or runaway recursion.`,
          { timeout: true, ms: timeoutS * 1000 })), timeoutS * 1000);
      } else {
        const { id: _, fatal, ...r } = m;
        if (fatal) kill(r); else finish(r);
      }
    };
    const onErr = e => {
      e.preventDefault?.();
      kill(fail(`The Python runtime failed to start: ${e.message || 'network error'}\n` +
                'Check the internet connection and run again.'));
    };
    w.addEventListener('message', onMsg);
    w.addEventListener('error', onErr);
    timer = setTimeout(() => kill(fail(
      `The Python runtime did not load within ${BOOT_TIMEOUT_S}s. Check the connection and run again.`)),
      BOOT_TIMEOUT_S * 1000);
    w.postMessage({ id, code });
  });

  // One run at a time, like the server's subprocess per request.
  const python = (code, timeoutS = PY_TIMEOUT_S) => {
    const p = queue.then(() => runPyOnce(code, timeoutS));
    queue = p.catch(() => {});
    return p;
  };

  /* -------------------------------------------------------------- Go -- */
  const playground = async (path, params, timeoutS) => {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), timeoutS * 1000);
    try {
      const r = await fetch(GO_PLAYGROUND + path, {
        method: 'POST', body: new URLSearchParams(params), signal: ctl.signal,
      });
      if (!r.ok) throw new Error(`Go Playground answered ${r.status}`);
      return await r.json();
    } finally {
      clearTimeout(timer);
    }
  };
  // The Playground names the file prog.go; the server and the editor call it main.go.
  const renameFile = s => (s || '').replaceAll('prog.go', 'main.go');

  const go = async (code, timeoutS = GO_TIMEOUT_S) => {
    const t0 = performance.now();
    try {
      const j = await playground('/compile', { version: '2', body: code }, timeoutS);
      const ms = Math.round(performance.now() - t0);
      if (j.Errors) {
        return { ok: false, stdout: '', stderr: renameFile(j.Errors), exitCode: 2, ms, via: 'Go Playground' };
      }
      let stdout = '', stderr = '';
      for (const ev of j.Events || []) {
        if (ev.Kind === 'stderr') stderr += ev.Message; else stdout += ev.Message;
      }
      const exitCode = j.Status || 0;
      return { ok: exitCode === 0, stdout, stderr: renameFile(stderr), exitCode, ms, via: 'Go Playground' };
    } catch (e) {
      return e.name === 'AbortError'
        ? fail(`Timed out after ${timeoutS}s waiting for the Go Playground.`,
               { timeout: true, ms: timeoutS * 1000, via: 'Go Playground' })
        : fail(`Could not reach the Go Playground (${e.message}). Check the internet connection and run again.`,
               { via: 'Go Playground' });
    }
  };

  const gofmt = async code => {
    try {
      const j = await playground('/fmt', { body: code }, 20);
      return j.Error ? { ok: false, code, error: renameFile(j.Error) } : { ok: true, code: j.Body };
    } catch (e) {
      return { ok: false, code, error: `Could not reach the Go Playground (${e.message}).` };
    }
  };

  /* Get ready for a Run while the learner reads: start Python (downloads the runtime
     the first time, then boots from the browser cache in a second or two), or open
     the connection to the Go Playground. Skipped on data-saver or 2G connections,
     where a 10 MB download nobody asked for would hurt. */
  const slowLink = () => {
    const c = navigator.connection;
    return !!c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ''));
  };
  let preconnected = false;
  const warm = lang => {
    if (lang === 'py') {
      if (worker || slowLink()) return;
      (window.requestIdleCallback || (cb => setTimeout(cb, 1500)))(() => { if (!worker) freshWorker(); }, { timeout: 5000 });
    } else if (!preconnected) {
      preconnected = true;
      const l = document.createElement('link');
      l.rel = 'preconnect';
      l.href = GO_PLAYGROUND;
      l.crossOrigin = 'anonymous';
      document.head.append(l);
    }
  };

  return { python, go, gofmt, warm, isPythonReady: () => pyReady };
})();
