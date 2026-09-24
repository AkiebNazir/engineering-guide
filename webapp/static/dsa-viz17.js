/* ============================================================================
   Visualizations for 13_trie (continued) — problems 002-007.
   Canvas engine (defineAlgo). Problem 001 (Implement Trie) lives in dsa-viz2.js
   and defines the layout style these all copy; see charTrieDraw below for the
   shared helper extracted from it (now generalised with subLabel + region so
   it can annotate values (004), lay out a binary bit-trie (005 — kids keyed
   '0'/'1' instead of letters, same layout code), or share the canvas with a
   grid (006).
   Requires dsa-viz.js (defineAlgo, avNums, avParts, avNum, avRecorder, AV, esc).
   ========================================================================= */
'use strict';

/* ---------------------------------------------------- shared trie helpers -- */
function charTrieLayout(nodes) {
  const pos = {};
  let col = 0, maxD = 0;
  const walk = (id, d) => {
    maxD = Math.max(maxD, d);
    const ks = Object.keys(nodes[id].kids).sort();
    if (!ks.length) { pos[id] = { x: col++, d }; return; }
    const xs = ks.map(k => { walk(nodes[id].kids[k], d + 1); return pos[nodes[id].kids[k]].x; });
    pos[id] = { x: (Math.min(...xs) + Math.max(...xs)) / 2, d };
  };
  walk(0, 0);
  return { pos, cols: Math.max(1, col), maxD };
}
function charTrieHeightFromFrames(frames) {
  const deep = Math.max(...frames.map(f => {
    const d = id => 1 + Math.max(0, ...Object.values(f.nodes[id].kids).map(d));
    return d(0);
  }));
  return 40 + deep * 58 + 40;
}
/* nodes: [{ch, kids:{label->id}, ...}]. region lets two of these share one canvas (006). */
function charTrieDraw(ctx, c, P, nodes, { cur = null, path = [], fresh = null, endSet = null, subLabel = null, footer = null, region = null } = {}) {
  const { pos, cols } = charTrieLayout(nodes);
  const rx = region ? region.x : 0, rw = region ? region.w : c.w;
  const slot = (rw - 56) / cols;
  const X = id => rx + 28 + (pos[id].x + .5) * slot, Y = id => 34 + pos[id].d * 58;
  const onPath = new Set(path);
  nodes.forEach((nd, id) => Object.entries(nd.kids).forEach(([ch, kid]) => {
    const hot = onPath.has(id) && onPath.has(kid);
    D.line(ctx, X(id), Y(id) + 16, X(kid), Y(kid) - 16, hot ? P.accent : P.strong, hot ? 2.6 : 1.4);
    D.text(ctx, ch, (X(id) + X(kid)) / 2 + 9, (Y(id) + Y(kid)) / 2, { color: hot ? P.accent : P.dim, size: 12, weight: 700, mono: true });
  }));
  nodes.forEach((nd, id) => {
    const isCur = id === cur;
    const isEnd = endSet ? endSet.has(id) : !!nd.end;
    const sub = subLabel ? subLabel(id) : null;
    AV.node(ctx, P, X(id), Y(id), 15, nd.ch || '·', {
      fill: id === fresh ? P.alpha('ok', .35) : isCur ? P.alpha('accent', .35) : isEnd ? P.alpha('ok', .12) : null,
      stroke: isCur ? P.accent : isEnd ? P.ok : null,
      ring: isEnd ? P.alpha('ok', .8) : null,
      sub: sub != null && sub !== '' ? sub : undefined,
    });
  });
  if (footer) D.text(ctx, footer.text, rx + rw / 2, c.h - 16, { color: footer.color || P.dim, size: 12, align: 'center', weight: 650, mono: footer.mono !== false });
}

