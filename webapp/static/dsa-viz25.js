/* ============================================================================
   Visualizations for 23_string_algorithms — the 7 problems that were
   fallback-only (seq 001 "Find the Index of the First Occurrence in a
   String" already has a spec, "KMP: never re-read the text" in
   dsa-viz3.js; left untouched).
   Reuses dpBox/dpStrip/dpPanel/dpWrap (dsa-viz24.js) and chipRow
   (dsa-viz16.js) — both plain `function` declarations, so they're already
   global by the time this file (loaded later) runs.
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
function saPtrHTML(label, color) {
  return `<div class="pointer" style="color:${color || 'var(--accent)'}">${label}</div>`;
}
function saCharBox(ch, sub, cls, ptrs) {
  return `
  <div class="array-node ${cls || ''}">
      ${(ptrs || []).join('')}
      ${esc(ch)}
      <div class="node-index">${sub}</div>
  </div>`;
}
function saCharStrip(chars, { subOf = (c, i) => i, clsOf = () => '', ptrsOf = () => [] } = {}) {
  return chars.map((c, i) => saCharBox(c, subOf(c, i), clsOf(c, i), ptrsOf(c, i))).join('');
}

/* Builds the KMP failure/LPS table for `pat`, one frame per decision, via
   a caller-supplied `emit(i, len, lps, note)`. Shared by 002 and 006. */
function saBuildLpsTraced(pat, emit) {
  const m = pat.length;
  const lps = new Array(m).fill(0);
  let len = 0, i = 1;
  emit(0, 0, [...lps], `lps[0] is always 0 — a single character has no proper prefix that is also a suffix.`);
  while (i < m) {
    if (pat[i] === pat[len]) {
      len++; lps[i] = len; i++;
      emit(i - 1, len, [...lps], `pattern[${i - 1}] extends the match: the prefix that is also a suffix here is now ${len} long.`);
    } else if (len) {
      const from = len;
      len = lps[len - 1];
      emit(i, len, [...lps], `Mismatch at pattern[${i}] — fall back through the table from ${from} to ${len} instead of restarting at 0.`);
    } else {
      lps[i] = 0; i++;
      emit(i - 1, 0, [...lps], `No prefix/suffix match here — lps[${i - 1}] stays 0.`);
    }
  }
  return lps;
}

/* ============================== 002 · Repeated Substring Pattern ========== */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Repeated Substring Pattern', short: 'Repeated Substring',
  idea: 'Build the KMP failure table (lps) for <code>s</code> against itself. <code>lps[n-1]</code> is the length of the longest prefix of <code>s</code> that is also a suffix. If that overlap is nonzero, the "leftover" length <code>period = n - lps[n-1]</code> is a candidate repeating unit — <code>s</code> is built from whole copies of it exactly when <code>n % period == 0</code>.',
  complexity: 'Time O(n) building the failure table · Space O(n)',
  input: 'abcabcabcabc', hint: 'a string, up to 16 characters',
  code: [
    'def repeatedSubstringPattern(s):',
    '    lps = build_lps(s)',
    '    n = len(s)',
    '    period = n - lps[-1]',
    '    return lps[-1] != 0 and n % period == 0',
  ],
  parse(s) {
    const str = String(s || '').trim();
    if (!str) throw new Error('Enter a string');
    if (str.length > 16) throw new Error('Keep the string to 16 characters for visualization');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const chars = [...str];
    domPushState(seq, {
      line: 2, color: 'default', chars, lps: chars.map(() => 0), i: -1, len: -1,
      explTitle: 'Build the failure table', explText: `We build the KMP prefix table for "${str}" against itself.`,
      pause: true,
    }, ctx);
    saBuildLpsTraced(str, (i, len, lps, note) => {
      domPushState(seq, { line: 2, color: 'blue', chars, lps, i, len, explTitle: 'Building lps', explText: note }, ctx);
    });
    const finalLps = saBuildLpsTraced(str, () => {});
    const n = chars.length, last = finalLps[n - 1], period = n - last;
    const divides = last !== 0 && n % period === 0;
    domPushState(seq, {
      line: 4, color: divides ? 'emerald' : 'rose', chars, lps: finalLps, i: n - 1, len: last, period, divides,
      explTitle: 'Check the period',
      explText: `lps[${n - 1}] = ${last}, so the candidate repeating unit is period = ${n} − ${last} = ${period}. ` +
        (last === 0 ? `The overlap is 0, so there is no repeating unit shorter than the whole string — return False.`
          : `${n} % ${period} ${divides ? '== 0' : '!= 0'}: ${divides ? `the string is exactly ${n / period} copies of the first ${period} characters — return True.` : `the string does not divide evenly into copies of that length — return False.`}`),
      pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = saCharStrip(s.chars, {
      clsOf: (c, idx) => idx === s.i ? 'active-k' : (s.period && idx < s.period ? 'merged' : ''),
      ptrsOf: (c, idx) => idx === s.i ? [saPtrHTML('↓ i', '#34d399')] : (idx === s.len ? [saPtrHTML('↓ len', 'var(--accent)')] : []),
    });
    const lpsStrip = saCharStrip(s.lps.map(String), { clsOf: (v, idx) => idx === s.i ? 'active-1' : '' });
    container.innerHTML = dpWrap(
      dpPanel('s', strip),
      dpPanel('lps (failure table)', lpsStrip),
      s.period ? `<div class="glass-panel" style="padding:12px 15px; color:${s.divides ? '#10b981' : '#ef4444'}; font-weight:600;">period = ${s.period} → ${s.divides ? 'True' : 'False'}</div>` : '',
    );
  },
});

