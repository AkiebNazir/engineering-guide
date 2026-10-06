/* ============================================================================
   Python runner for the static site — Pyodide (CPython compiled to WebAssembly)
   in a dedicated Web Worker. Only browser-run.js uses it, and only when the app
   is a static build (GitHub Pages etc.), where there is no server to run code.

   A run that never ends (an infinite loop, runaway recursion) blocks this
   worker, not the page: browser-run.js terminates the worker on timeout and
   starts a fresh one for the next run.

   Protocol (one run at a time; browser-run.js serialises them):
     → { id, code }
     ← { id, started: true }                              boot done, code about to run
     ← { id, ok, stdout, stderr, exitCode, ms }           the run finished
     ← { id, bootError }                                  Pyodide could not load
   ========================================================================= */
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
// Same shape as `python main.py` on the server: a real __main__ module (so
// sys.modules[__name__] works), source lines in tracebacks, and SystemExit turned
// into an exit code. Two browser limits are papered over before user code runs:
//
//   * Timers are coarsened to ~0.1 ms (a Spectre mitigation), so two clock reads can
//     be equal and a benchmark's `slow / fast` divides by zero. The clocks are made
//     strictly increasing.
//
//   * WebAssembly runs on the browser's native stack, and a worker gets little of it
//     (~0.5 MB in Chrome). Pure-Python recursion is unaffected (CPython 3.13 keeps it
//     on the heap), but recursion that passes through C — @functools.cache, __repr__,
//     map(), freeing a long linked list node by node — is bounded only by CPython's
//     C-recursion budget of 10,000 units, far past what fits: the stack overflows and
//     the interpreter dies. Measured in Chrome, @cache recursion (3 units a level)
//     dies at ~1,000 units, freeing a list (1 a level) at ~2,300. So each run gets a
//     budget of C_BUDGET units: deep C recursion raises an ordinary RecursionError,
//     and CPython's trashcan frees long chains iteratively instead of recursively.
//     The budget lives in PyThreadState.c_recursion_remaining, set through ctypes;
//     its offset is verified at boot and the cap is skipped if it does not check out.
const C_BUDGET = 700;

const RUNNER = `
import sys, time, types, traceback, linecache, gc

_PYODIDE_MAIN = sys.modules["__main__"]
_DEFAULT_LIMIT = sys.getrecursionlimit()

def _strictly_increasing(clock, step):
    last = clock()
    def read():
        nonlocal last
        t = clock()
        last = t if t > last else last + step
        return last
    return read

for _name, _step in (("perf_counter", 1e-7), ("monotonic", 1e-7), ("time", 1e-7),
                     ("perf_counter_ns", 100), ("monotonic_ns", 100), ("time_ns", 100)):
    setattr(time, _name, _strictly_increasing(getattr(time, _name), _step))

def _find_c_budget():
    """PyThreadState as ints: [7] py_recursion_remaining, [8] py_recursion_limit,
    [9] c_recursion_remaining (CPython 3.13, wasm32). Returns the ctypes view of
    [9], or None if the layout is not what we expect."""
    try:
        import ctypes
        get = ctypes.pythonapi.PyThreadState_Get
        get.restype = ctypes.c_void_p
        ts = (ctypes.c_int * 12).from_address(get())
        if sys.version_info[:2] != (3, 13) or ts[8] != sys.getrecursionlimit():
            return None
        sys.setrecursionlimit(_DEFAULT_LIMIT + 7)
        moved = ts[8] == _DEFAULT_LIMIT + 7
        sys.setrecursionlimit(_DEFAULT_LIMIT)
        top = ts[9]
        inner = []
        sorted([0], key=lambda _: inner.append(ts[9]))       # one C -> Python call deeper
        if moved and ts[8] == _DEFAULT_LIMIT and 0 < inner[0] < top <= 10000:
            return ts
    except Exception:
        pass
    return None

_TS = _find_c_budget()

def _eg_run(src):
    name = "main.py"
    linecache.cache[name] = (len(src), None, src.splitlines(True), name)
    mod = types.ModuleType("__main__")
    mod.__file__ = name
    sys.modules["__main__"] = mod
    sys.argv = [name]
    sys.setrecursionlimit(_DEFAULT_LIMIT)
    cut = max(0, _TS[9] - ${C_BUDGET}) if _TS else 0
    if cut:
        _TS[9] -= cut
    try:
        exec(compile(src, name, "exec"), mod.__dict__)
        return 0
    except SystemExit as e:
        if e.code is None:
            return 0
        if isinstance(e.code, int):
            return e.code
        print(e.code, file=sys.stderr)
        return 1
    except BaseException as e:
        tb = e.__traceback__
        traceback.print_exception(type(e), e, tb.tb_next if tb else None)   # drop this frame
        if isinstance(e, RecursionError) and cut:
            print("\\nnote: in the browser, recursion through C code (@cache / lru_cache, "
                  "__repr__, map, ...) is limited to a few hundred levels: WebAssembly gets far "
                  "less stack than a native Python. Plain recursion is not affected. Run the "
                  "app locally (make app) for deep recursion of this kind.", file=sys.stderr)
        return 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.modules["__main__"] = _PYODIDE_MAIN
        # Free what the program built while the budget still applies: a 100,000-node
        # list freed with the full budget would overflow the stack on the way out.
        mod.__dict__.clear()
        gc.collect()
        if cut:
            _TS[9] += cut
`;