/* ============================================ 002 · Design Add and Search Words == */
defineAlgo('13_trie', {
  title: 'Design Add and Search Words Data Structure', short: 'Wildcard Trie Search',
  idea: 'Same trie as a plain prefix tree, but <code>search</code> allows <code>.</code> to match any single character. A <code>.</code> forces a small DFS over every child at that position — this is a trie <b>plus backtracking</b>, not a single straight-line walk.',
  complexity: 'addWord O(L) · search O(26^d &middot; L) worst case where d = number of dots (usually far fewer branches in practice)',
  input: 'bad, dad, mad ; .ad', hint: 'words to add, comma-separated ; a search pattern (letters and "." wildcards)',
  code: [
    'class TrieNode:',
    '    def __init__(self):',
    '        self.children = {}',
    '        self.is_word = False',
    '',
    'def addWord(self, word):',
    '    node = self.root',
    '    for ch in word:',
    '        if ch not in node.children:',
    '            node.children[ch] = TrieNode()',
    '        node = node.children[ch]',
    '    node.is_word = True',
    '',
    'def search(self, word):',
    '    def dfs(node, i):',
    '        if node is None:',
    '            return False',
    '        if i == len(word):',
    '            return node.is_word',
    "        ch = word[i]",
    "        if ch == '.':",
    '            return any(dfs(c, i + 1) for c in node.children.values())',
    '        return dfs(node.children.get(ch), i + 1)',
    '    return dfs(self.root, 0)',
  ],
  parse(s) {
    const [a, q] = avParts(s);
    const words = String(a || '').split(/[\s,]+/).filter(Boolean).map(w => w.toLowerCase());
    if (!words.length) throw new Error('Enter at least one word to add');
    if (words.length > 6) throw new Error('Use at most 6 words');
    words.forEach(w => { if (!/^[a-z]{1,6}$/.test(w)) throw new Error(`“${w}” — letters only, up to 6 per word`); });
    const query = String(q || '').trim().toLowerCase();
    if (!/^[a-z.]{1,6}$/.test(query)) throw new Error('Add a search pattern (letters and "." wildcards) after the ";"');
    if ((query.match(/\./g) || []).length > 2) throw new Error('Use at most 2 "." wildcards so branching stays readable');
    return { words, query };
  },
  run({ words, query }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, end: false }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), ...extra });

    snap(3, 'Start with one empty root node — every word we add branches off it.', S({ cur: 0, path: [0] }));

    words.forEach(word => {
      let node = 0; const path = [0];
      snap(7, `addWord(<b>${word}</b>) — walk from the root, creating nodes as needed.`, S({ cur: 0, path: [...path], word }));
      [...word].forEach(ch => {
        const has = nodes[node].kids[ch] !== undefined;
        if (!has) {
          nodes.push({ ch, kids: {}, end: false });
          nodes[node].kids[ch] = nodes.length - 1;
          snap(10, `No <code>${ch}</code> branch yet — create one.`, S({ cur: node, path: [...path], word, fresh: nodes.length - 1 }));
        } else {
          snap(9, `<code>${ch}</code> already branches off here — reuse it.`, S({ cur: node, path: [...path], word }));
        }
        node = nodes[node].kids[ch];
        path.push(node);
      });
      nodes[node].end = true;
      snap(12, `Mark this node as the end of <b>${word}</b>.`, S({ cur: node, path: [...path], word, done: true }));
    });

    let calls = 0;
    const MAX_CALLS = 60;
    function dfs(node, i, path) {
      calls++;
      if (calls > MAX_CALLS) return false;
      if (node === null) {
        snap(17, `This branch doesn't exist — dead end, return False.`, S({ cur: path[path.length - 1], path: [...path], query, at: i, miss: true }));
        return false;
      }
      if (i === query.length) {
        const ok = nodes[node].end;
        snap(19, ok ? `Pattern fully matched and this node is a word end — return True.` : `Pattern fully matched but this node is not a word end — return False.`, S({ cur: node, path: [...path], query, at: i, result: ok }));
        return ok;
      }
      const ch = query[i];
      if (ch === '.') {
        snap(21, `'.' at position ${i} — try every child from here, one at a time.`, S({ cur: node, path: [...path], query, at: i, wildcard: true }));
        for (const [ch2, kid] of Object.entries(nodes[node].kids)) {
          snap(22, `Try branch <code>${ch2}</code>.`, S({ cur: node, path: [...path], query, at: i, tryCh: ch2 }));
          if (dfs(kid, i + 1, [...path, kid])) return true;
        }
        snap(22, `Every branch from here failed — backtrack.`, S({ cur: node, path: [...path], query, at: i, miss: true }));
        return false;
      }
      const kid = nodes[node].kids[ch];
      snap(23, kid !== undefined ? `Follow <code>${ch}</code>.` : `No <code>${ch}</code> branch here.`, S({ cur: node, path: [...path], query, at: i, tryCh: ch }));
      return dfs(kid === undefined ? null : kid, i + 1, kid !== undefined ? [...path, kid] : path);
    }

    snap(24, `search(<b>${query}</b>) — start the recursive walk from the root.`, S({ cur: 0, path: [0], query }));
    const ok = dfs(0, 0, [0]);
    snap(24, `search("${query}") → <b>${ok}</b>`, S({ query, result: ok, final: true }));
    return F;
  },
  height: (w, last, frames) => charTrieHeightFromFrames(frames),
  draw(ctx, c, f, P) {
    charTrieDraw(ctx, c, P, f.nodes, {
      cur: f.cur, path: f.path, fresh: f.fresh,
      footer: f.query
        ? { text: f.result !== undefined ? `search("${f.query}") → ${f.result}` : `searching "${f.query}"`, color: f.result === true ? P.ok : f.result === false ? P.err : P.dim }
        : f.word ? { text: `adding "${f.word}"`, color: P.dim } : null,
    });
    if (f.tryCh) D.text(ctx, `trying branch '${f.tryCh}'`, c.w / 2, c.h - 34, { color: P.accent, size: 11.5, align: 'center', weight: 650 });
    if (f.wildcard) D.text(ctx, `'.' — branching over all children`, c.w / 2, c.h - 34, { color: P.accent, size: 11.5, align: 'center', weight: 650 });
    D.text(ctx, '◎ = a word ends here', 20, 16, { color: P.ok, size: 11 });
  },
});