/* ================================ 003 · String to Integer (atoi) ========== */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'String to Integer (atoi)', short: 'atoi',
  idea: 'A small state machine over the characters: skip leading spaces, read at most one sign, then consume digits while accumulating the number, and finally clamp to the 32-bit signed range.',
  complexity: 'Time O(n) · Space O(1)',
  input: '   -42abc', hint: 'a string to parse, up to 20 characters',
  code: [
    'def myAtoi(s):',
    '    i = 0',
    '    while i < len(s) and s[i] == " ": i += 1',
    '    sign = 1',
    '    if i < len(s) and s[i] in "+-":',
    '        sign = -1 if s[i] == "-" else 1; i += 1',
    '    num = 0',
    '    while i < len(s) and s[i].isdigit():',
    '        num = num * 10 + int(s[i]); i += 1',
    '    num *= sign',
    '    return max(INT_MIN, min(INT_MAX, num))',
  ],
  parse(s) {
    if (s == null || s === '') throw new Error('Enter a string to parse');
    if (s.length > 20) throw new Error('Keep the string to 20 characters for visualization');
    return { str: s };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const chars = [...str];
    const INT_MIN = -(2 ** 31), INT_MAX = 2 ** 31 - 1;
    let i = 0;
    domPushState(seq, { line: 2, color: 'default', chars, i: -1, phase: 'start', num: 0, sign: 1, explTitle: 'Start', explText: `Parsing "${str}".` }, ctx);
    while (i < chars.length && chars[i] === ' ') {
      domPushState(seq, { line: 3, color: 'default', chars, i, phase: 'ws', num: 0, sign: 1, explTitle: 'Skip whitespace', explText: `chars[${i}] is a space — skip it.` }, ctx);
      i++;
    }
    let sign = 1;
    if (i < chars.length && (chars[i] === '+' || chars[i] === '-')) {
      sign = chars[i] === '-' ? -1 : 1;
      domPushState(seq, { line: 5, color: 'amber', chars, i, phase: 'sign', num: 0, sign, explTitle: 'Optional sign', explText: `chars[${i}] = '${chars[i]}' — sign is now ${sign > 0 ? '+' : '−'}.` }, ctx);
      i++;
    } else {
      domPushState(seq, { line: 5, color: 'default', chars, i, phase: 'sign', num: 0, sign, explTitle: 'No sign', explText: `No '+'/'-' here — sign stays +.` }, ctx);
    }
    let num = 0;
    while (i < chars.length && /[0-9]/.test(chars[i])) {
      num = num * 10 + (chars[i].charCodeAt(0) - 48);
      domPushState(seq, { line: 8, color: 'blue', chars, i, phase: 'digits', num, sign, explTitle: 'Consume a digit', explText: `chars[${i}] = '${chars[i]}' — running value is now ${num}.` }, ctx);
      i++;
    }
    let signed = num * sign;
    const clamped = Math.max(INT_MIN, Math.min(INT_MAX, signed));
    domPushState(seq, {
      line: 10, color: clamped !== signed ? 'rose' : 'emerald', chars, i, phase: 'done', num: clamped, sign,
      explTitle: 'Sign and clamp',
      explText: clamped !== signed
        ? `${sign > 0 ? '' : '−'}${num} is outside the 32-bit signed range, so it is clamped to ${clamped}.`
        : `Apply the sign: ${sign > 0 ? '' : '−'}${num} = ${clamped}. Within range — return it as is.`,
      pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = saCharStrip(s.chars.map(c => c === ' ' ? '·' : c), {
      clsOf: (c, idx) => idx === s.i ? 'active-k' : (idx < s.i ? 'merged' : ''),
      ptrsOf: (c, idx) => idx === s.i ? [saPtrHTML('↓ i', '#34d399')] : [],
    });
    container.innerHTML = dpWrap(
      dpPanel('s', strip),
      `<div class="glass-panel" style="padding:12px 15px; display:flex; gap:24px; font-weight:600;">
        <span>phase: <span style="color:var(--accent)">${s.phase}</span></span>
        <span>sign: ${s.sign > 0 ? '+' : '−'}</span>
        <span>value: <span style="color:#10b981">${s.num}</span></span>
      </div>`,
    );
  },
});

