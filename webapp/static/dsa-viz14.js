/* ============================================================================
   Visualizations for 09_recursion_backtracking (Part 4 - Strings & Grids Backtracking)
   ========================================================================= */
"use strict";

const DIGIT_MAP = {
  "2": ["a","b","c"], "3": ["d","e","f"], "4": ["g","h","i"], "5": ["j","k","l"],
  "6": ["m","n","o"], "7": ["p","q","r","s"], "8": ["t","u","v"], "9": ["w","x","y","z"]
};

defineAlgoDom("09_recursion_backtracking", {
  id: "010_letter_combinations",
  title: "Letter Combinations of a Phone Number",
  type: "dom",
  input: "23",
  
  idea: 'Cartesian Product Backtracking. The pool of choices CHANGES at each recursion depth. At depth `i`, pool is `DIGIT_MAP[digits[i]]`.',
  complexity: 'Time O(4^n) · Space O(n)',
  code: [
    'def letterCombinations(digits):',
    '    if not digits: return []',
    '    res = []',
    '    digitsToChar = {',
    '        "2": "abc", "3": "def", "4": "ghi", "5": "jkl",',
    '        "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"',
    '    }',
    '    def backtrack(i, curStr):',
    '        if len(curStr) == len(digits):',
    '            res.append(curStr)',
    '            return',
    '        for c in digitsToChar[digits[i]]:',
    '            backtrack(i + 1, curStr + c)',
    '    backtrack(0, "")',
    '    return res'
  ],

  parse(s) {
    const digits = s.trim();
    if (!digits) throw new Error('Provide a string of digits 2-9 (e.g., 23)');
    if (/[^2-9]/.test(digits)) throw new Error('Only digits 2-9 are allowed');
    return { digits };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { digits } = parsed;
    const path = [];
    const results = [];

    const snapshot = (kind, line, color, title, text, activeDepth = -1, activeChar = '') => {
      domPushState(seq, {
        kind, line, color,
        digits,
        path: [...path],
        results: [...results],
        activeDepth,
        activeChar,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 2, "default", "Initialization", `Digits: "${digits}". Looking for all combinations.`, -1, '');

    function dfs(i) {
      if (i === digits.length) {
        results.push(path.join(""));
        snapshot("record", 10, "emerald", "Base Case Reached!", `We have processed all digits. Adding "${path.join("")}" to results.`, i, '');
        return;
      }

      const digit = digits[i];
      const letters = DIGIT_MAP[digit];

      for (let ch of letters) {
        snapshot("loop", 12, "default", "Loop Iteration", `At depth ${i}, digit is '${digit}'. Pool is [${letters.join(", ")}]. Next choice is '${ch}'.`, i, ch);

        path.push(ch);
        snapshot("choose", 13, "blue", "Choose", `Choose '${ch}'. Path becomes "${path.join("")}". Calling backtrack(${i + 1}).`, i, ch);

        dfs(i + 1);

        let popped = path.pop();
        snapshot("unchoose", 13, "amber", "Unchoose (Backtrack)", `Backtracking from '${popped}'. Path reverts to "${path.join("")}".`, i, ch);
      }
    }

    if (digits.length > 0) {
      dfs(0);
    }
    
    snapshot("done", 15, "emerald", "Finished", `Found ${results.length} combinations.`, -1, '');
    return seq;
  },

  renderDOM(container, s, spec) {
    const getDigitsHTML = () => {
        let els = [];
        s.digits.split("").forEach((d, idx) => {
            const isCurrentDepth = idx === s.activeDepth;
            const chosenChar = s.path[idx] || '';
            
            let poolHtml = '';
            DIGIT_MAP[d].forEach(ch => {
                const isChosen = chosenChar === ch;
                const isChecking = isCurrentDepth && s.activeChar === ch;
                let cCls = isChosen ? 'bg-emerald border-emerald' : 
                           isChecking ? 'bg-amber border-amber' : 'bg-surface border-border';
                           
                poolHtml += `<div class="array-node" style="width:20px; height:20px; font-size:12px; min-width:20px; padding:0; ${
                    isChosen ? 'background:var(--emerald); color:white; border-color:var(--emerald);' : 
                    isChecking ? 'background:var(--amber); color:white; border-color:var(--amber);' : 
                    'opacity:0.6;'
                }">${ch}</div>`;
            });

            els.push(`
            <div style="display:flex; flex-direction:column; align-items:center; margin-right:15px;">
                <div class="array-node ${isCurrentDepth ? 'active-1' : 'merged'}" style="margin-bottom:10px; width:40px; height:40px;">
                    ${isCurrentDepth ? `<div class="pointer" style="color:var(--blue); top:-25px;">↓ i=${idx}</div>` : ''}
                    ${d}
                </div>
                <div style="display:flex; gap:4px;">
                    ${poolHtml}
                </div>
            </div>`);
        });
        return els.join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                "${p}"
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Digits & Character Pools</div>
                  <div class="array-track" style="margin-bottom:15px; margin-top:25px; align-items:flex-start;">${getDigitsHTML()}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current String (curStr)</div>
                  <div class="array-track" style="justify-content:flex-start; font-family:monospace; font-size:18px; color:var(--text-bright); padding:10px;">
                      "${s.path.join('')}"
                  </div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:160px;">
                  <div class="panel-heading">Results (${s.results.length} combinations)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});


defineAlgoDom("09_recursion_backtracking", {
  id: "011_palindrome_partitioning",
  title: "Palindrome Partitioning",
  type: "dom",
  input: "aab",
  
  idea: 'Combinations shape, but iterating over substrings. Iterate `end` to form a prefix `s[start:end]`. If it is a palindrome, recurse on the rest.',
  complexity: 'Time O(n * 2^n) · Space O(n)',
  code: [
    'def partition(s):',
    '    res = []',
    '    part = []',
    '    def isPali(l, r):',
    '        while l < r:',
    '            if s[l] != s[r]: return False',
    '            l, r = l + 1, r - 1',
    '        return True',
    '    def dfs(i):',
    '        if i >= len(s):',
    '            res.append(part[:])',
    '            return',
    '        for j in range(i, len(s)):',
    '            if isPali(i, j):',
    '                part.append(s[i:j+1])',
    '                dfs(j + 1)',
    '                part.pop()',
    '    dfs(0)',
    '    return res'
  ],

  parse(s) {
    const str = s.trim();
    if (!str) throw new Error('Provide a string (e.g., aab)');
    return { str };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { str } = parsed;
    const n = str.length;
    const path = [];
    const results = [];
    
    function isPalindrome(sub) {
      let l = 0, r = sub.length - 1;
      while (l < r) {
        if (sub[l] !== sub[r]) return false;
        l++; r--;
      }
      return true;
    }

    const snapshot = (kind, line, color, title, text, i = -1, j = -1) => {
      domPushState(seq, {
        kind, line, color,
        str,
        path: [...path],
        results: JSON.parse(JSON.stringify(results)),
        i, j,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 2, "default", "Initialization", `String: "${str}". Length: ${n}.`, -1, -1);

    function dfs(i) {
      if (i >= n) {
        results.push([...path]);
        snapshot("record", 11, "emerald", "Base Case Reached!", `We have partitioned the whole string. Adding to results.`, i, -1);
        return;
      }

      for (let j = i; j < n; j++) {
        const sub = str.slice(i, j + 1);
        const isPal = isPalindrome(sub);
        
        snapshot("loop", 14, "default", "Loop Iteration (Check Prefix)", `Checking substring from index ${i} to ${j}: "${sub}". Is it a palindrome? ${isPal ? 'YES' : 'NO'}.`, i, j);

        if (isPal) {
          path.push(sub);
          snapshot("choose", 15, "blue", "Choose", `"${sub}" is a palindrome. Pick it! Path becomes [${path.map(s => `"${s}"`).join(", ")}].`, i, j);

          dfs(j + 1);

          let popped = path.pop();
          snapshot("unchoose", 17, "amber", "Unchoose (Backtrack)", `Backtracking from "${popped}". Path reverts to [${path.map(s => `"${s}"`).join(", ")}].`, i, j);
        } else {
          snapshot("prune", 14, "red", "Pruning", `"${sub}" is NOT a palindrome. Prune this branch.`, i, j);
        }
      }
    }

    dfs(0);
    snapshot("done", 19, "emerald", "Finished", `Found ${results.length} valid partitions.`, -1, -1);
    
    return seq;
  },

  renderDOM(container, s, spec) {
    const getStrHTML = (str, currI, currJ) => {
        let els = [];
        for (let idx = 0; idx < str.length; idx++) {
            const ch = str[idx];
            let cls = '';
            let ptrs = [];
            
            if (idx === currI) {
                cls = 'active-1';
                ptrs.push(`<div class="pointer" style="color:var(--blue); top:-25px;">↓ i</div>`);
            }
            if (idx === currJ) {
                cls = s.kind === 'prune' ? 'active-red' : 'active-k';
                ptrs.push(`<div class="pointer" style="color:var(--amber); bottom:-25px;">↑ j</div>`);
            }
            
            if (idx > currI && idx < currJ) {
                cls = s.kind === 'prune' ? 'active-red' : 'active-k';
            }
            
            if (idx < currI) {
                cls = 'merged';
            }
            
            els.push(`
            <div class="array-node ${cls}" style="position:relative; margin-bottom: 20px;">
                ${ptrs.join('')}
                ${ch}
                <div class="node-index">${idx}</div>
            </div>`);
        }
        return els.join('');
    };

    const getPathHTML = (path) => {
        if (path.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return path.map(val => `
            <div class="array-node active-1" style="background:var(--blue); color:white; border-color:white;">
                "${val}"
            </div>
        `).join('');
    };

    const getResultsHTML = (results) => {
        if (results.length === 0) return `<div style="color:var(--text-dim); padding:10px; font-style:italic;">[ ]</div>`;
        return `<div style="display:flex; flex-wrap:wrap; gap:8px;">` + results.map(p => `
            <div class="array-node merged" style="border-radius:4px; padding:4px 8px; border-color:var(--emerald); background:var(--bg-card); min-width:30px;">
                [${p.map(x => `"${x}"`).join(', ')}]
            </div>
        `).join('') + `</div>`;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">String</div>
                  <div class="array-track" style="margin-bottom:25px; margin-top:15px;">${getStrHTML(s.str, s.i, s.j)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--blue);">
                  <div class="panel-heading">Current Partition (part)</div>
                  <div class="array-track" style="justify-content:flex-start;">${getPathHTML(s.path)}</div>
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); flex:1; overflow-y:auto; max-height:160px;">
                  <div class="panel-heading">Results (${s.results.length} partitions)</div>
                  <div class="array-track" style="justify-content:flex-start; align-items:flex-start;">${getResultsHTML(s.results)}</div>
              </div>
    </div>`;
  }
});


defineAlgoDom("09_recursion_backtracking", {
  id: "012_word_search",
  title: "Word Search",
  type: "dom",
  input: "A,B,C,E ; S,F,C,S ; A,D,E,E | ABCCED",
  
  idea: 'Classic Grid Backtracking. At each step, branch up to 4 ways. We mutate board to mark a cell as visited (e.g. to `#`) and MUST unmark before returning.',
  complexity: 'Time O(N*M * 4^L) · Space O(L)',
  code: [
    'def exist(board, word):',
    '    ROWS, COLS = len(board), len(board[0])',
    '    def dfs(r, c, i):',
    '        if i == len(word): return True',
    '        if (r < 0 or c < 0 or r >= ROWS or c >= COLS or',
    '            board[r][c] != word[i]):',
    '            return False',
    '        tmp = board[r][c]',
    '        board[r][c] = "#" # Mark visited',
    '        res = (dfs(r + 1, c, i + 1) or',
    '               dfs(r - 1, c, i + 1) or',
    '               dfs(r, c + 1, i + 1) or',
    '               dfs(r, c - 1, i + 1))',
    '        board[r][c] = tmp # Unmark',
    '        return res',
    '    for r in range(ROWS):',
    '        for c in range(COLS):',
    '            if dfs(r, c, 0): return True',
    '    return False'
  ],

  parse(s) {
    const parts = s.split("|");
    if (parts.length !== 2) throw new Error('Format: row1;row2;row3 | word');
    const boardRows = parts[0].split(";").map(r => r.trim()).filter(Boolean);
    const board = boardRows.map(r => r.split(",").map(c => c.trim()));
    const word = parts[1].trim();
    if (board.length === 0 || word.length === 0) throw new Error('Invalid input');
    return { board, word };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { board, word } = parsed;
    const ROWS = board.length;
    const COLS = board[0].length;
    const WORD_LEN = word.length;
    let foundResult = false;
    
    const copyBoard = (b) => b.map(r => [...r]);

    const snapshot = (kind, line, color, title, text, r = -1, c = -1, i = -1) => {
      domPushState(seq, {
        kind, line, color,
        board: copyBoard(board),
        word,
        r, c, i,
        foundResult,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 2, "default", "Initialization", `Searching for word "${word}" in ${ROWS}x${COLS} grid.`, -1, -1, -1);

    function dfs(r, c, i) {
      if (foundResult) return false;
      
      snapshot("call", 3, "default", "Recursion Call", `dfs(r=${r}, c=${c}, i=${i}). Need to match word[${i}] = '${word[i] || ""}'.`, r, c, i);

      if (i === WORD_LEN) {
        foundResult = true;
        snapshot("found", 4, "emerald", "Word Found!", `Matched all characters of "${word}". Returning true!`, r, c, i);
        return true;
      }

      if (r < 0 || c < 0 || r >= ROWS || c >= COLS) {
        snapshot("oob", 5, "red", "Pruning (Out of Bounds)", `Cell (${r}, ${c}) is out of bounds.`, r, c, i);
        return false;
      }
      
      if (board[r][c] !== word[i]) {
        snapshot("mismatch", 6, "red", "Pruning (Mismatch or Visited)", `board[${r}][${c}] is '${board[r][c]}', but we need '${word[i]}'. Fail.`, r, c, i);
        return false;
      }

      const tmp = board[r][c];
      board[r][c] = '#';
      snapshot("choose", 9, "blue", "Choose (Mark Visited)", `Matched '${tmp}'. Mark board[${r}][${c}] as '#' to prevent reuse. Recurse neighbors.`, r, c, i);

      const found = (
        dfs(r + 1, c, i + 1) ||
        dfs(r - 1, c, i + 1) ||
        dfs(r, c + 1, i + 1) ||
        dfs(r, c - 1, i + 1)
      );

      if (found) return true;

      board[r][c] = tmp;
      snapshot("unchoose", 14, "amber", "Unchoose (Backtrack)", `All paths from (${r}, ${c}) failed. Restore board[${r}][${c}] back to '${tmp}'.`, r, c, i);
      
      return false;
    }

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        if (foundResult) break;
        snapshot("start", 18, "default", "New Start Point", `Initiate search from cell (${r}, ${c}).`, r, c, 0);
        if (dfs(r, c, 0)) {
          break;
        }
      }
    }
    
    if (!foundResult) {
       snapshot("done", 19, "red", "Finished", `Word "${word}" was NOT found in the grid.`, -1, -1, -1);
    }
    return seq;
  },

  renderDOM(container, s, spec) {
    const ROWS = s.board.length;
    const COLS = s.board[0].length;
    
    const getGridHTML = () => {
        let html = '<div style="display:flex; flex-direction:column; gap:5px;">';
        for (let r = 0; r < ROWS; r++) {
            html += '<div style="display:flex; gap:5px;">';
            for (let c = 0; c < COLS; c++) {
                const ch = s.board[r][c];
                const isActive = r === s.r && c === s.c;
                const isVisited = ch === '#';
                
                let cls = '';
                if (isActive && isVisited) cls = 'active-k border-amber';
                else if (isActive) cls = s.kind === 'oob' || s.kind === 'mismatch' ? 'active-red' : 'active-1';
                else if (isVisited) cls = 'active-k'; // dark gray or marked
                
                html += `
                <div class="array-node ${cls}" style="width:50px; height:50px; border-radius:8px; font-weight:bold; font-size:24px; position:relative; ${isVisited && !isActive ? 'background:var(--bg-surface); color:var(--text-dim);' : ''}">
                    ${ch}
                    ${isActive ? `<div class="pointer" style="top:-20px; font-size:10px;">(${r},${c})</div>` : ''}
                </div>`;
            }
            html += '</div>';
        }
        html += '</div>';
        return html;
    };
    
    const getWordHTML = () => {
        let html = '<div style="display:flex; gap:5px; margin-top:10px; font-family:monospace; font-size:24px;">';
        for (let i = 0; i < s.word.length; i++) {
            const ch = s.word[i];
            const isActive = i === s.i;
            const isMatched = i < s.i;
            html += `<span style="padding:5px 10px; border-radius:4px; ${isActive ? 'background:var(--blue); color:white;' : isMatched ? 'background:var(--emerald); color:white;' : 'background:var(--bg-surface); color:var(--text-dim);'}">${ch}</span>`;
        }
        html += '</div>';
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Target Word</div>
                  <div class="array-track" style="justify-content:flex-start;">${getWordHTML()}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Board</div>
                  <div class="array-track">${getGridHTML()}</div>
                  ${s.foundResult ? `<div style="margin-top:15px; text-align:center; padding:10px; background:var(--emerald); color:white; border-radius:8px; font-weight:bold;">WORD FOUND!</div>` : ''}
              </div>
    </div>`;
  }
});