/* ============================================================= 003 · Replace Words == */
defineAlgo('13_trie', {
  title: 'Replace Words', short: 'Trie: Replace Words',
  idea: 'Insert every dictionary root into a trie. For each sentence word, walk the trie one character at a time — the <b>first</b> word-end you hit is the <b>shortest</b> matching root (a trie walk visits shorter prefixes before longer ones), so stop immediately.',
  complexity: 'Build O(sum of root lengths) &middot; each word O(its length), not O(roots &times; length)',
  input: 'cat, bat, rat ; the cattle was rattled by battery', hint: 'dictionary roots, comma-separated ; a sentence (each word becomes its shortest matching root)',
  code: [
    'def replaceWords(dictionary, sentence):',
    '    root = TrieNode()',
    '    for w in dictionary:',
    '        node = root',
    '        for ch in w:',
    '            if ch not in node.children:',
    '                node.children[ch] = TrieNode()',
    '            node = node.children[ch]',
    '        node.is_word = True',
    '',
    '    def shortest_root(word):',
    '        node = root',
    '        for i, ch in enumerate(word):',
    '            if ch not in node.children:',
    '                return word            # no root matches',
    '            node = node.children[ch]',
    '            if node.is_word:',
    '                return word[:i + 1]    # first hit = shortest root',
    '        return word                     # ran off the end',
    '',
    '    return " ".join(shortest_root(w) for w in sentence.split())',
  ],
  parse(s) {
    const [a, q] = avParts(s);
    const roots = String(a || '').split(/[\s,]+/).filter(Boolean).map(w => w.toLowerCase());
    if (!roots.length) throw new Error('Enter at least one dictionary root');
    if (roots.length > 6) throw new Error('Use at most 6 roots');
    roots.forEach(w => { if (!/^[a-z]{1,6}$/.test(w)) throw new Error(`“${w}” — letters only, up to 6 per root`); });
    const words = String(q || '').trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) throw new Error('Add a sentence after the ";"');
    if (words.length > 6) throw new Error('Use at most 6 words in the sentence');
    words.forEach(w => { if (!/^[a-z]{1,8}$/.test(w)) throw new Error(`“${w}” — letters only, up to 8 per word`); });
    return { roots, words };
  },
  run({ roots, words }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, end: false }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), ...extra });

    snap(2, 'Build a trie of every dictionary root.', S({ cur: 0, path: [0] }));
    roots.forEach(w => {
      let node = 0; const path = [0];
      [...w].forEach(ch => {
        if (nodes[node].kids[ch] === undefined) {
          nodes.push({ ch, kids: {}, end: false });
          nodes[node].kids[ch] = nodes.length - 1;
          snap(7, `Create a node for <code>${ch}</code> (root "${w}").`, S({ cur: node, path: [...path], fresh: nodes.length - 1 }));
        }
        node = nodes[node].kids[ch];
        path.push(node);
      });
      nodes[node].end = true;
      snap(9, `Mark the end of root <b>${w}</b>.`, S({ cur: node, path: [...path], done: true }));
    });

    const out = [];
    words.forEach(word => {
      let node = 0; const path = [0];
      let replaced = null;
      snap(12, `shortest_root("${word}") — walk the trie one character at a time.`, S({ cur: 0, path: [0], word, out: [...out] }));
      for (let i = 0; i < word.length; i++) {
        const ch = word[i];
        if (nodes[node].kids[ch] === undefined) {
          snap(15, `No <code>${ch}</code> branch — no root matches. Keep "${word}" as-is.`, S({ cur: node, path: [...path], word, at: i, miss: true, out: [...out] }));
          replaced = word;
          break;
        }
        node = nodes[node].kids[ch]; path.push(node);
        if (nodes[node].end) {
          replaced = word.slice(0, i + 1);
          snap(18, `Hit a word end at "${replaced}" — that's the shortest root. Replace "${word}" → "${replaced}".`, S({ cur: node, path: [...path], word, at: i, hit: true, replaced, out: [...out] }));
          break;
        }
        snap(16, `Follow <code>${ch}</code> — ${i + 1} of ${word.length} matched, no word end yet.`, S({ cur: node, path: [...path], word, at: i, out: [...out] }));
      }
      if (replaced === null) {
        replaced = word;
        snap(19, `Ran off the end of "${word}" without hitting a word end. Keep it as-is.`, S({ cur: node, path: [...path], word, out: [...out] }));
      }
      out.push(replaced);
    });
    snap(21, `Join every replacement: "${out.join(' ')}"`, S({ out: [...out], final: true }));
    return F;
  },
  height: (w, last, frames) => charTrieHeightFromFrames(frames),
  draw(ctx, c, f, P) {
    charTrieDraw(ctx, c, P, f.nodes, {
      cur: f.cur, path: f.path, fresh: f.fresh,
      footer: f.word ? { text: f.replaced ? `"${f.word}" → "${f.replaced}"` : `checking "${f.word}"`, color: f.hit ? P.ok : f.miss ? P.err : P.dim } : null,
    });
    D.text(ctx, `so far: ${f.out && f.out.length ? f.out.join(' ') : '(none yet)'}`, c.w / 2, 16, { color: P.dim, size: 11.5, align: 'center', mono: true });
  },
});

