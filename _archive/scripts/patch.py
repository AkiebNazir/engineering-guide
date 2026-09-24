import re

content = open("webapp/static/dsa-viz.js").read()

replacements = [
    (r"  draw\(ctx, c, f, P\) \{\n    const g = AV\.row\(ctx, P, f\.nums, \{ cw: c\.w, y: 34, style: i => \{\n      if \(f\.phase === 'mark'\) \{\n        if \(i === f\.idx\) return \{ fill: P\.alpha\('danger', \.3\), stroke: P\.danger \};\n        if \(i === f\.i\) return \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \};\n      \} else if \(f\.phase === 'gather'\) \{\n        if \(i === f\.i && f\.nums\[i\] > 0\) return \{ fill: P\.alpha\('ok', \.3\), stroke: P\.ok \};\n        if \(i === f\.i\) return \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \};\n        if \(i < f\.i\) return \{ fade: true \};\n      \}\n      return \{\};\n    \} \}\);\n    if \(f\.phase === 'mark' && f\.i >= 0\) AV\.ptr\(ctx, P, g, f\.i, 'i', P\.accent\);\n    if \(f\.phase === 'mark' && f\.idx >= 0\) AV\.ptr\(ctx, P, g, f\.idx, 'idx', P\.danger, f\.idx === f\.i \? 1 : 0, true\);\n    \n    if \(f\.phase === 'gather'\) \{\n      if \(f\.i >= 0\) AV\.ptr\(ctx, P, g, f\.i, 'i', P\.accent\);\n      if \(f\.ans\.length > 0\) \{\n        const ansRow = AV\.row\(ctx, P, f\.ans, \{ cw: c\.w, y: 120, max: 40, style: \(\) => \(\{ fill: P\.surface2, stroke: P\.ok \}\) \}\);\n        D\.text\(ctx, 'ans', ansRow\.left - 24, ansRow\.y \+ ansRow\.size / 2 \+ 0\.5, \{ color: P\.text, size: 13, align: 'right', weight: 600, mono: true \}\);\n      \}\n    \}\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-nums', f.nums.map((v, i) => {
      let state = '';
      let ptr = null;
      if (f.phase === 'mark') {
        if (i === f.idx) state = 'miss';
        if (i === f.i) state = 'active';
        if (i === f.idx) ptr = 'idx';
        if (i === f.i) ptr = ptr ? 'i, idx' : 'i';
      } else if (f.phase === 'gather') {
        if (i === f.i) state = f.nums[i] > 0 ? 'match' : 'active';
        else if (i < f.i) state = 'faded';
        if (i === f.i) ptr = 'i';
      }
      return { val: v, state, ptr };
    }), { label: 'nums' });
    
    if (f.phase === 'gather' && f.ans.length > 0) {
      window.MV.arrayRow(stage, 'row-ans', f.ans.map((v, i) => ({ val: v, state: 'match', ptr: null })), { label: 'ans' });
    }
  },"""),
  
    (r"  draw\(ctx, c, f, P\) \{\n    const g = AV\.row\(ctx, P, f\.nums, \{ cw: c\.w, y: 34, style: i => i === f\.i \? \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \} : \{\} \}\);\n    if \(f\.i >= 0\) AV\.ptr\(ctx, P, g, f\.i, 'i', P\.accent\);\n    \n    const r = AV\.row\(ctx, P, f\.res, \{ cw: c\.w, y: 120, max: 40, style: i => i === f\.i \? \{ fill: P\.alpha\('ok', \.25\), stroke: P\.ok \} : f\.phase === 'postfix' && i > f\.i \? \{ fill: P\.surface2, stroke: P\.ok \} : f\.phase === 'postfix' \? \{ fill: P\.surface2, stroke: P\.text \} : i < f\.i \? \{ fill: P\.surface2, stroke: P\.text \} : \{ fade: true \} \}\);\n    D\.text\(ctx, 'res', r\.left - 24, r\.y \+ r\.size / 2 \+ 0\.5, \{ color: P\.text, size: 13, align: 'right', weight: 600, mono: true \}\);\n    if \(f\.i >= 0\) AV\.ptr\(ctx, P, r, f\.i, 'i', P\.ok\);\n    \n    const items = \[\];\n    if \(f\.phase === 'prefix'\) items\.push\(\['prefix', String\(f\.prefix\)\]\);\n    if \(f\.phase === 'postfix'\) items\.push\(\['postfix', String\(f\.postfix\)\]\);\n    AV\.pills\(ctx, P, 20, r\.y \+ r\.size \+ 50, c\.w - 40, 'variables', items, \{ hi: null, miss: null \}\);\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-nums', f.nums.map((v, i) => ({
      val: v,
      state: i === f.i ? 'active' : '',
      ptr: i === f.i ? 'i' : null
    })), { label: 'nums' });
    
    window.MV.arrayRow(stage, 'row-res', f.res.map((v, i) => ({
      val: v,
      state: i === f.i ? 'match' : (f.phase === 'postfix' && i > f.i ? 'match' : (f.phase === 'postfix' || i < f.i ? '' : 'faded')),
      ptr: i === f.i ? 'i' : null
    })), { label: 'res' });
    
    const items = [];
    if (f.phase === 'prefix') items.push({ k: 'prefix', v: String(f.prefix) });
    if (f.phase === 'postfix') items.push({ k: 'postfix', v: String(f.postfix) });
    window.MV.hashMap(stage, 'hash-vars', 'variables', items);
  },"""),
  
    (r"  draw\(ctx, c, f, P\) \{\n    const g = AV\.row\(ctx, P, f\.board, \{ cw: c\.w, y: 34, style: i => i === f\.r \? \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \} : \{\} \}\);\n    if \(f\.r >= 0\) AV\.ptr\(ctx, P, g, f\.r, 'r', P\.accent\);\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-board', f.board.map((v, i) => ({
      val: v,
      state: i === f.r ? 'active' : '',
      ptr: i === f.r ? 'r' : null
    })), { label: 'board' });
  },"""),
  
    (r"  draw\(ctx, c, f, P\) \{\n    const g = AV\.row\(ctx, P, f\.nums, \{ cw: c\.w, y: 34, style: i => i === f\.i \? \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \} : \{\} \}\);\n    if \(f\.i >= 0\) AV\.ptr\(ctx, P, g, f\.i, 'i', P\.accent\);\n    \n    const items = \[\];\n    if \(f\.vars\.n !== undefined\) items\.push\(\['n', String\(f\.vars\.n\)\]\);\n    if \(f\.vars\.length !== undefined\) items\.push\(\['length', String\(f\.vars\.length\)\]\);\n    if \(f\.vars\.longest !== undefined\) items\.push\(\['longest', String\(f\.vars\.longest\)\]\);\n    AV\.pills\(ctx, P, 20, 120, c\.w - 40, 'variables', items, \{ hi: null, miss: null \}\);\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-nums', f.nums.map((v, i) => ({
      val: v,
      state: i === f.i ? 'active' : '',
      ptr: i === f.i ? 'i' : null
    })), { label: 'nums' });
    
    const items = [];
    if (f.vars.n !== undefined) items.push({ k: 'n', v: String(f.vars.n) });
    if (f.vars.length !== undefined) items.push({ k: 'length', v: String(f.vars.length) });
    if (f.vars.longest !== undefined) items.push({ k: 'longest', v: String(f.vars.longest) });
    window.MV.hashMap(stage, 'hash-vars', 'variables', items);
  },"""),
  
    (r"  draw\(ctx, c, f, P\) \{\n    const g = AV\.row\(ctx, P, f\.nums, \{ cw: c\.w, y: 34, style: idx => \{\n      if \(f\.phase === 'scan1' \|\| f\.phase === 'scan2'\) \{\n        if \(idx === f\.i\) return \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \};\n        if \(idx === f\.j\) return \{ fill: P\.alpha\('ok', \.25\), stroke: P\.ok \};\n      \}\n      if \(f\.phase === 'reverse'\) \{\n        if \(idx === f\.left \|\| idx === f\.right\) return \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \};\n      \}\n      return \{\};\n    \}\}\);\n    \n    if \(f\.phase === 'scan1' \|\| f\.phase === 'scan2'\) \{\n      if \(f\.i >= 0\) AV\.ptr\(ctx, P, g, f\.i, 'i', P\.accent\);\n      if \(f\.j >= 0\) AV\.ptr\(ctx, P, g, f\.j, 'j', P\.ok\);\n    \} else if \(f\.phase === 'reverse'\) \{\n      if \(f\.left >= 0 && f\.left < f\.right\) AV\.ptr\(ctx, P, g, f\.left, 'L', P\.accent\);\n      if \(f\.right >= 0 && f\.left < f\.right\) AV\.ptr\(ctx, P, g, f\.right, 'R', P\.accent\);\n    \}\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-nums', f.nums.map((v, idx) => {
      let state = '';
      let ptr = null;
      if (f.phase === 'scan1' || f.phase === 'scan2') {
        if (idx === f.i) { state = 'active'; ptr = 'i'; }
        if (idx === f.j) { state = 'match'; ptr = ptr ? 'i, j' : 'j'; }
      } else if (f.phase === 'reverse') {
        if (idx === f.left) { state = 'active'; ptr = 'L'; }
        if (idx === f.right) { state = 'active'; ptr = ptr ? 'L, R' : 'R'; }
      }
      return { val: v, state, ptr };
    }), { label: 'nums' });
  },"""),
  
    (r"  draw\(ctx, c, f, P\) \{\n    const sRow = AV\.row\(ctx, P, f\.s, \{ cw: c\.w, y: 34, style: i => i === f\.i \? \{ fill: P\.alpha\('accent', \.25\), stroke: P\.accent \} : \{\} \}\);\n    D\.text\(ctx, 's', sRow\.left - 24, sRow\.y \+ sRow\.size / 2 \+ 0\.5, \{ color: P\.text, size: 13, align: 'right', weight: 600, mono: true \}\);\n    \n    const tRow = AV\.row\(ctx, P, f\.t, \{ cw: c\.w, y: 90, style: i => i === f\.i \? \{ fill: P\.alpha\('ok', \.25\), stroke: P\.ok \} : \{\} \}\);\n    D\.text\(ctx, 't', tRow\.left - 24, tRow\.y \+ tRow\.size / 2 \+ 0\.5, \{ color: P\.text, size: 13, align: 'right', weight: 600, mono: true \}\);\n    \n    if \(f\.i >= 0\) \{\n      AV\.ptr\(ctx, P, sRow, f\.i, 'i', P\.accent, true\); \n      AV\.ptr\(ctx, P, tRow, f\.i, 'i', P\.ok\);\n    \}\n    \n    const stItems = Object\.entries\(f\.mapST\)\.map\(\(\[k, v\]\) => \[`'\$\{k\}'`, `'\$\{v\}'`\]\);\n    AV\.pills\(ctx, P, 20, 150, c\.w / 2 - 30, 'mapST \\(s → t\\)', stItems, \{ hi: null, miss: null \}\);\n    \n    const tsItems = Object\.entries\(f\.mapTS\)\.map\(\(\[k, v\]\) => \[`'\$\{k\}'`, `'\$\{v\}'`\]\);\n    AV\.pills\(ctx, P, c\.w / 2 \+ 10, 150, c\.w / 2 - 30, 'mapTS \\(t → s\\)', tsItems, \{ hi: null, miss: null \}\);\n  \},",
     """  renderDOM(stage, c, f, P) {
    window.MV.arrayRow(stage, 'row-s', f.s.map((v, i) => ({
      val: v,
      state: i === f.i ? 'active' : '',
      ptr: i === f.i ? 'i' : null
    })), { label: 's' });
    
    window.MV.arrayRow(stage, 'row-t', f.t.map((v, i) => ({
      val: v,
      state: i === f.i ? 'match' : '',
      ptr: i === f.i ? 'i' : null
    })), { label: 't' });
    
    window.MV.hashMap(stage, 'hash-st', 'mapST (s → t)', Object.entries(f.mapST).map(([k, v]) => ({ k: `'${k}'`, v: `'${v}'` })));
    window.MV.hashMap(stage, 'hash-ts', 'mapTS (t → s)', Object.entries(f.mapTS).map(([k, v]) => ({ k: `'${k}'`, v: `'${v}'` })));
  },""")
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open("webapp/static/dsa-viz.js", "w") as f:
    f.write(content)

print("Patch applied successfully.")
