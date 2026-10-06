/* ============================================================================
   Scripts loaded on first use, and asset URLs.

   The step-by-step DSA visualizers and the interactive labs are three fifths of
   the app's JavaScript (~3 MB) but only a few pages use them, so they are not in
   index.html. A page that needs a group awaits LazyScripts.load(name):

     dsaviz  the DSA problem Visualize tab and the solution's "Watch it run"
             (app.js loadPane, solution-gate.js)
     labs    the "Try it" labs and system-design flows inside reading pages
             (reader.js renderDoc: data-viz placeholders, sd.js, roadmap.js)

   Both groups need viz.js, which index.html still loads. A group's files run in
   the order listed, the same order index.html used to give them.

   assetUrl() adds the file's content hash in a static build (config.js EG_V,
   written by build_static.py), so a new deploy never mixes with cached files.
   ========================================================================= */
const assetUrl = file => {
  const v = (window.EG_V || {})[file.replace(/^\.\//, '')];
  return v ? `${file}?v=${v}` : file;
};

window.LazyScripts = (() => {
  const GROUPS = {
    labs: [
      'viz-ml.js', 'viz-llm.js', 'viz-csfund.js', 'viz-cs2.js', 'viz-cs3.js',
      'viz-math.js', 'viz-math2.js', 'viz-math3.js', 'viz-math4.js',
      'viz-sd.js', 'viz-sd2.js', 'viz-sd3.js', 'viz-sd4.js',
      'sd-flow.js', 'flows-net.js', 'flows-osdb.js', 'flows-data.js', 'flows-sdbb.js', 'flows-ai.js',
      'flows-toolkit.js', 'flows-testing.js', 'flows-cicd.js', 'flows-dataeng.js', 'flows-mlops.js',
      'viz-api.js', 'viz-api2.js', 'viz-api3.js', 'viz-api4.js', 'viz-api5.js',
    ],
    dsaviz: [
      'dsa-viz.js', 'dsa-viz-player.js', 'dsa-viz-dom.js', 'dsa-viz2.js', 'dsa-viz17.js',
      'dsa-viz3.js', 'dsa-viz4.js', 'dsa-viz5.js', 'dsa-viz6.js', 'dsa-viz7.js', 'dsa-viz8.js',
      'dsa-viz9.js', 'dsa-viz10.js', 'dsa-viz11.js', 'dsa-viz12.js', 'dsa-viz13.js', 'dsa-viz14.js',
      'dsa-viz15.js', 'dsa-viz16.js', 'dsa-viz18.js', 'dsa-viz19.js', 'dsa-viz20.js', 'dsa-viz21.js',
      'dsa-viz22.js', 'dsa-viz23.js', 'dsa-viz24.js', 'dsa-viz25.js', 'dsa-viz26.js', 'dsa-viz27.js',
      'dsa-viz28.js', 'dsa-viz29.js', 'dsa-viz30.js', 'viz-algorithms.js',
    ],
  };
  const loading = new Map();
  const warmed = new Set();

  // async = false: the files download in parallel but run in insertion order.
  const addScript = file => new Promise(resolve => {
    const s = document.createElement('script');
    s.src = assetUrl(`./${file}`);
    s.async = false;
    s.onload = () => resolve(true);
    s.onerror = () => { console.error(`Could not load ${file}`); resolve(false); };
    document.head.append(s);
  });

  /* Resolves true once every file in the group has run (false if one failed to
     load; the rest still run, as they did as separate <script> tags). */
  const load = name => {
    if (!loading.has(name)) {
      loading.set(name, Promise.all(GROUPS[name].map(addScript)).then(r => r.every(Boolean)));
    }
    return loading.get(name);
  };

  /* Download a group into the browser cache while the page is idle, without
     running it, so a later load() is quick. Skipped on data-saver connections. */
  const warm = name => {
    if (loading.has(name) || warmed.has(name) || navigator.connection?.saveData) return;
    warmed.add(name);
    const go = () => GROUPS[name].forEach(f => fetch(assetUrl(`./${f}`), { priority: 'low' }).catch(() => {}));
    (window.requestIdleCallback || (cb => setTimeout(cb, 1500)))(go, { timeout: 4000 });
  };

  return { load, warm };
})();