/* =========================================================== 004 · Map Sum Pairs == */
defineAlgo('13_trie', {
  title: 'Map Sum Pairs', short: 'Trie: Prefix Sums',
  idea: 'Give every trie node a running <code>value</code> — the sum of every inserted value whose key passes through it. Insert stores a <b>delta</b> (new value minus whatever that key held before) and adds it to every node on the key’s path, including the root, so <code>sum(prefix)</code> is just reading one node’s value in O(prefix length).',
  complexity: 'insert O(key length) &middot; sum O(prefix length), no scanning of other keys',
  input: 'apple 3, app 2 ; ap', hint: '"key value" pairs, comma-separated (later inserts overwrite earlier ones) ; a prefix to sum',
  code: [
    'class TrieNode:',
    '    def __init__(self):',
    '        self.children = {}',
    '        self.value = 0        # sum of every value passing through here',
    '',
    'def insert(self, key, val):',
    '    delta = val - self.key_values.get(key, 0)',
    '    self.key_values[key] = val',
    '    node = self.root',
    '    node.value += delta       # root = sum(""), no special-casing needed',
    '    for ch in key:',
    '        if ch not in node.children:',
    '            node.children[ch] = TrieNode()',
    '        node = node.children[ch]',
    '        node.value += delta',
    '',
    'def sum(self, prefix):',
    '    node = self.root',
    '    for ch in prefix:',
    '        if ch not in node.children:',
    '            return 0',
    '        node = node.children[ch]',
    '    return node.value',
  ],
  parse(s) {
    const [a, q] = avParts(s);
    const pairs = String(a || '').split(',').map(x => x.trim()).filter(Boolean).map(tok => {
      const m = tok.match(/^([a-zA-Z]{1,6})\s+(-?\d{1,4})$/);
      if (!m) throw new Error(`“${tok}” should look like "apple 3"`);
      return { key: m[1].toLowerCase(), val: +m[2] };
    });
    if (!pairs.length) throw new Error('Enter at least one "key value" pair, comma-separated');
    if (pairs.length > 5) throw new Error('Use at most 5 pairs');
    const prefix = String(q || '').trim().toLowerCase();
    if (!/^[a-z]{1,6}$/.test(prefix)) throw new Error('Add a prefix (letters only) after the ";"');
    return { pairs, prefix };
  },
  run({ pairs, prefix }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, value: 0 }];
    const keyValues = {};
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), ...extra });

    snap(3, 'Start with one root node whose value is the running sum of everything inserted.', S({ cur: 0, path: [0] }));

    pairs.forEach(({ key, val }) => {
      const delta = val - (keyValues[key] || 0);
      keyValues[key] = val;
      let node = 0; const path = [0];
      nodes[0].value += delta;
      snap(10, `insert("${key}", ${val}) — delta = ${delta}. Add it to the root's running total first.`, S({ cur: 0, path: [0], key, val, delta }));
      [...key].forEach(ch => {
        if (nodes[node].kids[ch] === undefined) {
          nodes.push({ ch, kids: {}, value: 0 });
          nodes[node].kids[ch] = nodes.length - 1;
          snap(13, `Create a node for <code>${ch}</code>.`, S({ cur: node, path: [...path], key, val, delta, fresh: nodes.length - 1 }));
        }
        node = nodes[node].kids[ch]; path.push(node);
        nodes[node].value += delta;
        snap(15, `Add the delta (${delta}) to this node too — every node on the path shares it.`, S({ cur: node, path: [...path], key, val, delta }));
      });
    });

    let node = 0; const path = [0]; let miss = false;
    snap(18, `sum("${prefix}") — walk to the prefix's node and read its value.`, S({ cur: 0, path: [0], prefix }));
    for (const ch of prefix) {
      if (nodes[node].kids[ch] === undefined) { miss = true; break; }
      node = nodes[node].kids[ch]; path.push(node);
      snap(22, `Follow <code>${ch}</code>.`, S({ cur: node, path: [...path], prefix }));
    }
    const result = miss ? 0 : nodes[node].value;
    snap(23, miss ? `No node for "${prefix}" — return 0.` : `sum("${prefix}") = <b>${result}</b> (this node's accumulated value).`, S({ cur: miss ? null : node, path: [...path], prefix, result, final: true }));
    return F;
  },
  height: (w, last, frames) => charTrieHeightFromFrames(frames),
  draw(ctx, c, f, P) {
    charTrieDraw(ctx, c, P, f.nodes, {
      cur: f.cur, path: f.path, fresh: f.fresh, subLabel: id => f.nodes[id].value,
      footer: f.result !== undefined ? { text: `sum("${f.prefix}") = ${f.result}`, color: P.ok }
        : f.key ? { text: `insert("${f.key}", ${f.val})  Δ=${f.delta}`, color: P.dim }
        : f.prefix ? { text: `sum("${f.prefix}")`, color: P.dim } : null,
    });
  },
});