/* ================================ 004 · Repeated DNA Sequences ============ */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Repeated DNA Sequences', short: 'Repeated DNA',
  idea: 'Slide a fixed 10-character window across the string. A rolling 2-bit-per-base hash (A/C/G/T → 0-3) lets the window\'s hash update in O(1) as it slides. The first time a hash repeats, that 10-mer is reported.',
  complexity: 'Time O(n) · Space O(n) for the seen/repeated hash sets',
  input: 'AAAAACCCCCAAAAACCCCC', hint: 'a DNA string (A/C/G/T only), 10-26 characters',
  code: [
    'def findRepeatedDnaSequences(s):',
    '    seen, repeated = set(), set()',
    '    for i in range(len(s) - 9):',
    '        window = s[i:i+10]',
    '        h = encode(window)      # rolling 2-bit hash',
    '        if h in seen:',
    '            repeated.add(h)',
    '        else:',
    '            seen.add(h)',
    '    return [decode(h) for h in repeated]',
  ],
  parse(s) {
    const str = String(s || '').trim().toUpperCase();
    if (!/^[ACGT]+$/.test(str)) throw new Error('Use only A/C/G/T characters');
    if (str.length < 10 || str.length > 26) throw new Error('Use between 10 and 26 characters so a 10-window makes sense');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const chars = [...str];
    const seen = new Set(), repeated = new Set();
    domPushState(seq, { line: 2, color: 'default', chars, win: -1, seen: [], repeated: [], explTitle: 'Start', explText: `Two hash sets: "seen" (windows we've met once) and "repeated" (windows we've met twice).` }, ctx);
    for (let i = 0; i <= chars.length - 10; i++) {
      const win = str.slice(i, i + 10);
      const isRepeat = seen.has(win);
      if (isRepeat) repeated.add(win); else seen.add(win);
      domPushState(seq, {
        line: isRepeat ? 6 : 8, color: isRepeat ? 'rose' : 'blue', chars, win: i, seen: [...seen], repeated: [...repeated],
        explTitle: isRepeat ? 'Seen before!' : 'New window',
        explText: `Window at index ${i}: "${win}" — ${isRepeat ? `already in "seen", so it moves to "repeated".` : `first time we've met it — add to "seen".`}`,
      }, ctx);
    }
    domPushState(seq, { line: 10, color: 'emerald', chars, win: -1, seen: [...seen], repeated: [...repeated], explTitle: 'Done', explText: `${repeated.size} sequence${repeated.size === 1 ? '' : 's'} repeated: ${[...repeated].join(', ') || '(none)'}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = saCharStrip(s.chars, {
      clsOf: (c, idx) => (s.win >= 0 && idx >= s.win && idx < s.win + 10) ? 'active-k' : '',
    });
    container.innerHTML = dpWrap(
      dpPanel('s', strip),
      `<div class="glass-panel" style="padding:12px 15px;">
        <div class="panel-heading">seen once</div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; font-family:var(--mono); font-size:13px;">${s.seen.map(w => `<span style="padding:3px 8px; border-radius:6px; background:var(--bg-card);">${w}</span>`).join('') || '<span style="color:var(--text-dim)">(empty)</span>'}</div>
      </div>`,
      `<div class="glass-panel" style="padding:12px 15px;">
        <div class="panel-heading">repeated</div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; font-family:var(--mono); font-size:13px;">${s.repeated.map(w => `<span style="padding:3px 8px; border-radius:6px; background:var(--rose,#ef4444); color:#fff;">${w}</span>`).join('') || '<span style="color:var(--text-dim)">(empty)</span>'}</div>
      </div>`,
    );
  },
});

/* =============================== 005 · Repeated String Match =============== */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Repeated String Match', short: 'Repeated String Match',
  idea: 'If <code>b</code> can appear in some number of copies of <code>a</code> laid end to end, it appears within the first <code>q = ceil(len(b) / len(a))</code> copies — or that plus one more, in case the match straddles a boundary. So build exactly those two candidates and check containment; no need to try more copies.',
  complexity: 'Time O((|a|+|b|) × |a|) for the containment check · Space O(|a|·q)',
  input: 'abcd;cdabcdab', hint: 'a ; b',
  code: [
    'def repeatedStringMatch(a, b):',
    '    if not set(b) <= set(a): return -1',
    '    q = ceil(len(b) / len(a))',
    '    candidate = a * q',
    '    if b in candidate: return q',
    '    candidate += a',
    '    if b in candidate: return q + 1',
    '    return -1',
  ],
  parse(s) {
    const [a, b] = String(s || '').split(';').map(x => (x || '').trim());
    if (!a || !b) throw new Error('Enter a ; b');
    if (a.length > 8 || b.length > 20) throw new Error('Keep a to 8 chars and b to 20 chars');
    return { a, b };
  },
  buildStates({ a, b }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const setA = new Set(a), setB = new Set(b);
    const superset = [...setB].every(c => setA.has(c));
    domPushState(seq, { line: 2, color: superset ? 'default' : 'rose', a, b, candidate: '', q: 0, contains: null, explTitle: 'Character check', explText: superset ? `Every character of b already appears in a — continue.` : `b has a character a never uses — impossible, return -1.`, pause: !superset }, ctx);
    if (!superset) return seq;
    const q = Math.ceil(b.length / a.length);
    let candidate = a.repeat(q);
    domPushState(seq, { line: 4, color: 'blue', a, b, candidate, q, contains: null, explTitle: `Build ${q} cop${q === 1 ? 'y' : 'ies'}`, explText: `q = ceil(${b.length} / ${a.length}) = ${q}. candidate = "${candidate}" (length ${candidate.length}).` }, ctx);
    let contains = candidate.includes(b);
    domPushState(seq, { line: 5, color: contains ? 'emerald' : 'default', a, b, candidate, q, contains, explTitle: 'Check containment', explText: contains ? `"${b}" is inside candidate — return ${q}.` : `Not found yet — a match could straddle the end of this candidate.`, pause: contains }, ctx);
    if (contains) return seq;
    candidate += a;
    domPushState(seq, { line: 6, color: 'amber', a, b, candidate, q: q + 1, contains: null, explTitle: 'One more copy', explText: `candidate += a → "${candidate}" (length ${candidate.length}).` }, ctx);
    contains = candidate.includes(b);
    domPushState(seq, { line: 7, color: contains ? 'emerald' : 'rose', a, b, candidate, q: q + 1, contains, explTitle: 'Final check', explText: contains ? `Found — return ${q + 1}.` : `Still not found, and one more copy can never help beyond this — return -1.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const candStrip = s.candidate ? saCharStrip([...s.candidate], {
      clsOf: (c, idx) => s.contains ? 'merged' : '',
    }) : '<div style="padding:20px; color:var(--text-dim);">(not built yet)</div>';
    container.innerHTML = dpWrap(
      dpPanel(`b = "${s.b}"`, saCharStrip([...s.b])),
      dpPanel(`candidate (${s.q ? `${s.q} × a` : ''})`, candStrip),
      s.contains !== null ? `<div class="glass-panel" style="padding:12px 15px; color:${s.contains ? '#10b981' : '#ef4444'}; font-weight:600;">${s.contains ? `b found → result ${s.q}` : 'not found yet'}</div>` : '',
    );
  },
});

/* ================================= 006 · Shortest Palindrome =============== */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Shortest Palindrome', short: 'Shortest Palindrome',
  idea: 'The shortest palindrome is <code>s</code> with the minimum number of characters prepended. Build <code>t = s + "#" + reverse(s)</code> (the "#" stops the two halves overlapping) and run KMP\'s failure table on <code>t</code>. <code>lps[-1]</code> is exactly the length of the longest prefix of <code>s</code> that is already a palindrome — everything after it, reversed, is what must be prepended.',
  complexity: 'Time O(n) · Space O(n)',
  input: 'aacecaaa', hint: 'a string, up to 12 characters',
  code: [
    'def shortestPalindrome(s):',
    '    t = s + "#" + s[::-1]',
    '    lps = build_lps(t)',
    '    longest = lps[-1]',
    '    return s[longest:][::-1] + s',
  ],
  parse(s) {
    const str = String(s || '').trim();
    if (!str) throw new Error('Enter a string');
    if (str.length > 12) throw new Error('Keep the string to 12 characters for visualization');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const rev = [...str].reverse().join('');
    const t = `${str}#${rev}`;
    const tChars = [...t];
    domPushState(seq, { line: 2, color: 'default', chars: tChars, lps: tChars.map(() => 0), i: -1, sep: str.length, explTitle: 'Build t', explText: `t = "${str}" + "#" + "${rev}" = "${t}". The "#" guarantees the failure table can never see past the whole of s.` }, ctx);
    saBuildLpsTraced(t, (i, len, lps, note) => {
      domPushState(seq, { line: 3, color: 'blue', chars: tChars, lps, i, sep: str.length, explTitle: 'Building lps(t)', explText: note }, ctx);
    });
    const finalLps = saBuildLpsTraced(t, () => {});
    const longest = finalLps[t.length - 1];
    const toPrepend = [...str.slice(longest)].reverse().join('');
    const answer = toPrepend + str;
    domPushState(seq, {
      line: 4, color: 'emerald', chars: tChars, lps: finalLps, i: t.length - 1, sep: str.length, longest, toPrepend, answer,
      explTitle: 'Read off the answer',
      explText: `lps[-1] = ${longest}: "${str.slice(0, longest)}" is the longest prefix of s that is already a palindrome. Reverse the rest ("${str.slice(longest)}" → "${toPrepend}") and prepend it: "${toPrepend}" + "${str}" = "${answer}".`,
      pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = saCharStrip(s.chars, {
      clsOf: (c, idx) => idx === s.i ? 'active-k' : (idx === s.sep ? 'active-1' : (s.longest && idx < s.longest ? 'merged' : '')),
    });
    const lpsStrip = saCharStrip(s.lps.map(String), { clsOf: (v, idx) => idx === s.i ? 'active-1' : '' });
    return container.innerHTML = dpWrap(
      dpPanel('t = s + "#" + reverse(s)', strip),
      dpPanel('lps(t)', lpsStrip),
      s.answer ? `<div class="glass-panel" style="padding:12px 15px; font-weight:600; color:#10b981;">answer: "${s.answer}"</div>` : '',
    );
  },
});

/* ============================ 007 · Longest Duplicate Substring ============ */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Longest Duplicate Substring', short: 'Longest Dup Substring',
  idea: 'Binary search on the answer\'s length. For a candidate length L, slide a Rabin-Karp rolling hash across every substring of that length in O(n); a hash match is only a <em>candidate</em> duplicate, so it is always verified with a direct character comparison before being trusted. If some duplicate of length L exists, try longer; otherwise try shorter.',
  complexity: 'Time O(n log n) expected (hashing) · Space O(n)',
  input: 'banana', hint: 'a string, up to 16 lowercase letters',
  code: [
    'def longestDupSubstring(s):',
    '    def search(L):              # any duplicate of length L?',
    '        seen = {}',
    '        for start in range(len(s) - L + 1):',
    '            h = hash(s[start:start+L])       # rolling',
    '            for idx in seen.get(h, []):',
    '                if s[idx:idx+L] == s[start:start+L]:',
    '                    return start        # verified, not just hash-equal',
    '            seen.setdefault(h, []).append(start)',
    '        return -1',
    '    lo, hi = 1, len(s) - 1',
    '    best_start, best_len = -1, 0',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        pos = search(mid)',
    '        if pos != -1: best_start, best_len, lo = pos, mid, mid + 1',
    '        else: hi = mid - 1',
    '    return s[best_start:best_start+best_len]',
  ],
  parse(s) {
    const str = String(s || '').trim().toLowerCase();
    if (!/^[a-z]+$/.test(str)) throw new Error('Use lowercase letters only');
    if (str.length < 2 || str.length > 16) throw new Error('Use between 2 and 16 characters');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const chars = [...str];
    const n = chars.length;
    function search(L, emit) {
      // Uses the substring itself as the map key for teaching clarity — the real
      // solution keys by a numeric rolling hash instead (see the code panel), but
      // the collision/verify shape taught here is identical either way.
      const seen = new Map();
      for (let start = 0; start + L <= n; start++) {
        const cand = str.slice(start, start + L);
        let hit = -1;
        for (const idx of (seen.get(cand) || [])) {
          emit({ compareIdx: idx, start, L, verdict: str.slice(idx, idx + L) === cand }, `Hash matches a previous window at ${idx} — verify by direct comparison: ${str.slice(idx, idx + L) === cand ? 'confirmed duplicate.' : 'false positive, keep going.'}`);
          if (str.slice(idx, idx + L) === cand) { hit = idx; break; }
        }
        if (hit !== -1) return hit;
        if (!seen.has(cand)) { seen.set(cand, []); emit({ start, L, newWindow: true }, `Window "${cand}" at ${start} — new, remember it.`); }
        seen.get(cand).push(start);
      }
      return -1;
    }
    let lo = 1, hi = n - 1, bestStart = -1, bestLen = 0;
    domPushState(seq, { line: 11, color: 'default', chars, lo, hi, mid: null, explTitle: 'Binary search on length', explText: `Search for the longest length L that has a duplicate, between 1 and ${hi}.` }, ctx);
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      domPushState(seq, { line: 14, color: 'blue', chars, lo, hi, mid, explTitle: `Try length ${mid}`, explText: `mid = (${lo} + ${hi}) / 2 = ${mid}. Does a duplicate substring of length ${mid} exist?` }, ctx);
      let pos = search(mid, (extra, note) => {
        domPushState(seq, { line: 7, color: extra.verdict === false ? 'rose' : (extra.newWindow ? 'default' : 'emerald'), chars, lo, hi, mid, ...extra, explTitle: 'Inside search()', explText: note }, ctx);
      });
      if (pos !== -1) {
        bestStart = pos; bestLen = mid; lo = mid + 1;
        domPushState(seq, { line: 15, color: 'emerald', chars, lo, hi, mid, found: pos, bestLen, explTitle: 'Duplicate found', explText: `Length ${mid} has a duplicate at index ${pos} — remember it, then try a longer length.` }, ctx);
      } else {
        hi = mid - 1;
        domPushState(seq, { line: 16, color: 'rose', chars, lo, hi, mid, bestLen, explTitle: 'No duplicate', explText: `No duplicate of length ${mid} — try a shorter length.` }, ctx);
      }
    }
    domPushState(seq, {
      line: 17, color: 'emerald', chars, lo, hi, mid: null, bestStart, bestLen,
      explTitle: 'Done', explText: bestStart === -1 ? 'No duplicate substring exists at all.' : `Longest duplicate substring: "${str.slice(bestStart, bestStart + bestLen)}" (length ${bestLen}).`,
      pause: true,
    }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const highlight = new Set();
    if (s.start != null && s.L) for (let k = 0; k < s.L; k++) highlight.add(s.start + k);
    if (s.compareIdx != null && s.L) for (let k = 0; k < s.L; k++) highlight.add(s.compareIdx + k);
    if (s.found != null && s.bestLen) for (let k = 0; k < s.bestLen; k++) highlight.add(s.found + k);
    if (s.bestStart != null && s.bestStart >= 0 && s.bestLen) for (let k = 0; k < s.bestLen; k++) highlight.add(s.bestStart + k);
    const strip = saCharStrip(s.chars, {
      clsOf: (c, idx) => s.compareIdx != null && idx >= s.compareIdx && idx < s.compareIdx + s.L ? 'active-1'
        : (s.start != null && idx >= s.start && idx < s.start + s.L) ? 'active-k'
        : (highlight.has(idx) ? 'merged' : ''),
    });
    const rangeChips = chipRow(
      Array.from({ length: s.hi - s.lo + 3 }, (_, k) => s.lo - 1 + k).filter(v => v >= 1),
      { cls: v => v === s.mid ? 'active-k' : (v === s.lo ? 'active-1' : (v === s.hi ? 'merged' : '')) },
    );
    container.innerHTML = dpWrap(
      dpPanel('s', strip),
      `<div class="glass-panel" style="padding:12px 15px;"><div class="panel-heading">candidate length range [lo, hi], mid highlighted</div>${rangeChips}</div>`,
      s.bestStart != null && s.bestStart >= 0 ? `<div class="glass-panel" style="padding:12px 15px; font-weight:600; color:#10b981;">best so far: "${s.chars.slice(s.bestStart, s.bestStart + s.bestLen).join('')}" (length ${s.bestLen})</div>` : '',
    );
  },
});

