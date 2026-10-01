/* ============================================================================
   Visualizations for 09_recursion_backtracking (Part 5 - Advanced Board Backtracking)
   ========================================================================= */
"use strict";

defineAlgoDom("09_recursion_backtracking", {
  id: "013_n_queens",
  title: "N-Queens",
  type: "dom",
  input: "4",
  
  idea: 'Place queens row by row. Use three sets to track attacked columns and diagonals (positive diag: r+c, negative diag: r-c).',
  complexity: 'Time O(N!) · Space O(N)',
  code: [
    'def solveNQueens(n):',
    '    col, posDiag, negDiag = set(), set(), set()',
    '    res = []',
    '    board = [["."] * n for _ in range(n)]',
    '    ',
    '    def backtrack(r):',
    '        if r == n:',
    '            res.append(["".join(row) for row in board])',
    '            return',
    '        for c in range(n):',
    '            if c in col or (r+c) in posDiag or (r-c) in negDiag:',
    '                continue',
    '            ',
    '            col.add(c); posDiag.add(r+c); negDiag.add(r-c)',
    '            board[r][c] = "Q"',
    '            backtrack(r + 1)',
    '            col.remove(c); posDiag.remove(r+c); negDiag.remove(r-c)',
    '            board[r][c] = "."',
    '    backtrack(0)',
    '    return res'
  ],

  parse(s) {
    const n = parseInt(s.trim(), 10);
    if (isNaN(n) || n < 1 || n > 8) throw new Error("Enter N between 1 and 8");
    return { n };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const { n } = parsed;
    const board = Array(n).fill().map(() => Array(n).fill("."));
    const results = [];
    
    const col = new Set();
    const posDiag = new Set();
    const negDiag = new Set();

    const snapshot = (kind, line, color, title, text, r = -1, c = -1) => {
      domPushState(seq, {
        kind, line, color,
        board: board.map(row => [...row]),
        r, c,
        results: [...results],
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 4, "default", "Initialization", `${n}x${n} board created. Sets initialized.`, -1, -1);

    function backtrack(r) {
      snapshot("call", 6, "default", "Recursion Call", `backtrack(r=${r}).`, r, -1);

      if (r === n) {
        results.push(board.map(row => row.join("")));
        snapshot("record", 8, "emerald", "Base Case Reached!", `All ${n} queens placed! Adding board to results.`, r, -1);
        return;
      }

      for (let c = 0; c < n; c++) {
        snapshot("loop", 10, "default", "Loop Iteration", `Checking cell (${r}, ${c}).`, r, c);

        if (col.has(c) || posDiag.has(r + c) || negDiag.has(r - c)) {
          snapshot("prune", 12, "red", "Pruning (Attacked)", `Cell (${r}, ${c}) is under attack! (c in col: ${col.has(c)}, r+c in pos: ${posDiag.has(r+c)}, r-c in neg: ${negDiag.has(r-c)}). Skip.`, r, c);
          continue;
        }

        col.add(c); posDiag.add(r + c); negDiag.add(r - c);
        board[r][c] = "Q";
        snapshot("choose", 15, "blue", "Choose (Place Queen)", `Cell (${r}, ${c}) is safe. Placed Queen.`, r, c);

        backtrack(r + 1);

        col.delete(c); posDiag.delete(r + c); negDiag.delete(r - c);
        board[r][c] = ".";
        snapshot("unchoose", 18, "amber", "Unchoose (Backtrack)", `Backtracking from (${r}, ${c}). Removed Queen.`, r, c);
      }
    }

    backtrack(0);
    snapshot("done", 20, "emerald", "Finished", `Found ${results.length} distinct solutions for ${n}-Queens.`, -1, -1);
    
    return seq;
  },

  renderDOM(container, s, spec) {
    const N = s.board.length;
    const getGridHTML = () => {
        let html = '<div style="display:flex; flex-direction:column; gap:2px; padding:10px; background:var(--bg-surface); border-radius:8px;">';
        for (let r = 0; r < N; r++) {
            html += '<div style="display:flex; gap:2px;">';
            for (let c = 0; c < N; c++) {
                const ch = s.board[r][c];
                const isBlack = (r + c) % 2 === 1;
                const isActive = r === s.r && c === s.c;
                const isTargetRow = r === s.r && c !== s.c;
                
                let bgCls = isBlack ? 'background:#334155;' : 'background:#e2e8f0; color:#0f172a;';
                if (isActive) {
                    bgCls = s.kind === 'prune' ? 'background:var(--red); color:white;' : 
                            s.kind === 'choose' ? 'background:var(--blue); color:white;' : 
                            'background:var(--amber); color:black;';
                } else if (isTargetRow && s.c === -1) {
                    bgCls += ' box-shadow: inset 0 0 0 2px var(--blue);';
                }
                
                html += `
                <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:bold; ${bgCls}">
                    ${ch === 'Q' ? '♛' : ''}
                </div>`;
            }
            html += '</div>';
        }
        html += '</div>';
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container" style="align-items:center;">
                  <div class="panel-heading">Chessboard (${N}x${N})</div>
                  ${getGridHTML()}
              </div>
              <div class="glass-panel arrays-container" style="border-left:4px solid var(--emerald); width:100%;">
                  <div class="panel-heading">Solutions Found: ${s.results.length}</div>
              </div>
    </div>`;
  }
});


defineAlgoDom("09_recursion_backtracking", {
  id: "014_sudoku_solver",
  title: "Sudoku Solver",
  type: "dom",
  input: `5,3,.,.,7,.,.,.,.
6,.,.,1,9,5,.,.,.
.,9,8,.,.,.,.,6,.
8,.,.,.,6,.,.,.,3
4,.,.,8,.,3,.,.,1
7,.,.,.,2,.,.,.,6
.,6,.,.,.,.,2,8,.
.,.,.,4,1,9,.,.,5
.,.,.,.,8,.,.,7,9`,
  
  idea: 'Try filling empty cells `.`. Validate numbers 1-9 against row, column, and 3x3 block. If valid, recurse. Backtrack on failure.',
  complexity: 'Time O(9^(Empty cells)) · Space O(1)',
  code: [
    'def solveSudoku(board):',
    '    def isValid(r, c, val):',
    '        for i in range(9):',
    '            if board[i][c] == val: return False',
    '            if board[r][i] == val: return False',
    '            if board[3*(r//3) + i//3][3*(c//3) + i%3] == val:',
    '                return False',
    '        return True',
    '        ',
    '    def solve():',
    '        for i in range(9):',
    '            for j in range(9):',
    '                if board[i][j] == ".":',
    '                    for val in "123456789":',
    '                        if isValid(i, j, val):',
    '                            board[i][j] = val',
    '                            if solve(): return True',
    '                            board[i][j] = "."',
    '                    return False',
    '        return True',
    '    solve()',
    '    return board'
  ],

  parse(s) {
    const rows = s.trim().split(/\n|;/).map(r => r.trim()).filter(Boolean);
    if (rows.length !== 9) throw new Error("Need exactly 9 rows.");
    const board = rows.map(r => {
      const cells = r.split(",").map(c => c.trim());
      if (cells.length !== 9) throw new Error("Each row needs exactly 9 cells.");
      return cells;
    });
    return { board };
  },

  buildStates(parsed) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const board = parsed.board.map(r => [...r]);
    // Pre-calculate fixed cells
    const fixed = Array(9).fill().map(() => Array(9).fill(false));
    for(let r=0; r<9; r++) {
        for(let c=0; c<9; c++) {
            if (board[r][c] !== '.') fixed[r][c] = true;
        }
    }

    let isSolved = false;

    const snapshot = (kind, line, color, title, text, r = -1, c = -1, v = '') => {
      domPushState(seq, {
        kind, line, color,
        board: board.map(row => [...row]),
        fixed,
        r, c, v,
        isSolved,
        explTitle: title,
        explText: text
      }, ctx);
    };

    snapshot("init", 10, "default", "Initialization", `9x9 board created. Searching for empty cells.`, -1, -1, '');

    function isValid(r, c, val) {
      for (let i = 0; i < 9; i++) {
        if (board[i][c] === val) return false;
        if (board[r][i] === val) return false;
        if (board[3 * Math.floor(r / 3) + Math.floor(i / 3)][3 * Math.floor(c / 3) + (i % 3)] === val) {
          return false;
        }
      }
      return true;
    }

    // to avoid excessive states, we might only record specific events.
    let stepCount = 0;
    const MAX_STEPS = 500; // prevent huge rendering

    function solve() {
      if (isSolved || stepCount > MAX_STEPS) return true;

      for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
          if (board[i][j] === '.') {
            
            for (let v = 1; v <= 9; v++) {
              const val = String(v);
              
              if (stepCount <= MAX_STEPS) {
                 // snapshot("loop", 15, "default", "Try Value", `Trying ${val} at (${i}, ${j}).`, i, j, val);
              }

              if (isValid(i, j, val)) {
                board[i][j] = val;
                stepCount++;
                if (stepCount % 5 === 0 && stepCount <= MAX_STEPS) {
                    snapshot("choose", 16, "blue", "Choose", `Placed ${val} at (${i}, ${j}). Recursing.`, i, j, val);
                }

                if (solve()) return true;

                board[i][j] = '.';
                stepCount++;
                if (stepCount % 5 === 0 && stepCount <= MAX_STEPS) {
                    snapshot("unchoose", 18, "amber", "Unchoose (Backtrack)", `Backtracking at (${i}, ${j}). Cleared.`, i, j, '');
                }
              }
            }
            if (stepCount <= MAX_STEPS) {
                // snapshot("dead", 19, "red", "Dead End", `No valid number 1-9 for (${i}, ${j}). Returning False to backtrack!`, i, j, '');
            }
            return false; // Crucial: if no digit 1-9 works, this path is dead
          }
        }
      }
      isSolved = true;
      return true;
    }

    solve();
    snapshot("done", 20, "emerald", "Finished", isSolved ? "Sudoku solved successfully!" : "No solution exists.", -1, -1, '');
    
    return seq;
  },

  renderDOM(container, s, spec) {
    const getGridHTML = () => {
        let html = '<div style="display:flex; flex-direction:column; background:white; border:2px solid black; width:fit-content; border-radius:4px; overflow:hidden;">';
        for (let r = 0; r < 9; r++) {
            html += '<div style="display:flex;">';
            for (let c = 0; c < 9; c++) {
                const ch = s.board[r][c];
                const isFixed = s.fixed[r][c];
                const isActive = r === s.r && c === s.c;
                
                let bBottom = r % 3 === 2 && r !== 8 ? 'border-bottom: 2px solid black;' : 'border-bottom: 1px solid #ccc;';
                let bRight = c % 3 === 2 && c !== 8 ? 'border-right: 2px solid black;' : 'border-right: 1px solid #ccc;';
                
                let bgCls = isFixed ? 'background:#f1f5f9; color:#0f172a;' : 'background:white; color:#3b82f6;';
                if (isActive) {
                    bgCls = s.kind === 'choose' ? 'background:var(--blue); color:white;' : 
                            s.kind === 'unchoose' ? 'background:var(--amber); color:white;' : 
                            'background:#bfdbfe; color:black;';
                }
                
                html += `
                <div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:bold; ${bBottom} ${bRight} ${bgCls}">
                    ${ch === '.' ? '' : ch}
                </div>`;
            }
            html += '</div>';
        }
        html += '</div>';
        return html;
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container" style="align-items:center;">
                  <div class="panel-heading">Sudoku Board</div>
                  ${getGridHTML()}
              </div>
    </div>`;
  }
});