/* ============================================ 005 · Maximum XOR of Two Numbers == */
defineAlgo('13_trie', {
  title: 'Maximum XOR of Two Numbers in an Array', short: 'Binary Trie: Max XOR',
  idea: 'A <b>binary</b> trie: every number becomes a root-to-leaf path of its bits, MSB first, so every edge is 0 or 1 instead of a letter. To maximise <code>a XOR b</code> for a fixed <code>a</code>, greedily walk toward the <b>opposite</b> bit at every level — that flips the bit in the XOR from 0 to 1, which is worth more than any combination of bits below it.',
  complexity: 'Build O(n &times; bits) &middot; query all n numbers O(n &times; bits) &middot; real solution uses 30 bits, this animation uses 4 so the tree stays small',
  input: '3, 10, 5, 14, 2, 8', hint: 'numbers 0-15 only (a 4-bit trie, kept small for the animation — the real solution uses 30 bits)',
  code: [
    'BITS = 4                     # shrunk for the animation (real solution: 30)',
    'def findMaximumXOR(nums):',
    '    root = TrieNode()',
    '    for num in nums:',
    '        node = root',
    '        for i in range(BITS - 1, -1, -1):',
    '            bit = (num >> i) & 1',
    '            if node.children[bit] is None:',
    '                node.children[bit] = TrieNode()',
    '            node = node.children[bit]',
    '',
    '    best = 0',
    '    for num in nums:',
    '        node, xor_val = root, 0',
    '        for i in range(BITS - 1, -1, -1):',
    '            bit = (num >> i) & 1',
    '            want = 1 - bit',
    '            if node.children[want] is not None:',
    '                xor_val |= (1 << i)',
    '                node = node.children[want]',
    '            else:',
    '                node = node.children[bit]',
    '        best = max(best, xor_val)',
    '    return best',
  ],
  parse(s) {
    const BITS = 4;
    const nums = avNums(s, 6, 'numbers').map(n => Math.trunc(Math.abs(n)));
    if (nums.some(n => n > 15)) throw new Error('Keep numbers between 0 and 15 (4-bit trie, so the tree stays readable — the real solution uses 30 bits)');
    if (nums.length < 2) throw new Error('Enter at least 2 numbers');
    return { nums, BITS };
  },
  run({ nums, BITS }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, end: false }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), ...extra });
    const bits = n => Array.from({ length: BITS }, (_, k) => (n >> (BITS - 1 - k)) & 1);

    snap(3, 'Build a binary trie: every number becomes a root-to-leaf path of its bits, MSB first.', S({ cur: 0, path: [0] }));
    nums.forEach(num => {
      let node = 0; const path = [0]; const bs = bits(num);
      bs.forEach(bit => {
        if (nodes[node].kids[bit] === undefined) {
          nodes.push({ ch: String(bit), kids: {}, end: false });
          nodes[node].kids[bit] = nodes.length - 1;
        }
        node = nodes[node].kids[bit]; path.push(node);
      });
      nodes[node].end = true;
      snap(10, `Insert ${num} = ${bs.join('')} in binary.`, S({ cur: node, path: [...path], num }));
    });

    let best = 0;
    nums.forEach(num => {
      let node = 0, xor = 0; const path = [0]; const bs = bits(num);
      snap(14, `Walk ${num} greedily, preferring the opposite bit at each step.`, S({ cur: 0, path: [0], num, xor: 0 }));
      bs.forEach(bit => {
        const want = 1 - bit;
        if (nodes[node].kids[want] !== undefined) {
          xor = xor * 2 + 1;
          node = nodes[node].kids[want]; path.push(node);
          snap(19, `Opposite bit <code>${want}</code> exists — take it (this bit of the XOR becomes 1).`, S({ cur: node, path: [...path], num, xor }));
        } else {
          xor = xor * 2;
          node = nodes[node].kids[bit]; path.push(node);
          snap(22, `No <code>${want}</code> branch — forced to take <code>${bit}</code> (this bit of the XOR is 0).`, S({ cur: node, path: [...path], num, xor }));
        }
      });
      best = Math.max(best, xor);
      snap(23, `${num}'s best partner gives XOR = ${xor}. Running best = ${best}.`, S({ cur: node, path: [...path], num, xor, best }));
    });
    snap(24, `Maximum XOR of any pair = <b>${best}</b>`, S({ best, final: true }));
    return F;
  },
  height: (w, last, frames) => charTrieHeightFromFrames(frames),
  draw(ctx, c, f, P) {
    charTrieDraw(ctx, c, P, f.nodes, {
      cur: f.cur, path: f.path,
      footer: f.num !== undefined ? { text: f.best !== undefined ? `num=${f.num}  xor so far=${f.xor}  best=${f.best}` : `inserting ${f.num}`, color: P.dim } : null,
    });
    if (f.final) D.text(ctx, `answer: ${f.best}`, c.w / 2, 16, { color: P.ok, size: 13, align: 'center', weight: 700 });
  },
});