/* =================================== 008 · Palindrome Pairs ================ */
defineAlgoDom('23_string_algorithms', {
  type: 'dom',
  title: 'Palindrome Pairs', short: 'Palindrome Pairs',
  idea: 'For each word, try every split point. If the <b>prefix</b> up to the split is itself a palindrome, then pairing with some other word equal to the <b>reverse of the suffix</b> makes (other, this) a palindrome — the palindromic prefix just mirrors onto itself in the middle. Symmetrically, if the <b>suffix</b> is a palindrome, pairing with the reverse of the <b>prefix</b> makes (this, other) work.',
  complexity: 'Time O(n · k²) for n words of length up to k · Space O(n·k) for the word→index map',
  input: 'abcd,dcba,lls,s,sssll', hint: 'comma-separated words, up to 6 words, 8 characters each',
  code: [
    'def palindromePairs(words):',
    '    idx = {w: i for i, w in enumerate(words)}',
    '    result = []',
    '    for i, word in enumerate(words):',
    '        for j in range(len(word) + 1):',
    '            if is_pal(word, 0, j - 1):          # prefix is a palindrome',
    '                k = idx.get(word[j:][::-1])',
    '                if k is not None and k != i: result.append([k, i])',
    '            if j != len(word) and is_pal(word, j, len(word) - 1):  # suffix',
    '                k = idx.get(word[:j][::-1])',
    '                if k is not None and k != i: result.append([i, k])',
    '    return result',
  ],
  parse(s) {
    const words = String(s || '').split(',').map(w => w.trim()).filter(Boolean);
    if (words.length < 2) throw new Error('Enter at least 2 comma-separated words');
    if (words.length > 6) throw new Error('Use at most 6 words');
    words.forEach(w => { if (w.length > 8) throw new Error(`"${w}" — keep each word to 8 characters`); });
    return { words };
  },
  buildStates({ words }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const idx = new Map(words.map((w, i) => [w, i]));
    const isPal = (w, lo, hi) => { while (lo < hi) { if (w[lo] !== w[hi]) return false; lo++; hi--; } return true; };
    const pairs = [];
    domPushState(seq, { line: 2, color: 'default', words, i: -1, j: -1, pairs: [], explTitle: 'Start', explText: `Word → index map built. We'll try every (word, split point) pair.` }, ctx);
    words.forEach((word, i) => {
      const n = word.length;
      for (let j = 0; j <= n; j++) {
        if (isPal(word, 0, j - 1)) {
          const revSuffix = [...word.slice(j)].reverse().join('');
          const k = idx.has(revSuffix) ? idx.get(revSuffix) : null;
          if (k != null && k !== i) {
            pairs.push([k, i]);
            domPushState(seq, { line: 6, color: 'emerald', words, i, j, case: 'A', pairs: [...pairs], explTitle: 'Pair found (case A)', explText: `"${word.slice(0, j) || '(empty)'}" is a palindrome; reverse of the rest ("${word.slice(j)}") is "${revSuffix}" = words[${k}] — so (${k}, ${i}) is a palindrome pair.` }, ctx);
          } else {
            domPushState(seq, { line: 5, color: 'blue', words, i, j, case: 'A', pairs: [...pairs], explTitle: 'Case A: check prefix', explText: `Prefix "${word.slice(0, j) || '(empty)'}" of "${word}" is a palindrome. Need reverse of "${word.slice(j)}" = "${revSuffix}" in the list — ${idx.has(revSuffix) ? 'found, but it is this same word.' : 'not present.'}` }, ctx);
          }
        }
        if (j !== n && isPal(word, j, n - 1)) {
          const revPrefix = [...word.slice(0, j)].reverse().join('');
          const k = idx.has(revPrefix) ? idx.get(revPrefix) : null;
          if (k != null && k !== i) {
            pairs.push([i, k]);
            domPushState(seq, { line: 9, color: 'emerald', words, i, j, case: 'B', pairs: [...pairs], explTitle: 'Pair found (case B)', explText: `"${word.slice(j)}" is a palindrome; reverse of the rest ("${word.slice(0, j)}") is "${revPrefix}" = words[${k}] — so (${i}, ${k}) is a palindrome pair.` }, ctx);
          } else {
            domPushState(seq, { line: 8, color: 'blue', words, i, j, case: 'B', pairs: [...pairs], explTitle: 'Case B: check suffix', explText: `Suffix "${word.slice(j)}" of "${word}" is a palindrome. Need reverse of "${word.slice(0, j)}" = "${revPrefix}" in the list — ${idx.has(revPrefix) ? 'found, but it is this same word.' : 'not present.'}` }, ctx);
          }
        }
      }
    });
    domPushState(seq, { line: 11, color: 'emerald', words, i: -1, j: -1, pairs: [...pairs], explTitle: 'Done', explText: `${pairs.length} pair${pairs.length === 1 ? '' : 's'} found: ${pairs.map(p => `[${p[0]},${p[1]}]`).join(', ') || '(none)'}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const wordChips = chipRow(s.words.map((w, i) => `${i}: ${w}`), { cls: (label, i) => i === s.i ? 'active-k' : '' });
    const split = s.i >= 0 && s.j >= 0 ? `<div class="glass-panel" style="padding:12px 15px;">
      <div class="panel-heading">splitting "${s.words[s.i]}" at ${s.j} (case ${s.case})</div>
      <div style="display:flex; gap:2px; font-family:var(--mono); font-size:15px;">
        <span style="padding:6px 8px; border-radius:6px 0 0 6px; background:var(--accent); color:#fff;">${esc(s.words[s.i].slice(0, s.j)) || '∅'}</span>
        <span style="padding:6px 8px; border-radius:0 6px 6px 0; background:var(--bg-card);">${esc(s.words[s.i].slice(s.j)) || '∅'}</span>
      </div>
    </div>` : '';
    container.innerHTML = dpWrap(
      `<div class="glass-panel" style="padding:12px 15px;"><div class="panel-heading">words</div>${wordChips}</div>`,
      split,
      `<div class="glass-panel" style="padding:12px 15px;">
        <div class="panel-heading">pairs found</div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; font-family:var(--mono); font-size:13px;">${s.pairs.map(p => `<span style="padding:3px 8px; border-radius:6px; background:var(--emerald,#10b981); color:#fff;">[${p[0]}, ${p[1]}]</span>`).join('') || '<span style="color:var(--text-dim)">(none yet)</span>'}</div>
      </div>`,
    );
  },
});
