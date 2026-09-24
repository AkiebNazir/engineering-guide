/* ============================================================================
   Visualizations for 06_stack
   ========================================================================= */
'use strict';

/* ================================ 06 · Valid Parentheses (DOM) ========== */
defineAlgoDom('06_stack', {
  type: 'dom',
  title: 'Valid Parentheses', short: 'Valid Parentheses',
  idea: 'Use a stack to keep track of open brackets. When closing a bracket, check if it matches the top of the stack.',
  complexity: 'Time O(n) · Space O(n)',
  input: '()[]{}', hint: 'string of brackets ()[]{}',
  code: [
    'def isValid(s):',
    '    pairs = {")": "(", "]": "[", "}": "{"}',
    '    stack = []',
    '    for c in s:',
    '        if c in pairs:',
    '            if not stack or stack[-1] != pairs[c]:',
    '                return False',
    '            stack.pop()',
    '        else:',
    '            stack.append(c)',
    '    return not stack'
  ],
  parse(s) {
    if (!s || s.length === 0) throw new Error('Enter a string of brackets');
    if (s.length > 20) throw new Error('Keep string length <= 20 for visualization');
    return { str: s };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const stack = [];
    const pairs = { ')': '(', ']': '[', '}': '{' };
    
    domPushState(seq, {
      kind: 'init', line: 3, color: 'default',
      str, stack: [...stack], i: -1, valid: null,
      explTitle: 'Initialization',
      explText: `We start with an empty stack. We will iterate through each character of the string.`,
      pause: true
    }, ctx);

    for (let i = 0; i < str.length; i++) {
      let c = str[i];
      domPushState(seq, {
        kind: 'loop', line: 4, color: 'blue',
        str, stack: [...stack], i, valid: null,
        explTitle: `Process '${c}'`,
        explText: `Examining character '${c}' at index ${i}.`
      }, ctx);

      if (pairs[c]) {
        domPushState(seq, {
          kind: 'is-closer', line: 5, color: 'default',
          str, stack: [...stack], i, valid: null,
          explTitle: `Closer Bracket`,
          explText: `'${c}' is a closing bracket. We check if the stack is empty or if the top of the stack matches its corresponding opening bracket '${pairs[c]}'.`
        }, ctx);

        if (stack.length === 0 || stack[stack.length - 1] !== pairs[c]) {
          domPushState(seq, {
            kind: 'invalid', line: 7, color: 'rose',
            str, stack: [...stack], i, valid: false,
            explTitle: `Mismatch or Empty Stack`,
            explText: stack.length === 0 ? `The stack is empty, meaning there is no corresponding opening bracket.` : `The top of the stack is '${stack[stack.length - 1]}', which does not match '${pairs[c]}'. Return False.`,
            pause: true
          }, ctx);
          return seq;
        }

        stack.pop();
        domPushState(seq, {
          kind: 'match', line: 8, color: 'emerald',
          str, stack: [...stack], i, valid: null,
          explTitle: `Match Found`,
          explText: `The top of the stack matches. We pop it from the stack.`
        }, ctx);
      } else {
        stack.push(c);
        domPushState(seq, {
          kind: 'is-opener', line: 10, color: 'amber',
          str, stack: [...stack], i, valid: null,
          explTitle: `Opener Bracket`,
          explText: `'${c}' is an opening bracket. We push it onto the stack.`
        }, ctx);
      }
    }

    const isValid = stack.length === 0;
    domPushState(seq, {
      kind: 'done', line: 11, color: isValid ? 'emerald' : 'rose',
      str, stack: [...stack], i: str.length, valid: isValid,
      explTitle: 'Complete',
      explText: isValid ? `The string is fully processed and the stack is empty. Return True.` : `The string is fully processed but the stack still has elements. Return False.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getCharsHTML = (str, activeI) => {
        return str.split('').map((c, idx) => {
            let cls = '';
            if (idx === activeI) cls = 'active-k'; // Highlight current character
            else if (idx < activeI) cls = 'merged'; // Dimmed past characters
            
            return `
            <div class="array-node ${cls}">
                ${idx === activeI ? '<div class="pointer" style="color:#34d399">↓ i</div>' : ''}
                ${c}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getStackHTML = (stack) => {
        if (stack.length === 0) {
            return `<div style="text-align:center; padding:20px; color:var(--text-dim);">Empty Stack</div>`;
        }
        return stack.map((item, idx) => {
            let isTop = idx === stack.length - 1;
            return `
            <div class="array-node ${isTop ? 'active-1' : ''}" style="margin-bottom:5px; min-width:60px;">
                ${item}
                ${isTop ? '<div class="pointer" style="position:absolute; right:-35px; top:15px; color:#3b82f6;">← top</div>' : ''}
            </div>`;
        }).reverse().join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>s (String)</span>
                      <span style="color:${s.valid === true ? '#10b981' : (s.valid === false ? '#ef4444' : 'var(--text-bright)')};">Result: ${s.valid !== null ? s.valid : '?'}</span>
                  </div>
                  <div class="array-track">${getCharsHTML(s.str, s.i)}</div>
              </div>
              <div class="glass-panel stack-container" style="display:flex; flex-direction:column; align-items:center;">
                  <div class="panel-heading" style="align-self:flex-start;">Stack</div>
                  <div style="display:flex; flex-direction:column; justify-content:flex-end; min-height:150px; padding:10px;">
                      ${getStackHTML(s.stack)}
                  </div>
              </div>
    </div>`;
  }
});

/* ================================ 06 · Evaluate Reverse Polish Notation (DOM) ========== */
defineAlgoDom('06_stack', {
  type: 'dom',
  title: 'Evaluate Reverse Polish Notation', short: 'Evaluate RPN',
  idea: 'Push numbers onto a stack. When an operator is encountered, pop the last two numbers, apply the operator, and push the result back onto the stack.',
  complexity: 'Time O(n) · Space O(n)',
  input: '2, 1, +, 3, *', hint: 'comma-separated tokens',
  code: [
    'def evalRPN(tokens):',
    '    stack = []',
    '    ops = {"+", "-", "*", "/"}',
    '    for tok in tokens:',
    '        if tok in ops:',
    '            b = stack.pop()',
    '            a = stack.pop()',
    '            if tok == "+": stack.append(a + b)',
    '            elif tok == "-": stack.append(a - b)',
    '            elif tok == "*": stack.append(a * b)',
    '            else: stack.append(int(a / b))',
    '        else:',
    '            stack.append(int(tok))',
    '    return stack[0]'
  ],
  parse(s) {
    if (!s || s.trim().length === 0) throw new Error('Enter comma-separated tokens');
    const tokens = s.split(',').map(x => x.trim()).filter(Boolean);
    if (tokens.length > 20) throw new Error('Keep token count <= 20 for visualization');
    return { tokens };
  },
  buildStates({ tokens }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const stack = [];
    const ops = new Set(['+', '-', '*', '/']);
    
    domPushState(seq, {
      kind: 'init', line: 2, color: 'default',
      tokens, stack: [...stack], i: -1, a: null, b: null,
      explTitle: 'Initialization',
      explText: `We start with an empty stack. We will process each token one by one.`,
      pause: true
    }, ctx);

    for (let i = 0; i < tokens.length; i++) {
      let tok = tokens[i];
      domPushState(seq, {
        kind: 'loop', line: 4, color: 'blue',
        tokens, stack: [...stack], i, a: null, b: null,
        explTitle: `Process Token '${tok}'`,
        explText: `Examining token '${tok}' at index ${i}.`
      }, ctx);

      if (ops.has(tok)) {
        domPushState(seq, {
          kind: 'is-op', line: 5, color: 'default',
          tokens, stack: [...stack], i, a: null, b: null,
          explTitle: `Operator Detected`,
          explText: `'${tok}' is an operator. We will pop the top two numbers from the stack.`
        }, ctx);

        let b = stack.pop();
        let a = stack.pop();
        
        domPushState(seq, {
          kind: 'pop', line: 7, color: 'amber',
          tokens, stack: [...stack], i, a, b,
          explTitle: `Pop Operands`,
          explText: `Popped b = ${b} and a = ${a}. Now we evaluate ${a} ${tok} ${b}.`
        }, ctx);

        let res = 0;
        let line = 0;
        if (tok === '+') { res = a + b; line = 8; }
        else if (tok === '-') { res = a - b; line = 9; }
        else if (tok === '*') { res = a * b; line = 10; }
        else { res = Math.trunc(a / b); line = 11; }

        stack.push(res);
        domPushState(seq, {
          kind: 'push-res', line, color: 'emerald',
          tokens, stack: [...stack], i, a, b,
          explTitle: `Push Result`,
          explText: `${a} ${tok} ${b} = ${res}. Pushed ${res} onto the stack.`
        }, ctx);
      } else {
        stack.push(parseInt(tok, 10));
        domPushState(seq, {
          kind: 'push-num', line: 13, color: 'emerald',
          tokens, stack: [...stack], i, a: null, b: null,
          explTitle: `Operand Detected`,
          explText: `'${tok}' is a number. We push it onto the stack.`
        }, ctx);
      }
    }

    domPushState(seq, {
      kind: 'done', line: 14, color: 'emerald',
      tokens, stack: [...stack], i: tokens.length, a: null, b: null,
      explTitle: 'Complete',
      explText: `All tokens processed. The final answer is ${stack[0]} at the top of the stack.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getTokensHTML = (tokens, activeI) => {
        return tokens.map((tok, idx) => {
            let cls = '';
            if (idx === activeI) cls = 'active-k'; 
            else if (idx < activeI) cls = 'merged'; 
            
            return `
            <div class="array-node ${cls}" style="min-width:30px;">
                ${idx === activeI ? '<div class="pointer" style="color:#34d399">↓ i</div>' : ''}
                ${tok}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getStackHTML = (stack) => {
        if (stack.length === 0) {
            return `<div style="text-align:center; padding:20px; color:var(--text-dim);">Empty Stack</div>`;
        }
        return stack.map((item, idx) => {
            let isTop = idx === stack.length - 1;
            return `
            <div class="array-node ${isTop ? 'active-1' : ''}" style="margin-bottom:5px; min-width:60px;">
                ${item}
                ${isTop ? '<div class="pointer" style="position:absolute; right:-35px; top:15px; color:#3b82f6;">← top</div>' : ''}
            </div>`;
        }).reverse().join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading" style="display:flex; justify-content:space-between;">
                      <span>Tokens</span>
                  </div>
                  <div class="array-track">${getTokensHTML(s.tokens, s.i)}</div>
              </div>
              <div style="display:flex; gap:15px;">
                  <div class="glass-panel stack-container" style="flex:1; display:flex; flex-direction:column; align-items:center;">
                      <div class="panel-heading" style="align-self:flex-start;">Stack</div>
                      <div style="display:flex; flex-direction:column; justify-content:flex-end; min-height:150px; padding:10px;">
                          ${getStackHTML(s.stack)}
                      </div>
                  </div>
                  <div class="glass-panel" style="flex:1;">
                      <div class="panel-heading">Variables</div>
                      <div style="display:flex; flex-direction:column; gap:10px; padding:10px;">
                          <div>a: <b style="color:var(--accent)">${s.a !== null ? s.a : '-'}</b></div>
                          <div>b: <b style="color:#f59e0b">${s.b !== null ? s.b : '-'}</b></div>
                      </div>
                  </div>
              </div>
    </div>`;
  }
});

/* ================================ 06 · Daily Temperatures (DOM) ========== */
defineAlgoDom('06_stack', {
  type: 'dom',
  title: 'Daily Temperatures', short: 'Daily Temperatures',
  idea: 'Use a decreasing monotonic stack to store indices. If the current temperature is higher than the one at the top of the stack, we found a warmer day!',
  complexity: 'Time O(n) · Space O(n)',
  input: '73, 74, 75, 71, 69, 72, 76, 73', hint: 'comma-separated temperatures',
  code: [
    'def dailyTemperatures(temperatures):',
    '    n = len(temperatures)',
    '    ans = [0] * n',
    '    stack = []',
    '    for i, t in enumerate(temperatures):',
    '        while stack and temperatures[stack[-1]] < t:',
    '            j = stack.pop()',
    '            ans[j] = i - j',
    '        stack.append(i)',
    '    return ans'
  ],
  parse(s) { return { temps: avNums(s, 14, 'temperatures') }; },
  buildStates({ temps }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = temps.length;
    const ans = Array(n).fill(0);
    const stack = [];
    
    domPushState(seq, {
      kind: 'init', line: 4, color: 'default',
      temps, ans: [...ans], stack: [...stack], i: -1, j: -1, t: null,
      explTitle: 'Initialization',
      explText: `We initialize ans array with 0s and an empty stack to keep track of indices of cooler days.`,
      pause: true
    }, ctx);

    for (let i = 0; i < n; i++) {
      let t = temps[i];
      domPushState(seq, {
        kind: 'loop', line: 5, color: 'blue',
        temps, ans: [...ans], stack: [...stack], i, j: -1, t,
        explTitle: `Day ${i} (${t}°)`,
        explText: `Examining day ${i} with temperature ${t}°.`
      }, ctx);

      while (stack.length > 0 && temps[stack[stack.length - 1]] < t) {
        domPushState(seq, {
          kind: 'while-cond', line: 6, color: 'default',
          temps, ans: [...ans], stack: [...stack], i, j: -1, t,
          explTitle: `Warmer Day Found!`,
          explText: `The current temperature (${t}°) is greater than the top of the stack (${temps[stack[stack.length - 1]]}° at index ${stack[stack.length - 1]}).`
        }, ctx);

        let j = stack.pop();
        domPushState(seq, {
          kind: 'pop', line: 7, color: 'amber',
          temps, ans: [...ans], stack: [...stack], i, j, t,
          explTitle: `Pop Index`,
          explText: `We pop index ${j} from the stack.`
        }, ctx);

        ans[j] = i - j;
        domPushState(seq, {
          kind: 'update-ans', line: 8, color: 'emerald',
          temps, ans: [...ans], stack: [...stack], i, j, t,
          explTitle: `Update Answer`,
          explText: `We waited ${i} - ${j} = ${ans[j]} days for a warmer temperature after day ${j}. Update ans[${j}].`
        }, ctx);
      }

      stack.push(i);
      domPushState(seq, {
        kind: 'push', line: 9, color: 'emerald',
        temps, ans: [...ans], stack: [...stack], i, j: -1, t,
        explTitle: `Push Index`,
        explText: `Push current day index ${i} onto the stack.`
      }, ctx);
    }

    domPushState(seq, {
      kind: 'done', line: 10, color: 'emerald',
      temps, ans: [...ans], stack: [...stack], i: n, j: -1, t: null,
      explTitle: 'Complete',
      explText: `All days processed. The remaining indices in the stack never saw a warmer day, so their answers remain 0.`,
      pause: true
    }, ctx);

    return seq;
  },
  renderDOM(container, s, spec) {
    const getTempsHTML = (temps, activeI, activeJ) => {
        return temps.map((t, idx) => {
            let cls = '';
            if (idx === activeI) cls = 'active-k'; 
            else if (idx === activeJ) cls = 'active-1';
            
            let pointers = '';
            if (idx === activeI) pointers += '<div class="pointer" style="color:#34d399">↓ i</div>';
            if (idx === activeJ) pointers += '<div class="pointer" style="color:var(--accent)">↓ j</div>';
            
            return `
            <div class="array-node ${cls}">
                ${pointers}
                ${t}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getAnsHTML = (ans, activeJ) => {
        return ans.map((a, idx) => {
            let cls = '';
            if (idx === activeJ) cls = 'active-1';
            else if (a > 0 || idx < s.i && !s.stack.includes(idx)) cls = 'merged'; // Answered
            
            return `
            <div class="array-node ${cls}">
                ${a}
                <div class="node-index">${idx}</div>
    </div>`;
        }).join('');
    };

    const getStackHTML = (stack, temps) => {
        if (stack.length === 0) {
            return `<div style="text-align:center; padding:20px; color:var(--text-dim);">Empty Stack</div>`;
        }
        return stack.map((item, idx) => {
            let isTop = idx === stack.length - 1;
            return `
            <div class="array-node ${isTop ? 'active-1' : ''}" style="margin-bottom:5px; min-width:80px; position:relative;">
                <span style="font-size:12px; color:var(--text-dim);">idx:</span> ${item} <span style="font-size:12px; color:var(--text-dim);">(${temps[item]}°)</span>
                ${isTop ? '<div class="pointer" style="position:absolute; right:-35px; top:15px; color:#3b82f6;">← top</div>' : ''}
            </div>`;
        }).reverse().join('');
    };

    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">temperatures</div>
                  <div class="array-track">${getTempsHTML(s.temps, s.i, s.j)}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">ans</div>
                  <div class="array-track">${getAnsHTML(s.ans, s.j)}</div>
              </div>
              <div class="glass-panel stack-container" style="display:flex; flex-direction:column; align-items:center;">
                  <div class="panel-heading" style="align-self:flex-start;">Stack (Indices)</div>
                  <div style="display:flex; flex-direction:column; justify-content:flex-end; min-height:150px; padding:10px;">
                      ${getStackHTML(s.stack, s.temps)}
                  </div>
              </div>
    </div>`;
  }
});