/* ================================================================ 006 · Word Search II == */
defineAlgo('13_trie', {
  title: 'Word Search II', short: 'Trie + Grid DFS',
  idea: 'Put every target word into a trie, then run one DFS over the board from each cell, walking the trie alongside it — a branch dies the instant the board stops matching <b>any</b> remaining word, so the search fans out over the board and the dictionary at the same time instead of re-running a separate word search per word.',
  complexity: 'O(rows &times; cols &times; 4^L) worst case, but the trie prunes branches the moment they stop matching any word — far fewer in practice',
  input: 'at, ca ; cat, at', hint: 'grid rows, comma-separated (all the same length, max 3x3) ; words to find, comma-separated',
  code: [
    'def findWords(board, words):',
    '    root = TrieNode()',
    '    for w in words:',
    '        node = root',
    '        for ch in w:',
    '            if ch not in node.children:',
    '                node.children[ch] = TrieNode()',
    '            node = node.children[ch]',
    '        node.word = w',
    '',
    '    found = []',
    '    def dfs(r, c, node):',
    '        ch = board[r][c]',
    '        child = node.children.get(ch)',
    '        if child is None:',
    '            return',
    '        if child.word is not None:',
    '            found.append(child.word)',
    '            child.word = None            # avoid duplicate adds',
    '        board[r][c] = "#"                # mark visited',
    '        for nr, nc in neighbors(r, c):',
    '            if board[nr][nc] != "#":',
    '                dfs(nr, nc, child)',
    '        board[r][c] = ch                 # restore',
    '',
    '    for r in range(rows):',
    '        for c in range(cols):',
    '            dfs(r, c, root)',
    '    return found',
  ],
  parse(s) {
    const [g, w] = avParts(s);
    const rows = String(g || '').split(',').map(r => r.trim().toLowerCase()).filter(Boolean);
    if (!rows.length) throw new Error('Enter grid rows, comma-separated');
    if (rows.length > 3) throw new Error('Use at most 3 rows so the animation stays readable');
    const cols = rows[0].length;
    if (!cols || cols > 3) throw new Error('Use 1 to 3 letters per row');
    rows.forEach(r => {
      if (r.length !== cols) throw new Error('Every row needs the same number of letters');
      if (!/^[a-z]+$/.test(r)) throw new Error('Letters only in the grid');
    });
    const board = rows.map(r => [...r]);
    const words = String(w || '').split(/[\s,]+/).filter(Boolean).map(x => x.toLowerCase());
    if (!words.length) throw new Error('Add at least one word after the ";"');
    if (words.length > 3) throw new Error('Use at most 3 words');
    words.forEach(word => { if (!/^[a-z]{1,4}$/.test(word)) throw new Error(`“${word}” — letters only, up to 4 chars`); });
    return { board, words };
  },
  run({ board, words }) {
    const { F, snap } = avRecorder();
    const rows = board.length, cols = board[0].length;
    const nodes = [{ ch: '', kids: {}, word: null }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), board: board.map(r => [...r]), ...extra });

    snap(2, 'Build a trie of every word to find.', S({ cur: 0, path: [0] }));
    words.forEach(w => {
      let node = 0; const path = [0];
      [...w].forEach(ch => {
        if (nodes[node].kids[ch] === undefined) { nodes.push({ ch, kids: {}, word: null }); nodes[node].kids[ch] = nodes.length - 1; }
        node = nodes[node].kids[ch]; path.push(node);
      });
      nodes[node].word = w;
      snap(9, `Mark the end of "${w}".`, S({ cur: node, path: [...path] }));
    });

    const found = [];
    let calls = 0;
    const MAX_CALLS = 150;
    function dfs(r, c, node, path, cellPath) {
      calls++;
      if (calls > MAX_CALLS) return;
      const ch = board[r][c];
      const child = nodes[node].kids[ch];
      if (child === undefined) {
        snap(15, `board[${r}][${c}] = '${ch}' — no <code>${ch}</code> branch here. Stop.`, S({ cur: node, path: [...path], cell: [r, c], cellPath: [...cellPath], found: [...found], miss: true }));
        return;
      }
      const newPath = [...path, child], newCellPath = [...cellPath, [r, c]];
      if (nodes[child].word !== null) {
        found.push(nodes[child].word);
        snap(18, `Found "${nodes[child].word}"!`, S({ cur: child, path: newPath, cell: [r, c], cellPath: newCellPath, found: [...found], hit: true }));
        nodes[child].word = null;
      } else {
        snap(14, `board[${r}][${c}] = '${ch}' — follow it.`, S({ cur: child, path: newPath, cell: [r, c], cellPath: newCellPath, found: [...found] }));
      }
      const visited = board[r][c]; board[r][c] = '#';
      [[r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]].forEach(([nr, nc]) => {
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && board[nr][nc] !== '#') dfs(nr, nc, child, newPath, newCellPath);
      });
      board[r][c] = visited;
    }
    for (let r = 0; r < rows; r++) for (let cc = 0; cc < cols; cc++) {
      snap(28, `Start a fresh DFS at board[${r}][${cc}].`, S({ cur: 0, path: [0], cell: [r, cc], cellPath: [[r, cc]], found: [...found] }));
      dfs(r, cc, 0, [0], []);
    }
    snap(29, `Every found word: ${found.length ? found.join(', ') : '(none)'}`, S({ found: [...found], final: true }));
    return F;
  },
  height: (w, last, frames) => Math.max(240, charTrieHeightFromFrames(frames)),
  draw(ctx, c, f, P) {
    const leftW = c.w * 0.42;
    const rows = f.board.length, cols = f.board[0].length;
    const cell = Math.min(56, (leftW - 40) / cols, (c.h - 80) / rows);
    const gx0 = (leftW - cols * cell) / 2, gy0 = 40;
    const cellPathSet = new Set((f.cellPath || []).map(([r, cc]) => `${r},${cc}`));
    for (let r = 0; r < rows; r++) for (let cc = 0; cc < cols; cc++) {
      const x = gx0 + cc * cell, y = gy0 + r * cell;
      const isCur = f.cell && f.cell[0] === r && f.cell[1] === cc;
      const onPath = cellPathSet.has(`${r},${cc}`);
      ctx.fillStyle = isCur ? P.alpha('accent', .35) : onPath ? P.alpha('ok', .18) : P.surface2;
      D.rrect(ctx, x + 2, y + 2, cell - 4, cell - 4, 6); ctx.fill();
      ctx.strokeStyle = isCur ? P.accent : onPath ? P.ok : P.strong; ctx.lineWidth = isCur ? 2.4 : 1.2; ctx.stroke();
      D.text(ctx, f.board[r][cc].toUpperCase(), x + cell / 2, y + cell / 2, { color: P.text, size: Math.max(12, cell * .4), align: 'center', weight: 700, mono: true });
    }
    D.text(ctx, 'board', gx0, 20, { color: P.dim, size: 11.5, weight: 650 });
    D.text(ctx, `found: ${f.found && f.found.length ? f.found.join(', ') : '(none yet)'}`, leftW / 2, c.h - 16, { color: P.ok, size: 11.5, align: 'center', weight: 650 });
    charTrieDraw(ctx, c, P, f.nodes, { cur: f.cur, path: f.path, region: { x: leftW + 10, w: c.w - leftW - 20 } });
  },
});

