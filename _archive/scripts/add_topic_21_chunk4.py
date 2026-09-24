content = """
defineAlgo('21_math_geometry', {
  title: 'Detect Squares', short: 'Detect Squares',
  idea: 'Maintain counts of all points. For a query point (x, y), iterate through all points (px, py). If they form a valid diagonal (abs(px-x) == abs(py-y) and x != px), check if the other two corners (x, py) and (px, y) exist.',
  complexity: 'Time O(N) per query · Space O(N)',
  input: '[3, 10], [11, 2], [3, 2], query(11, 10)', hint: 'List of added points, then query point',
  code: [
    'class DetectSquares:',
    '    def __init__(self):',
    '        self.ptsCount = collections.defaultdict(int)',
    '        self.pts = []',
    '',
    '    def add(self, point):',
    '        self.ptsCount[tuple(point)] += 1',
    '        self.pts.append(point)',
    '',
    '    def count(self, point):',
    '        res = 0',
    '        qx, qy = point',
    '        for x, y in self.pts:',
    '            if abs(x - qx) != abs(y - qy) or x == qx:',
    '                continue',
    '            res += self.ptsCount[(x, qy)] * self.ptsCount[(qx, y)]',
    '        return res'
  ],
  parse(str) {
    // A simplified parser assuming format like: "[3, 10], [11, 2], [3, 2], [11, 10]" 
    // where the last one is the query point.
    let arr = str.replace(/[^\d,]/g, '').split(',');
    let points = [];
    for (let i = 0; i < arr.length; i += 2) {
       if(arr[i] && arr[i+1]) {
           points.push([parseInt(arr[i]), parseInt(arr[i+1])]);
       }
    }
    if (points.length < 2) return { points: [], query: [0, 0] };
    const query = points.pop();
    return { points, query };
  },
  run({ points, query }) {
    const { F, snap } = avRecorder();
    
    let ptsCount = {};
    for (let p of points) {
        let key = p[0] + ',' + p[1];
        ptsCount[key] = (ptsCount[key] || 0) + 1;
    }
    
    const [qx, qy] = query;
    let res = 0;
    
    let s = { points, query, qx, qy, ptsCount, res, currP: null, p2: null, p4: null, added: 0 };
    snap(2, `Added points to map. Query point is [${qx}, ${qy}]. Initialize res = 0.`, s);
    
    for (let p of points) {
        const [x, y] = p;
        s.currP = p;
        s.p2 = null;
        s.p4 = null;
        s.added = 0;
        
        if (Math.abs(x - qx) !== Math.abs(y - qy) || x === qx) {
            snap(13, `Point [${x}, ${y}] does not form a valid diagonal with [${qx}, ${qy}]. Skip.`, s);
            continue;
        }
        
        s.p2 = [x, qy];
        s.p4 = [qx, y];
        
        let count2 = ptsCount[x + ',' + qy] || 0;
        let count4 = ptsCount[qx + ',' + y] || 0;
        
        let squares = count2 * count4;
        res += squares;
        
        s.res = res;
        s.added = squares;
        
        snap(15, `Point [${x}, ${y}] forms a diagonal! Check corners [${x}, ${qy}] (count: ${count2}) and [${qx}, ${y}] (count: ${count4}). Added ${squares} squares.`, s);
    }
    
    s.currP = null; s.p2 = null; s.p4 = null; s.added = 0;
    snap(17, `Finished. Total squares found: ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px;">
            Query Point (p1): <span style="font-weight:bold; color:var(--accent);">[${state.qx}, ${state.qy}]</span>
        </div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current Diagonal Point (p3)</div>
                <div style="font-size:24px; font-weight:bold; color:${state.currP ? '#fbbf24' : 'var(--text-dim)'};">${state.currP ? `[${state.currP[0]}, ${state.currP[1]}]` : 'None'}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Total Squares (res)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.res}</div>
            </div>
        </div>`;
        
    if (state.p2 && state.p4) {
        let count2 = state.ptsCount[state.p2[0] + ',' + state.p2[1]] || 0;
        let count4 = state.ptsCount[state.p4[0] + ',' + state.p4[1]] || 0;
        
        html += `<div style="padding:15px; border:1px solid #34d399; border-radius:8px; background:rgba(52,211,153,0.1);">
            <div style="font-size:14px; margin-bottom:5px;">Other Required Corners:</div>
            <div style="display:flex; gap:20px; font-weight:bold;">
                <div>p2: [${state.p2[0]}, ${state.p2[1]}] (Found: ${count2})</div>
                <div>p4: [${state.p4[0]}, ${state.p4[1]}] (Found: ${count4})</div>
            </div>
            <div style="margin-top:10px; color:#34d399; font-weight:bold;">=> ${count2} * ${count4} = ${state.added} squares added!</div>
        </div>`;
    }
    
    let allPtsStr = Object.entries(state.ptsCount).map(([k, v]) => `[${k}]: ${v}`).join(', ');
    html += `<div style="font-size:12px; color:var(--text-dim); margin-top:10px;">Stored Points: { ${allPtsStr} }</div>`;
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Max Points on a Line', short: 'Max Points',
  idea: 'For each point, calculate the slopes to all other points. Keep a map of slopes to counts. The maximum number of points on a line going through this point is max(counts) + 1.',
  complexity: 'Time O(N^2) · Space O(N)',
  input: '[1,1],[2,2],[3,3]', hint: 'list of points',
  code: [
    'def maxPoints(points):',
    '    if len(points) <= 2: return len(points)',
    '    res = 0',
    '    for i in range(len(points)):',
    '        slopes = collections.defaultdict(int)',
    '        for j in range(i + 1, len(points)):',
    '            dx, dy = points[j][0] - points[i][0], points[j][1] - points[i][1]',
    '            if dx == 0:',
    '                slope = float("inf")',
    '            else:',
    '                slope = dy / dx',
    '            slopes[slope] += 1',
    '            res = max(res, slopes[slope] + 1)',
    '    return res'
  ],
  parse(str) {
    let arr = str.replace(/[^\d,-]/g, ' ').trim().split(/\s+/).map(x => x.replace(/,/g, ''));
    let points = [];
    for (let i = 0; i < arr.length; i += 2) {
       if(arr[i] && arr[i+1]) {
           points.push([parseInt(arr[i]), parseInt(arr[i+1])]);
       }
    }
    return { points };
  },
  run({ points }) {
    const { F, snap } = avRecorder();
    
    let s = { points, res: 0, p1: null, p2: null, slopes: {}, currSlope: null };
    
    if (points.length <= 2) {
        snap(2, '2 or fewer points, they always form a line.', s);
        return F;
    }
    
    snap(3, 'Initialize res = 0.', s);
    
    for (let i = 0; i < points.length; i++) {
        let slopes = {};
        s.p1 = points[i];
        s.slopes = slopes;
        s.p2 = null;
        s.currSlope = null;
        
        snap(5, `Anchor point: [${s.p1[0]}, ${s.p1[1]}]. Initialize slopes map.`, s);
        
        for (let j = i + 1; j < points.length; j++) {
            s.p2 = points[j];
            let dx = points[j][0] - points[i][0];
            let dy = points[j][1] - points[i][1];
            
            let slope = dx === 0 ? "inf" : (dy / dx).toFixed(4); // Simplified slope representation for viz
            // Need to fix precision issues in JS for floats, so we stringify with fixed precision.
            
            slopes[slope] = (slopes[slope] || 0) + 1;
            s.currSlope = slope;
            
            if (slopes[slope] + 1 > s.res) {
                s.res = slopes[slope] + 1;
            }
            
            s.slopes = {...slopes};
            snap(11, `Target point: [${s.p2[0]}, ${s.p2[1]}]. Slope is ${slope}. Map[${slope}] = ${slopes[slope]}. Current max result = ${s.res}.`, s);
        }
    }
    
    s.p1 = null; s.p2 = null; s.currSlope = null;
    snap(14, `Finished. Max points on a line: ${s.res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:15px; font-family:var(--mono);">
        <div style="font-size:18px;">Global Max Points: <span style="font-weight:bold; color:var(--accent); font-size:24px;">${state.res}</span></div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:2px solid #3b82f6; border-radius:8px; background:rgba(59,130,246,0.1); flex:1;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Anchor Point (p1)</div>
                <div style="font-size:20px; font-weight:bold; color:#3b82f6;">${state.p1 ? `[${state.p1[0]}, ${state.p1[1]}]` : 'None'}</div>
            </div>
            <div style="padding:15px; border:2px solid #ef4444; border-radius:8px; background:rgba(239,68,68,0.1); flex:1;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Target Point (p2)</div>
                <div style="font-size:20px; font-weight:bold; color:#ef4444;">${state.p2 ? `[${state.p2[0]}, ${state.p2[1]}]` : 'None'}</div>
            </div>
        </div>`;
        
    if (state.currSlope) {
        html += `<div style="padding:10px; border:1px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1); text-align:center;">
            Calculated Slope: <span style="font-weight:bold; color:#fbbf24;">${state.currSlope}</span>
        </div>`;
    }
    
    if (state.p1) {
        let mapStr = Object.entries(state.slopes).map(([k, v]) => `<span style="background:var(--surface); padding:3px 6px; border-radius:4px; margin-right:5px; border:1px solid var(--border);">${k} : ${v}</span>`).join(' ');
        html += `<div style="font-size:14px;">
            <div style="color:var(--text-dim); margin-bottom:5px;">Slopes Map for Anchor Point:</div>
            <div style="line-height:2;">${mapStr || 'Empty'}</div>
        </div>`;
    }
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 21 chunk 4.")
