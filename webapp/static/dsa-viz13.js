/* ============================================================================
   Visualizations for 09_recursion_backtracking (Part 3 - Combination Sums)
   ========================================================================= */
"use strict";

defineAlgoDom("09_recursion_backtracking", {
  id: "007_combination_sum",
  title: "Combination Sum",
  type: "dom",
  input: "2, 3, 6, 7 ; 7",
  
  idea: 'Because we can reuse elements, when we recurse, we pass `i` (not `i + 1`). To prevent duplicate combinations, we keep a `start` index. Sort candidates to prune early.',
  complexity: 'Time O(N^(T/M)) · Space O(T/M)',
  code: [
    'def combinationSum(candidates, target):',
    '    results, path = [], []',
    '    candidates.sort()',
    '    def backtrack(start, remaining):',
    '        if remaining == 0:',
    '            results.append(path[:])',
    '            return',
    '        for i in range(start, len(candidates)):',
    '            if candidates[i] > remaining:',
    '                break',
    '            path.append(candidates[i])',
    '            backtrack(i, remaining - candidates[i])',
    '            path.pop()',
    '    backtrack(0, target)',
    '    return results'
  ],

  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Provide candidates and target separated by semicolon (e.g., 2, 3, 6, 7 ; 7)');
    const cands = avNums(parts[0], 20, "candidates").sort((a, b) => a - b);
    const target = avNum(parts[1], "target");
    return { cands, target };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { cands, target } = parsed;
    const n = cands.length;
    const path = [];
    const results = [];

    const snapshot = (kind, line, color, title, text, activeIdx = -1, start = -1) => {
      domPushState(seq, {
        kind, line, color,
        cands: [...cands],
        target,
        path: [...path],
        results: JSON.parse(JSON.stringify(results)),
        activeIdx,
        start,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 3, "default", "Initialization", `Sorted candidates: [${cands.join(", ")}]. Target sum: ${target}.`, -1, -1);

    function backtrack(start, remaining) {
      if (remaining === 0) {
        results.push([...path]);
        snapshot("record", 6, "emerald", "Target Reached!", `Remaining is 0. Adding [${path.join(", ")}] to results.`, -1, start);
        return;
      }

      for (let i = start; i < n; i++) {
        snapshot("loop", 8, "default", "Loop Iteration", `Checking cands[${i}] = ${cands[i]}. Remaining = ${remaining}. start is ${start}.`, i, start);

        if (cands[i] > remaining) {
          snapshot("prune", 10, "red", "Pruning (Break)", `cands[${i}] (${cands[i]}) > remaining (${remaining}). Since array is sorted, all subsequent candidates will also be too big. Break loop.`, i, start);
          break; 
        }

        path.push(cands[i]);
        snapshot("choose", 11, "blue", "Choose", `Choose ${cands[i]}. Path becomes [${path.join(", ")}]. Calling backtrack(i, remaining - ${cands[i]}).`, i, start);

        backtrack(i, remaining - cands[i]);

        let popped = path.pop();
        snapshot("unchoose", 13, "amber", "Unchoose (Backtrack)", `Backtracking from ${popped}. Path reverts to [${path.join(", ")}].`, i, start);
      }
    }

    backtrack(0, target);
    snapshot("done", 15, "emerald", "Finished", `Found ${results.length} combination(s) that sum to ${target}.`, -1, -1);

    return seq;
  },

  renderDOM(container, s, spec) {
    const getCandsHTML = (cands, start, currI) => {
        return cands.map((val, idx) => {
            let cls = '';
            let ptrs = [];
            
            if (idx === currI) {
                cls = s.kind === 'prune' ? 'active-red' : 'active-k';
                ptrs.push(`<div class="pointer" style="color:var(--amber); top:-25px;">↓ i</div>`);
            }
            if (idx === start) {
                cls = cls || 'active-1';
                ptrs.push(`<div class="pointer" style="color:var(--blue); bottom:-25px; left:5px;">↑ start</div>`);
            }
            
            if (idx < start) {
                cls = cls || 'merged';
            }
            
            return `
            <div class="array-node ${cls}" style="position:relative; opacity: ${idx < start ? 0.4 : 1}; margin-bottom: 20px;">
                ${ptrs.join('')}
                ${val}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getPathHTML = (path) => {
        if (path.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return path.map(val => `
            <div class="array-node active-1" style="background:var(--blue); color:white; border-color:white;">
                ${val}
            </div>
        `).join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${p.join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    const pathSum = s.path.reduce((a, b) => a + b, 0);
    const remaining = s.target - pathSum;

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface); padding:15px; border-radius:8px; border-left:4px solid var(--blue);">
                  <div>
                      <div style="font-size:12px; color:var(--text-dim); text-transform:uppercase;">Target</div>
                      <div style="font-size:18px; font-weight:bold; color:var(--text-bright);">${s.target}</div>
                  </div>
                  <div style="text-align:right;">
                      <div style="font-size:12px; color:var(--text-dim); text-transform:uppercase;">Remaining</div>
                      <div style="font-size:18px; font-weight:bold; color:${remaining === 0 ? 'var(--emerald)' : remaining < 0 ? 'var(--red)' : 'var(--amber)'};">${remaining}</div>
                  </div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">candidates (sorted)</div>
                  <div class="array-track" style="margin-bottom:25px; margin-top:15px;">${getCandsHTML(s.cands, s.start, s.activeIdx)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Path (sum = ${pathSum})</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:160px;">
                  <div class="panel-heading">Results (${s.results.length} combinations)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});


defineAlgoDom("09_recursion_backtracking", {
  id: "008_combination_sum_ii",
  title: "Combination Sum II",
  type: "dom",
  input: "10, 1, 2, 7, 6, 1, 5 ; 8",
  
  idea: 'Each number may only be used ONCE. We pass `i + 1` in recursion. Skip duplicate siblings to avoid duplicate results: `if (i > start and cands[i] == cands[i-1]) continue`.',
  complexity: 'Time O(2^n) · Space O(n)',
  code: [
    'def combinationSum2(candidates, target):',
    '    results, path = [], []',
    '    candidates.sort()',
    '    def backtrack(start, remaining):',
    '        if remaining == 0:',
    '            results.append(path[:])',
    '            return',
    '        for i in range(start, len(candidates)):',
    '            if i > start and candidates[i] == candidates[i-1]:',
    '                continue # Skip duplicate sibling',
    '            if candidates[i] > remaining:',
    '                break',
    '            path.append(candidates[i])',
    '            backtrack(i + 1, remaining - candidates[i])',
    '            path.pop()',
    '    backtrack(0, target)',
    '    return results'
  ],

  parse(s) {
    const parts = avParts(s);
    if (parts.length < 2) throw new Error('Provide candidates and target separated by semicolon (e.g., 10,1,2,7,6,1,5 ; 8)');
    const cands = avNums(parts[0], 20, "candidates").sort((a, b) => a - b);
    const target = avNum(parts[1], "target");
    return { cands, target };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { cands, target } = parsed;
    const n = cands.length;
    const path = [];
    const results = [];

    const snapshot = (kind, line, color, title, text, activeIdx = -1, start = -1) => {
      domPushState(seq, {
        kind, line, color,
        cands: [...cands],
        target,
        path: [...path],
        results: JSON.parse(JSON.stringify(results)),
        activeIdx,
        start,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 3, "default", "Initialization", `Sorted candidates: [${cands.join(", ")}]. Target sum: ${target}.`, -1, -1);

    function backtrack(start, remaining) {
      if (remaining === 0) {
        results.push([...path]);
        snapshot("record", 6, "emerald", "Target Reached!", `Remaining is 0. Adding [${path.join(", ")}] to results.`, -1, start);
        return;
      }

      for (let i = start; i < n; i++) {
        snapshot("loop", 8, "default", "Loop Iteration", `Checking cands[${i}] = ${cands[i]}. Remaining = ${remaining}. start is ${start}.`, i, start);

        if (i > start && cands[i] === cands[i - 1]) {
          snapshot("skip", 10, "amber", "Duplicate Sibling Pruning", `i (${i}) > start (${start}) AND cands[${i}] == cands[${i - 1}] (${cands[i]}). Skip duplicate sibling to avoid duplicate combinations.`, i, start);
          continue; 
        }

        if (cands[i] > remaining) {
          snapshot("prune", 12, "red", "Pruning (Break)", `cands[${i}] (${cands[i]}) > remaining (${remaining}). Tail is hopeless. Break.`, i, start);
          break;
        }

        path.push(cands[i]);
        snapshot("choose", 13, "blue", "Choose", `Choose ${cands[i]}. Path becomes [${path.join(", ")}]. Calling backtrack(i + 1, rem - ${cands[i]}).`, i, start);

        backtrack(i + 1, remaining - cands[i]);

        let popped = path.pop();
        snapshot("unchoose", 15, "amber", "Unchoose (Backtrack)", `Backtracking from ${popped}. Path reverts to [${path.join(", ")}].`, i, start);
      }
    }

    backtrack(0, target);
    snapshot("done", 17, "emerald", "Finished", `Found ${results.length} combination(s) that sum to ${target}.`, -1, -1);

    return seq;
  },

  renderDOM(container, s, spec) {
    if (!s) return;
    const render007 = window.ALGOS["09_recursion_backtracking"].find(a => a.id === "007_combination_sum").renderDOM;
    render007(container, s, spec);
  }
});


defineAlgoDom("09_recursion_backtracking", {
  id: "009_combination_sum_iii",
  title: "Combination Sum III",
  type: "dom",
  input: "3, 9",
  
  idea: 'Find all valid combinations of `k` numbers summing up to `n` using digits 1-9 once. Prune max and min possible sums to exit branches early.',
  complexity: 'Time O(9!/(9-k)!) · Space O(k)',
  code: [
    'def combinationSum3(k, n):',
    '    results, path = [], []',
    '    def backtrack(start, need, rem):',
    '        if need == 0:',
    '            if rem == 0:',
    '                results.append(path[:])',
    '            return',
    '        maxPossible = need * (19 - need) / 2',
    '        if rem > maxPossible: return # PRUNE: Sum Hi',
    '        endLimit = 9 - need + 1',
    '        for digit in range(start, endLimit + 1):',
    '            minPossible = need * digit + need * (need - 1) / 2',
    '            if minPossible > rem: break # PRUNE: Sum Lo',
    '            path.append(digit)',
    '            backtrack(digit + 1, need - 1, rem - digit)',
    '            path.pop()',
    '    backtrack(1, k, n)',
    '    return results'
  ],

  parse(s) {
    const parsed = avNums(s, 2, "k, n");
    if (parsed.length < 2) throw new Error('Provide k and n (e.g., 3, 9)');
    return { k: parsed[0], n: parsed[1] };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { k, n: targetN } = parsed;
    const path = [];
    const results = [];
    const cands = [1, 2, 3, 4, 5, 6, 7, 8, 9];

    const snapshot = (kind, line, color, title, text, activeIdx = -1, start = -1) => {
      domPushState(seq, {
        kind, line, color,
        cands: [...cands],
        target: targetN,
        k,
        path: [...path],
        results: JSON.parse(JSON.stringify(results)),
        activeIdx,
        start: start - 1, // 0-indexed for visualization
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 2, "default", "Initialization", `Need ${k} digits from 1..9 summing to ${targetN}.`, -1, -1);

    function backtrack(start, need, rem) {
      if (need === 0) {
        if (rem === 0) {
          results.push([...path]);
          snapshot("record", 6, "emerald", "Target Reached!", `We picked ${k} digits and sum is ${targetN}. Adding [${path.join(", ")}] to results.`, -1, start);
        } else {
          snapshot("dead", 7, "red", "Wrong Sum", `We picked ${k} digits but remaining sum is ${rem} != 0. Dead end.`, -1, start);
        }
        return;
      }

      const maxPossible = (need * (19 - need)) / 2; 
      if (rem > maxPossible) {
        snapshot("prune-hi", 9, "red", "Pruning: Sum Hi", `rem (${rem}) > maxPossible (${maxPossible}). Even if we take the largest ${need} digits (9, 8...), we can't reach the sum.`, -1, start);
        return;
      }

      const endLimit = 9 - need + 1;
      
      for (let digit = start; digit <= endLimit; digit++) {
        const idx = digit - 1; 
        snapshot("loop", 11, "default", "Loop Iteration", `Checking digit ${digit}. need=${need}, rem=${rem}.`, idx, start);

        const minPossible = (need * digit) + (need * (need - 1)) / 2;
        if (minPossible > rem) {
          snapshot("prune-lo", 13, "red", "Pruning: Sum Lo", `minPossible (${minPossible}) > rem (${rem}). Even if we take the smallest ${need} digits, we overshoot. Break loop.`, idx, start);
          break; 
        }

        path.push(digit);
        snapshot("choose", 14, "blue", "Choose", `Choose ${digit}. Path becomes [${path.join(", ")}]. Calling backtrack(digit+1, need-1, rem-digit).`, idx, start);

        backtrack(digit + 1, need - 1, rem - digit);

        let popped = path.pop();
        snapshot("unchoose", 16, "amber", "Unchoose (Backtrack)", `Backtracking from ${popped}. Path reverts to [${path.join(", ")}].`, idx, start);
      }
    }

    backtrack(1, k, targetN);
    snapshot("done", 18, "emerald", "Finished", `Found ${results.length} valid combination(s).`, -1, -1);

    return seq;
  },

  renderDOM(container, s, spec) {
    if (!s) return;
    const render007 = window.ALGOS["09_recursion_backtracking"].find(a => a.id === "007_combination_sum").renderDOM;
    render007(container, s, spec);
  }
});