/* ==================================================== 007 · Search Suggestions System == */
defineAlgo('13_trie', {
  title: 'Search Suggestions System', short: 'Trie: Top-3 Suggestions',
  idea: 'Insert every product, sorted, into a trie, and at each node along an insertion path keep the first 3 words seen there — because insertion happens in sorted order, "first 3" is exactly the lexicographically smallest 3 words below that node. Typing the search word one character at a time is then just a trie walk, reading off the current node’s pre-computed top-3.',
  complexity: 'Build O(n log n + sum of lengths) once &middot; each typed character O(1) to read the answer, vs. re-filtering all products per character',
  input: 'mobile, mouse, moneypot, monitor, mousepad ; mouse', hint: 'products, comma-separated ; the word typed one letter at a time',
  code: [
    'def build_trie(products):',
    '    root = TrieNode()',
    '    for word in sorted(products):',
    '        node = root',
    '        for ch in word:',
    '            node = node.children.setdefault(ch, TrieNode())',
    '            if len(node.top) < 3:',
    '                node.top.append(word)',
    '    return root',
    '',
    'def suggest(root, word):',
    '    out, node = [], root',
    '    for ch in word:',
    '        node = node.children.get(ch) if node else None',
    '        out.append(list(node.top) if node else [])',
    '    return out',
  ],
  parse(s) {
    const [p, w] = avParts(s);
    const products = String(p || '').split(/[\s,]+/).filter(Boolean).map(x => x.toLowerCase());
    if (!products.length) throw new Error('Enter at least one product, comma-separated');
    if (products.length > 8) throw new Error('Use at most 8 products');
    products.forEach(x => { if (!/^[a-z]{1,8}$/.test(x)) throw new Error(`“${x}” — letters only, up to 8 chars`); });
    const word = String(w || '').trim().toLowerCase();
    if (!/^[a-z]{1,8}$/.test(word)) throw new Error('Add a search word (letters only) after the ";"');
    return { products, word };
  },
  run({ products, word }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, top: [] }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids }, top: [...n.top] })), ...extra });
    const sorted = [...products].sort();

    snap(3, `Sort the products first: ${sorted.join(', ')}. Sorted order is what makes "first 3 seen" the lexicographically smallest 3.`, S({ cur: 0, path: [0] }));
    sorted.forEach(w2 => {
      let node = 0; const path = [0];
      [...w2].forEach(ch => {
        if (nodes[node].kids[ch] === undefined) { nodes.push({ ch, kids: {}, top: [] }); nodes[node].kids[ch] = nodes.length - 1; }
        node = nodes[node].kids[ch]; path.push(node);
        if (nodes[node].top.length < 3) {
          nodes[node].top.push(w2);
          snap(8, `"${w2}" is still among the first 3 seen here — add it to this node's top-3.`, S({ cur: node, path: [...path], word: w2 }));
        } else {
          snap(7, `This node's top-3 is already full — "${w2}" doesn't get added here.`, S({ cur: node, path: [...path], word: w2 }));
        }
      });
    });

    const out = [];
    let node = 0; const path = [0];
    snap(12, `Now type "${word}" one character at a time.`, S({ cur: 0, path: [0], out: [] }));
    for (const ch of word) {
      node = node !== null && nodes[node].kids[ch] !== undefined ? nodes[node].kids[ch] : null;
      if (node !== null) path.push(node);
      const top = node !== null ? nodes[node].top : [];
      out.push(top);
      const typedSoFar = word.slice(0, out.length);
      snap(15, node !== null ? `At "${typedSoFar}" so far — this node's top-3: ${top.length ? top.join(', ') : '(none)'}.` : `No branch left for "${typedSoFar}" — no suggestions for the rest.`, S({ cur: node, path: node !== null ? [...path] : [], out: out.map(x => [...x]) }));
    }
    snap(16, `Full result: ${out.map(l => `[${l.join(', ')}]`).join('  ')}`, S({ out: out.map(x => [...x]), final: true }));
    return F;
  },
  height: (w, last, frames) => charTrieHeightFromFrames(frames),
  draw(ctx, c, f, P) {
    charTrieDraw(ctx, c, P, f.nodes, { cur: f.cur, path: f.path, subLabel: id => f.nodes[id].top.length || null });
    const lastTop = f.out && f.out.length ? f.out[f.out.length - 1] : null;
    if (lastTop) D.text(ctx, `suggestions: ${lastTop.length ? lastTop.join(', ') : '(none)'}`, c.w / 2, c.h - 16, { color: P.ok, size: 12, align: 'center', weight: 650 });
  },
});
