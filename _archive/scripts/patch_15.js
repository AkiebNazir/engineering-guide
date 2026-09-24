
defineAlgo('15_advanced_graphs', {
  title: 'Network Delay Time', short: 'Network Delay Time',
  idea: 'Dijkstra\'s algorithm. We want the time for the slowest node to receive the signal, which is the maximum shortest path from the start node `k`. We use a min-heap to always expand the closest unvisited node.',
  complexity: 'Time O((V + E) log V) · Space O(V + E)',
  input: '4; 2; 2,1,1; 2,3,1; 3,4,1', hint: 'n; k; u,v,w; ...',
  code: [
    'def networkDelayTime(times, n, k):',
    '    adj = collections.defaultdict(list)',
    '    for u, v, w in times:',
    '        adj[u].append((v, w))',
    '    ',
    '    dist = [float("inf")] * (n + 1)',
    '    dist[k] = 0',
    '    heap = [(0, k)]',
    '    while heap:',
    '        d, u = heapq.heappop(heap)',
    '        if d > dist[u]: continue',
    '        ',
    '        for v, w in adj[u]:',
    '            if d + w < dist[v]:',
    '                dist[v] = d + w',
    '                heapq.heappush(heap, (d + w, v))',
    '    ',
    '    reach = dist[1:n+1]',
    '    return max(reach) if float("inf") not in reach else -1',
  ],
  parse(str) {
    const parts = str.split(';');
    if (parts.length < 2) throw new Error("Input must contain at least n and k, separated by semicolons.");
    const n = parseInt(parts[0].trim());
    const k = parseInt(parts[1].trim());
    if (isNaN(n) || isNaN(k)) throw new Error("n and k must be integers.");
    const times = parts.slice(2).filter(x => x.trim().length > 0).map(edge => {
       const vals = edge.split(',').map(Number);
       if (vals.length !== 3 || vals.some(isNaN)) throw new Error("Edges must be in format u,v,w");
       return vals;
    });
    return { n, k, times };
  },
  run({ n, k, times }) {
    const { F, snap } = avRecorder();
    
    const adj = {};
    for(let i=1; i<=n; i++) adj[i] = [];
    for(let [u, v, w] of times) {
       if (!adj[u]) adj[u] = [];
       adj[u].push([v, w]);
    }
    
    let dist = new Array(n+1).fill('inf');
    dist[k] = 0;
    
    let heap = [[0, k]]; 
    
    const s = { n, k, adj, dist: [...dist], heap: [...heap], u: null, d: null, v: null, w: null, nd: null };
    snap(6, `Initialize dist array with infinity, except k (${k}) which is 0. Push (0, ${k}) to heap.`, s);
    
    while(heap.length > 0) {
       heap.sort((a,b) => a[0] - b[0]);
       const [d, u] = heap.shift();
       
       s.d = d; s.u = u; s.dist = [...dist]; s.heap = [...heap];
       s.v = null; s.w = null; s.nd = null;
       
       snap(9, `Pop node ${u} from heap with distance ${d}.`, s);
       
       if (d > (dist[u] === 'inf' ? Infinity : dist[u])) {
          snap(10, `Distance ${d} is stale (greater than dist[${u}]). Skip.`, s);
          continue;
       }
       
       for(let [v, w] of (adj[u] || [])) {
          s.v = v; s.w = w;
          const currentDistV = dist[v] === 'inf' ? Infinity : dist[v];
          s.nd = d + w;
          snap(13, `Check neighbor ${v} with edge weight ${w}. New distance = ${d} + ${w} = ${s.nd}.`, s);
          
          if (s.nd < currentDistV) {
             dist[v] = s.nd;
             heap.push([s.nd, v]);
             s.dist = [...dist];
             s.heap = [...heap];
             snap(15, `Found shorter path to ${v} (${s.nd} < ${currentDistV === Infinity ? 'inf' : currentDistV}). Update dist[${v}] and push to heap.`, s);
          } else {
             snap(14, `Path to ${v} (${s.nd}) is not shorter than current dist (${currentDistV === Infinity ? 'inf' : currentDistV}). Skip.`, s);
          }
       }
    }
    
    s.u = null; s.d = null; s.v = null; s.w = null; s.nd = null;
    let reachable = dist.slice(1);
    let allReached = reachable.indexOf('inf') === -1;
    let maxDist = allReached ? Math.max(...reachable) : -1;
    snap(18, `Dijkstra finished. Maximum distance is ${maxDist}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getNodesHTML = () => {
       let html = '<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 20px;">';
       for(let i=1; i<=s.n; i++) {
          const isCurrent = i === s.u;
          const isNeighbor = i === s.v;
          const dStr = s.dist[i] === 'inf' ? '∞' : s.dist[i];
          let bg = 'var(--surface)';
          let border = 'var(--border)';
          
          if(isCurrent) { border = 'var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
          else if(isNeighbor) { border = '#34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
          
          html += `
          <div style="padding: 10px; border: 2px solid ${border}; border-radius: 8px; background: ${bg}; text-align: center; min-width: 60px;">
             <div style="font-weight: bold; color: var(--text);">Node ${i}</div>
             <div style="font-family: var(--mono); color: ${isCurrent ? 'var(--accent)' : 'var(--text-dim)'};">dist: ${dStr}</div>
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    const getHeapHTML = () => {
       if (s.heap.length === 0) return '<div style="color:var(--text-dim); font-family:var(--mono);">(empty)</div>';
       return '<div style="display:flex; gap:5px; flex-wrap:wrap;">' + s.heap.map(item => {
          return `<div style="padding: 4px 8px; border: 1px solid var(--border); border-radius: 12px; font-family: var(--mono); font-size: 12px; background: var(--surface);">(${item[0]}, node ${item[1]})</div>`;
       }).join('') + '</div>';
    };
    
    const getAdjHTML = () => {
       let html = '<div style="display:flex; flex-direction: column; gap: 5px; font-family: var(--mono); font-size: 13px;">';
       for(let i=1; i<=s.n; i++) {
          const edges = (s.adj[i] || []).map(e => `[${e[0]}, w=${e[1]}]`).join(', ');
          html += `<div style="${i === s.u ? 'color: var(--accent); font-weight: bold;' : 'color: var(--text-dim)'}">Node ${i}: ${edges || '(none)'}</div>`;
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction: column; gap: 15px; width: 100%; padding: 10px;">
          <div>
              <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Nodes & Distances</div>
              ${getNodesHTML()}
          </div>
          <div style="display:flex; gap: 20px;">
              <div style="flex: 1; min-width: 0;">
                  <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Priority Queue (Heap)</div>
                  ${getHeapHTML()}
              </div>
              <div style="flex: 1; min-width: 0;">
                  <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Adjacency List</div>
                  ${getAdjHTML()}
              </div>
          </div>
      </div>
    `;
  }
});
