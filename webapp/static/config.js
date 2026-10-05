/* Runtime mode. This source copy is what the local server (`make app`) serves.
   `make build` (webapp/build_static.py) replaces it in dist/ with
   `window.EG_STATIC = true;`, which switches app.js to the pre-built data files. */
window.EG_STATIC = false;