let stdout = '', stderr = '';
const sink = append => {
  const dec = new TextDecoder();
  return { write: buf => { append(dec.decode(buf, { stream: true })); return buf.length; } };
};

const boot = (async () => {
  importScripts(PYODIDE_URL + 'pyodide.js');
  const py = await loadPyodide({ indexURL: PYODIDE_URL });
  py.setStdout(sink(s => { stdout += s; }));
  py.setStderr(sink(s => { stderr += s; }));
  py.setStdin({ stdin: () => null });           // input() sees EOF, as with no terminal attached
  py.runPython(RUNNER);
  return { py, run: py.globals.get('_eg_run') };
})();
boot.catch(() => {});                           // reported per run, in onmessage

onmessage = async ({ data: m }) => {
  let rt;
  try {
    rt = await boot;
  } catch (e) {
    postMessage({ id: m.id, bootError: String(e && e.message || e) });
    return;
  }
  // Stdlib needs nothing; imports of Pyodide-packaged libraries (numpy, sqlite3…) load on demand.
  try {
    await rt.py.loadPackagesFromImports(m.code, { messageCallback: () => {}, errorCallback: () => {} });
  } catch (e) { /* a bad import reports itself when the code runs */ }

  stdout = ''; stderr = '';
  postMessage({ id: m.id, started: true });
  const t0 = performance.now();
  let exitCode;
  try {
    exitCode = rt.run(m.code);
  } catch (e) {
    exitCode = undefined;
    stderr += `\n${e && e.message || e}`;
  }
  // Python exceptions are printed by _eg_run, which returns an int. Anything else is
  // the interpreter itself failing — in practice the stack overflowing despite
  // C_BUDGET (a browser with an even smaller worker stack, or C code that recurses
  // without counting). The interpreter is unusable after that, so start a fresh one.
  if (typeof exitCode !== 'number') {
    stderr += '\nThe Python runtime crashed, most likely by running out of stack: WebAssembly ' +
      'gets far less stack than a native Python process. Python restarts on the next run; ' +
      'run the app locally (make app) for full-size benchmarks.\n';
    postMessage({ id: m.id, ok: false, stdout, stderr, exitCode: -1, ms: Math.round(performance.now() - t0), fatal: true });
    return;
  }
  postMessage({ id: m.id, ok: exitCode === 0, stdout, stderr, exitCode, ms: Math.round(performance.now() - t0) });
};
