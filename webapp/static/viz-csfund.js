/* ============================================================================
   Interactive labs for CS Fundamentals Deep Dives.
   1. OS: False Sharing (MESI Cache Ping-Pong)
   2. Networking: TCP CUBIC vs BBR Race
   3. DBs: LSM Tree Compaction Engine
   4. SW Arch: Saga Compensating Transactions
   5. OS: Live Architecture — Process & Data Flow Through the OS
   ========================================================================= */
'use strict';

/* 1. OS: False Sharing (MESI Cache Invalidation) */
defineLab('false-sharing', (host) => {
  host.innerHTML = `
    <div class="lab-split">
      <div class="lab-col lab-canvas-wrap"><canvas width="400" height="200"></canvas></div>
      <div class="lab-col lab-controls">
        <label><input type="checkbox" id="fsPad"> Add padding (separate cache lines)</label>
        <button id="fsT1" class="btn">T1 Writes A</button>
        <button id="fsT2" class="btn">T2 Writes B</button>
        <div class="lab-stats">
          <div class="lab-stat"><div class="lab-stat-val" id="fsInvalidates">0</div><div class="lab-stat-lbl">RFO invalidations</div></div>
        </div>
      </div>
    </div>
    <div class="lab-caption" id="fsCap">Both variables sit on the same 64-byte cache line.</div>
  `;
  const P = labPalette(host);
  const canvas = host.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  
  let padded = false;
  let invalidates = 0;
  
  // State: E (Exclusive), S (Shared), I (Invalid), M (Modified)
  let core1State = 'E';
  let core2State = 'I';
  
  // Animation signals
  let signals = [];
  
  host.querySelector('#fsPad').onchange = e => {
    padded = e.target.checked;
    invalidates = 0;
    core1State = 'E';
    core2State = 'E';
    host.querySelector('#fsInvalidates').textContent = '0';
    host.querySelector('#fsCap').innerHTML = padded 
      ? 'Variables isolated to separate cache lines. <b>No false sharing.</b>' 
      : 'Both variables sit on the same 64-byte cache line. <b>False sharing occurs.</b>';
  };
  
  const write = (core) => {
    if (padded) {
      // Isolated, no invalidation cross-talk
      if (core === 1) core1State = 'M';
      if (core === 2) core2State = 'M';
      return;
    }
    
    // False sharing! writing to one invalidates the other
    if (core === 1) {
      core1State = 'M';
      if (core2State !== 'I') {
        core2State = 'I';
        invalidates++;
        signals.push({ x: 200, y: 150, tx: 300, ty: 70, t: 0, color: P.err }); // C1 -> Bus -> C2
      }
    } else {
      core2State = 'M';
      if (core1State !== 'I') {
        core1State = 'I';
        invalidates++;
        signals.push({ x: 200, y: 150, tx: 100, ty: 70, t: 0, color: P.err }); // C2 -> Bus -> C1
      }
    }
    host.querySelector('#fsInvalidates').textContent = invalidates;
  };
  
  host.querySelector('#fsT1').onclick = () => write(1);
  host.querySelector('#fsT2').onclick = () => write(2);

  return (dt) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw Bus
    D.line(ctx, 50, 150, 350, 150, P.strong, 4);
    D.text(ctx, 'Cache-coherent interconnect', 200, 165, { color: P.dim, align: 'center' });
    
    // Draw Core 1
    D.line(ctx, 100, 70, 100, 150, P.strong, 2);
    ctx.fillStyle = P.surface2;
    ctx.strokeStyle = P.border;
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(40, 20, 120, 50, 6); ctx.fill(); ctx.stroke();
    D.text(ctx, 'Core 1 (Var A)', 100, 35, { color: P.text, align: 'center', weight: 600 });
    
    // Draw Core 2
    D.line(ctx, 300, 70, 300, 150, P.strong, 2);
    ctx.fillStyle = P.surface2;   // D.text above left fillStyle on the text colour
    ctx.beginPath(); ctx.roundRect(240, 20, 120, 50, 6); ctx.fill(); ctx.stroke();
    D.text(ctx, 'Core 2 (Var B)', 300, 35, { color: P.text, align: 'center', weight: 600 });
    
    // Draw Cache States
    const drawState = (x, y, state) => {
      let color = P.faint;
      if (state === 'M') color = P.accent;
      if (state === 'I') color = P.err;
      if (state === 'E' || state === 'S') color = P.ok;
      D.text(ctx, `MESI: ${state}`, x, y, { color, align: 'center', weight: 700 });
    };
    drawState(100, 55, core1State);
    drawState(300, 55, core2State);
    
    // Animate Signals
    for (let i = signals.length - 1; i >= 0; i--) {
      let s = signals[i];
      s.t += dt * 3;
      if (s.t > 1) {
        signals.splice(i, 1);
        continue;
      }
      const x = lerp(s.x, s.tx, s.t);
      const y = lerp(s.y, s.ty, s.t);
      ctx.fillStyle = s.color;
      ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI*2); ctx.fill();
    }
  };
});


/* 2. Networking: TCP BBR vs CUBIC Race */
defineLab('tcp-bbr', (host) => {
  host.innerHTML = `
    <div class="lab-split">
      <div class="lab-col lab-canvas-wrap"><canvas width="400" height="200"></canvas></div>
      <div class="lab-col lab-controls">
        <label>Packet Loss Rate: <span id="bbrLossVal">1%</span>
          <input type="range" id="bbrLoss" min="0" max="50" value="10">
        </label>
        <div class="lab-stats">
          <div class="lab-stat"><div class="lab-stat-val" id="bbrCubic" style="color:var(--series-0)">0</div><div class="lab-stat-lbl">CUBIC window</div></div>
          <div class="lab-stat"><div class="lab-stat-val" id="bbrBbr" style="color:var(--series-2)">0</div><div class="lab-stat-lbl">BBR window</div></div>
        </div>
      </div>
    </div>
    <div class="lab-caption" id="bbrCap">On every loss CUBIC cuts its window by 30% (β = 0.7), so a lossy path keeps it small. BBR models bandwidth and RTT instead, so random loss barely moves it.</div>
  `;
  const P = labPalette(host);
  const canvas = host.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  
  let lossRate = 0.01;
  host.querySelector('#bbrLoss').oninput = e => {
    lossRate = e.target.value / 1000; // 0 to 5%
    host.querySelector('#bbrLossVal').textContent = (lossRate*100).toFixed(1) + '%';
  };
  
  let cubicCwnd = 10;
  let bbrCwnd = 10;
  let t = 0;
  
  const historyC = [];
  const historyB = [];

  return (dt) => {
    t += dt;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Simulate CUBIC
    if (Math.random() < lossRate) {
      cubicCwnd = Math.max(2, cubicCwnd * 0.7); // CUBIC's multiplicative decrease: β = 0.7, not a halving
    } else {
      cubicCwnd += 50 * dt; // Linear increase
    }
    cubicCwnd = Math.min(100, cubicCwnd);
    
    // Simulate BBR (resilient to loss, stays around 80-100 based on BDP)
    if (Math.random() < 0.02) {
      bbrCwnd = 80 + Math.random() * 20; // Probing bandwidth
    } else {
      bbrCwnd = lerp(bbrCwnd, 90, dt * 2);
    }
    
    host.querySelector('#bbrCubic').textContent = Math.round(cubicCwnd);
    host.querySelector('#bbrBbr').textContent = Math.round(bbrCwnd);
    
    historyC.push(cubicCwnd);
    historyB.push(bbrCwnd);
    if (historyC.length > canvas.width) { historyC.shift(); historyB.shift(); }
    
    // Draw grid
    D.line(ctx, 0, 180, 400, 180, P.strong, 2);
    D.line(ctx, 0, 20, 400, 20, P.soft, 1, [4, 4]);
    
    // Draw lines
    const drawLine = (hist, color) => {
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.lineJoin = 'round';
      for (let i = 0; i < hist.length; i++) {
        const x = canvas.width - hist.length + i;
        const y = 180 - (hist[i] / 100) * 160;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };
    
    drawLine(historyC, P.series[0]); // CUBIC blue
    drawLine(historyB, P.series[2]); // BBR green
    
    D.text(ctx, 'Capacity (BDP)', 10, 15, { color: P.faint, size: 10 });
  };
});


/* 3. Databases: LSM Tree Compaction Engine */
defineLab('lsm-tree', (host) => {
  host.innerHTML = `
    <div class="lab-split">
      <div class="lab-col lab-canvas-wrap"><canvas width="400" height="200"></canvas></div>
      <div class="lab-col lab-controls" style="align-items: center; justify-content: center;">
        <button id="lsmWrite" class="btn" style="width:100%; padding: 16px;">Write Random Key</button>
        <div style="height:20px"></div>
        <div class="lab-stats">
          <div class="lab-stat"><div class="lab-stat-val" id="lsmMem">0/4</div><div class="lab-stat-lbl">MemTable</div></div>
        </div>
      </div>
    </div>
    <div class="lab-caption" id="lsmCap">A write appends to the WAL for durability and lands in the in-memory MemTable. When it fills, it flushes to disk as an immutable SSTable — and compaction later rewrites that data again, which is where write amplification comes from.</div>
  `;
  const P = labPalette(host);
  const canvas = host.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  
  let memTable = [];
  let diskL0 = [];
  let diskL1 = [];
  let compacting = 0; // animation timer
  
  const flush = () => {
    diskL0.push([...memTable].sort((a,b)=>a-b));
    memTable = [];
    if (diskL0.length >= 3) {
      compacting = 1.0;
    }
  };
  
  host.querySelector('#lsmWrite').onclick = () => {
    if (compacting > 0) return;
    memTable.push(Math.floor(Math.random() * 99));
    if (memTable.length >= 4) flush();
    host.querySelector('#lsmMem').textContent = memTable.length + '/4';
  };

  return (dt) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (compacting > 0) {
      compacting -= dt * 0.5;
      if (compacting <= 0) {
        // execute compaction
        let merged = new Set();
        diskL0.forEach(t => t.forEach(k => merged.add(k)));
        diskL1.forEach(t => t.forEach(k => merged.add(k)));
        diskL1 = [Array.from(merged).sort((a,b)=>a-b).slice(0, 6)]; // simplified merge
        diskL0 = [];
        compacting = 0;
      }
    }
    
    // Draw MemTable
    D.text(ctx, 'MemTable (RAM)', 20, 20, { color: P.text, weight: 600 });
    ctx.fillStyle = P.surface2; ctx.strokeStyle = P.border; ctx.lineWidth=2;
    ctx.beginPath(); ctx.roundRect(20, 30, 160, 30, 4); ctx.fill(); ctx.stroke();
    for (let i = 0; i < memTable.length; i++) {
      ctx.fillStyle = P.series[0];
      ctx.beginPath(); ctx.roundRect(25 + i*38, 35, 34, 20, 2); ctx.fill();
      D.text(ctx, memTable[i], 42 + i*38, 45, { color: '#fff', align: 'center', size: 10 });
    }
    
    D.line(ctx, 20, 80, 380, 80, P.strong, 2, [5, 5]);
    
    // Draw Disk
    D.text(ctx, 'Disk SSTables', 20, 95, { color: P.text, weight: 600 });
    
    D.text(ctx, 'L0:', 20, 120, { color: P.dim });
    for (let i = 0; i < diskL0.length; i++) {
      let yOffset = compacting > 0 ? compacting * 40 : 0; // move down during compaction
      ctx.fillStyle = compacting > 0 ? P.series[1] : P.surface2;
      ctx.beginPath(); ctx.roundRect(45 + i*110, 105 + (compacting>0 ? (1-compacting)*40 : 0), 100, 25, 4); ctx.fill(); ctx.stroke();
      D.text(ctx, 'SSTable ' + i, 95 + i*110, 117 + (compacting>0 ? (1-compacting)*40 : 0), { color: P.text, align: 'center', size: 10 });
    }
    
    D.text(ctx, 'L1:', 20, 160, { color: P.dim });
    for (let i = 0; i < diskL1.length; i++) {
      ctx.fillStyle = P.surface2;
      ctx.beginPath(); ctx.roundRect(45 + i*110, 145, 100, 25, 4); ctx.fill(); ctx.stroke();
      D.text(ctx, 'Merged SST', 95 + i*110, 157, { color: P.text, align: 'center', size: 10 });
    }
    
    if (compacting > 0) {
      D.text(ctx, 'COMPACTING...', 200, 100, { color: P.accent, align: 'center', weight: 800, size: 24 });
    }
  };
});


/* 4. Software Engineering: Saga Compensator */
defineLab('saga-pattern', (host) => {
  host.innerHTML = `
    <div class="lab-split">
      <div class="lab-col lab-canvas-wrap"><canvas width="400" height="200"></canvas></div>
      <div class="lab-col lab-controls" style="align-items: center; justify-content: center;">
        <button id="sagaOK" class="btn" style="width:100%; margin-bottom: 8px;">Happy Path (Succeeds)</button>
        <button id="sagaFail" class="btn btn-outline" style="width:100%; border-color: var(--err); color: var(--err);">Fail Inventory (Compensate)</button>
      </div>
    </div>
    <div class="lab-caption" id="sagaCap">Choreography Saga: The failure in Inventory triggers a compensating event to refund the Payment.</div>
  `;
  const P = labPalette(host);
  const canvas = host.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  
  let msgs = [];
  let seq = 0; // 0=idle, 1=order, 2=pay, 3=inv, 4=done, 5=fail, 6=refund
  let failMode = false;
  let timer = 0;
  
  host.querySelector('#sagaOK').onclick = () => { seq = 1; timer = 0; msgs = []; failMode = false; };
  host.querySelector('#sagaFail').onclick = () => { seq = 1; timer = 0; msgs = []; failMode = true; };

  const addMsg = (sx, tx, txt, color) => {
    msgs.push({ x: sx, tx: tx, y: 130, t: 0, txt, color });
  };

  return (dt) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw Services
    const drawSvc = (x, name, icon) => {
      ctx.fillStyle = P.surface2; ctx.strokeStyle = P.border; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, 60, 30, 0, Math.PI*2); ctx.fill(); ctx.stroke();
      D.text(ctx, icon, x, 55, { size: 20, align: 'center' });
      D.text(ctx, name, x, 105, { color: P.text, align: 'center', size: 12, weight: 600 });
      D.line(ctx, x, 90, x, 130, P.strong, 2); // line to bus
    };
    
    drawSvc(70, 'Order', '🛒');
    drawSvc(200, 'Payment', '💳');
    drawSvc(330, 'Inventory', '📦');
    
    // Draw Event Bus
    D.line(ctx, 30, 130, 370, 130, P.accent, 4);
    D.text(ctx, 'Event Bus (Kafka/RabbitMQ)', 200, 145, { color: P.accent, align: 'center', size: 10, weight: 600 });
    
    // Logic
    if (seq > 0) {
      timer += dt;
      if (seq === 1 && timer > 0.1) {
        addMsg(70, 200, 'OrderCreated', P.series[0]);
        seq = 2; timer = 0;
      }
      if (seq === 2 && timer > 1.0) {
        addMsg(200, 330, 'PaymentSuccess', P.series[2]);
        seq = 3; timer = 0;
      }
      if (seq === 3 && timer > 1.0) {
        if (failMode) {
          addMsg(330, 200, 'InventoryFail!', P.err);
          seq = 5; timer = 0;
        } else {
          addMsg(330, 70, 'OrderComplete', P.ok);
          seq = 4;
        }
      }
      if (seq === 5 && timer > 1.0) {
        addMsg(200, 70, 'Refunded', P.series[3]);
        seq = 6;
      }
    }
    
    // Draw Msgs
    for (let i = msgs.length - 1; i >= 0; i--) {
      let m = msgs[i];
      m.t += dt * 1.5;
      if (m.t > 1) { msgs.splice(i, 1); continue; }
      
      const cx = lerp(m.x, m.tx, m.t);
      ctx.fillStyle = m.color;
      ctx.beginPath(); ctx.arc(cx, m.y, 8, 0, Math.PI*2); ctx.fill();
      D.text(ctx, m.txt, cx, m.y - 15, { color: m.color, align: 'center', size: 11, weight: 700 });
    }
  };
});


/* 5. OS: Live Architecture — Process & Data Flow Through the OS
   An AWS-style component diagram (grouped panels, colored icon badges,
   faint permanent connectors) with a live animated "packet" that walks a
   real request end to end — a syscall, a scheduling decision, a page
   fault, a socket write — cycling automatically, with buttons to jump
   straight to any one flow. */
defineLab('os-architecture', (host) => {
  host.innerHTML = `
    <div class="lab-canvas-wrap"><canvas width="860" height="480"></canvas></div>
    <div class="lab-controls" id="osaFlowBtns"></div>
    <div class="lab-caption" id="osaCap"></div>
  `;
  const P = labPalette(host);
  const canvas = host.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const capEl = host.querySelector('#osaCap');
  const btnWrap = host.querySelector('#osaFlowBtns');

  /* ---- layout: every box's canvas-space rect, category and badge ---- */
  const boxes = {
    app1:       { x: 110, y: 54,  w: 260, h: 54, label: 'Your Application',    sub: '',      cat: 'app',     badge: 'A1' },
    app2:       { x: 470, y: 54,  w: 260, h: 54, label: 'Another Application', sub: '',      cat: 'app',     badge: 'A2' },
    syscall:    { x: 60,  y: 134, w: 740, h: 30, label: 'System Call Interface — the only door across', sub: '', cat: 'gate', badge: '' },
    scheduler:  { x: 40,  y: 214, w: 140, h: 54, label: 'Scheduler',      sub: '§1',    cat: 'kernel',  badge: 'SH' },
    memory:     { x: 194, y: 214, w: 140, h: 54, label: 'Memory Manager', sub: '§5',    cat: 'kernel',  badge: 'MM' },
    filesystem: { x: 348, y: 214, w: 140, h: 54, label: 'File System',    sub: '§5/§7', cat: 'kernel',  badge: 'FS' },
    iomanager:  { x: 502, y: 214, w: 140, h: 54, label: 'I/O Manager',    sub: '§4/§7', cat: 'kernel',  badge: 'IO' },
    network:    { x: 656, y: 214, w: 140, h: 54, label: 'Network Stack', sub: '§7',    cat: 'kernel',  badge: 'NS' },
    cpu:        { x: 40,  y: 402, w: 175, h: 50, label: 'CPU cores',     sub: '',      cat: 'compute', badge: 'CP' },
    ram:        { x: 235, y: 402, w: 175, h: 50, label: 'RAM',           sub: '',      cat: 'compute', badge: 'RM' },
    disk:       { x: 430, y: 402, w: 175, h: 50, label: 'Disk',          sub: '',      cat: 'storage', badge: 'DK' },
    nic:        { x: 625, y: 402, w: 175, h: 50, label: 'Network Card',  sub: '',      cat: 'network', badge: 'NC' },
  };

  const panels = [
    { x: 20, y: 14,  w: 820, h: 110, label: 'USER SPACE — no direct hardware access' },
    { x: 20, y: 176, w: 820, h: 170, label: 'KERNEL SPACE — privileged, talks to hardware directly' },
    { x: 20, y: 366, w: 820, h: 104, label: 'HARDWARE' },
  ];

  /* permanent faint connectors, drawn under whichever path is animating */
  const links = [
    ['app1', 'syscall'], ['app2', 'syscall'],
    ['syscall', 'scheduler'], ['syscall', 'memory'], ['syscall', 'filesystem'], ['syscall', 'iomanager'], ['syscall', 'network'],
    ['scheduler', 'cpu'], ['memory', 'ram'],
    ['filesystem', 'disk'], ['filesystem', 'ram', 'dashed'],
    ['iomanager', 'disk'], ['iomanager', 'nic'],
    ['network', 'nic'],
  ];

  const catColor = cat => ({
    app: P.series[4], gate: P.accent, kernel: P.series[0],
    compute: P.series[1], storage: P.ok, network: P.series[5],
  }[cat] || P.dim);

  /* ---- named flows: a real request walking box to box ---- */
  const flows = [
    { label: 'Schedule a thread', path: ['app1', 'syscall', 'scheduler', 'cpu'], steps: [
      "Your app calls a blocking function — the CPU can't run it until the kernel is asked.",
      "The scheduler picks which runnable thread gets this core next (CFS's vruntime tree, §1).",
      'The chosen thread is context-switched onto a CPU core and runs.',
    ] },
    { label: 'Read a cached file', path: ['app2', 'syscall', 'filesystem', 'ram'], steps: [
      'Your app calls read() on a file it already opened.',
      'The file system looks the page up in the page cache first (§5).',
      'Already in RAM — no disk touched at all. This is the fast, common case.',
    ] },
    { label: 'Page fault (disk read)', path: ['app1', 'syscall', 'memory', 'disk', 'ram'], steps: [
      "Your app touches memory that isn't resident yet.",
      'The memory manager takes a page fault (§5).',
      'Major fault: the page has to be read from disk — this one costs milliseconds.',
      'Once loaded into RAM, the faulting instruction resumes as if nothing happened.',
    ] },
    { label: 'Send a network packet', path: ['app2', 'syscall', 'network', 'nic'], steps: [
      'Your app calls write() on a socket.',
      'The network stack segments the data and queues it for transmission (§7).',
      'The NIC driver DMAs the packet out onto the wire.',
    ] },
    { label: 'Write a file to disk', path: ['app1', 'syscall', 'iomanager', 'disk'], steps: [
      'Your app calls write() on a file descriptor.',
      'The I/O manager routes the request to the right device driver (§4).',
      "write() returns once the bytes reach the kernel — durability still needs fsync() (§5).",
    ] },
  ];

  let flowIdx = 0, hopIdx = 0, phase = 'move', t = 0;
  const MOVE_T = 1.15, PAUSE_T = 1.1, FLOW_PAUSE_T = 1.3;

  flows.forEach((f, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn';
    b.textContent = f.label;
    b.onclick = () => { flowIdx = i; hopIdx = 0; phase = 'move'; t = 0; updateCaption(); };
    btnWrap.append(b);
  });

  function updateCaption() {
    const f = flows[flowIdx];
    const stepText = f.steps[hopIdx] || f.steps[f.steps.length - 1];
    capEl.innerHTML = `<b>${esc(f.label)}</b> — ${esc(stepText)}`;
    [...btnWrap.children].forEach((b, i) => b.classList.toggle('is-on', i === flowIdx));
  }
  updateCaption();

  const anchor = (id, side) => {
    const b = boxes[id];
    if (side === 'top') return [b.x + b.w / 2, b.y];
    if (side === 'bottom') return [b.x + b.w / 2, b.y + b.h];
    if (side === 'left') return [b.x, b.y + b.h / 2];
    return [b.x + b.w, b.y + b.h / 2];
  };
  const edgePoints = (fromId, toId) => {
    const a = boxes[fromId], b = boxes[toId];
    if (a.y + a.h <= b.y) return [anchor(fromId, 'bottom'), anchor(toId, 'top')];
    if (b.y + b.h <= a.y) return [anchor(fromId, 'top'), anchor(toId, 'bottom')];
    return a.x < b.x ? [anchor(fromId, 'right'), anchor(toId, 'left')] : [anchor(fromId, 'left'), anchor(toId, 'right')];
  };

  return (dt) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    panels.forEach(p => {
      ctx.fillStyle = P.alpha('surface', .55);
      ctx.strokeStyle = P.soft; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.roundRect(p.x, p.y, p.w, p.h, 12); ctx.fill(); ctx.stroke();
      D.text(ctx, p.label, p.x + 12, p.y + 14, { color: P.faint, size: 10.5, weight: 700 });
    });

    links.forEach(([from, to, style]) => {
      const [[x1, y1], [x2, y2]] = edgePoints(from, to);
      D.line(ctx, x1, y1, x2, y2, P.soft, 1.4, style === 'dashed' ? [4, 4] : undefined);
    });

    /* ---- advance the flow/hop/phase state machine ---- */
    {
      const cur = flows[flowIdx];
      const totalHops = cur.path.length - 1;
      if (phase === 'move') {
        t += dt / MOVE_T;
        if (t >= 1) { t = 0; phase = 'pause'; }
      } else if (phase === 'pause') {
        t += dt / PAUSE_T;
        if (t >= 1) {
          t = 0;
          if (hopIdx < totalHops - 1) { hopIdx++; phase = 'move'; updateCaption(); }
          else phase = 'flowpause';
        }
      } else if (phase === 'flowpause') {
        t += dt / FLOW_PAUSE_T;
        if (t >= 1) {
          t = 0; hopIdx = 0; phase = 'move';
          flowIdx = (flowIdx + 1) % flows.length;
          updateCaption();
        }
      }
    }

    /* ---- render the now-current flow's progress ---- */
    const f = flows[flowIdx];
    const activeIds = new Set(f.path);
    const traveled = f.path.slice(0, hopIdx + 1);
    for (let i = 0; i < traveled.length - 1; i++) {
      const [[x1, y1], [x2, y2]] = edgePoints(traveled[i], traveled[i + 1]);
      D.line(ctx, x1, y1, x2, y2, P.accent, 3);
    }
    if (phase === 'move') {
      const [[x1, y1], [x2, y2]] = edgePoints(f.path[hopIdx], f.path[hopIdx + 1]);
      const et = 1 - Math.pow(1 - clamp(t, 0, 1), 2);
      const px = lerp(x1, x2, et), py = lerp(y1, y2, et);
      D.line(ctx, x1, y1, px, py, P.accent, 3);
      ctx.beginPath(); ctx.arc(px, py, 13, 0, TAU); ctx.fillStyle = P.alpha('accent', .22); ctx.fill();
      D.dot(ctx, px, py, 6.5, P.accent, P.bg, 2);
    }

    Object.entries(boxes).forEach(([id, b]) => {
      const isActive = activeIds.has(id);
      const isDone = traveled.includes(id) || (phase !== 'move' && f.path[hopIdx + 1] === id);
      const c = catColor(b.cat);
      ctx.globalAlpha = isActive ? 1 : .45;
      ctx.fillStyle = P.surface2;
      ctx.strokeStyle = isDone ? P.accent : c;
      ctx.lineWidth = isDone ? 2.4 : 1.6;
      ctx.beginPath(); ctx.roundRect(b.x, b.y, b.w, b.h, 10); ctx.fill(); ctx.stroke();
      if (b.badge) {
        const bs = 18;
        ctx.fillStyle = c;
        ctx.beginPath(); ctx.roundRect(b.x + 8, b.y + b.h / 2 - bs / 2, bs, bs, 4); ctx.fill();
        D.text(ctx, b.badge, b.x + 8 + bs / 2, b.y + b.h / 2, { color: '#fff', size: 8, align: 'center', weight: 800 });
        D.text(ctx, b.label, b.x + 8 + bs + 8, b.y + b.h / 2 - (b.sub ? 6 : 0), { color: P.text, size: 12.5, weight: 650 });
        if (b.sub) D.text(ctx, b.sub, b.x + 8 + bs + 8, b.y + b.h / 2 + 10, { color: P.faint, size: 10 });
      } else {
        D.text(ctx, b.label, b.x + b.w / 2, b.y + b.h / 2, { color: P.text, size: 11.5, align: 'center', weight: 650 });
      }
      ctx.globalAlpha = 1;
    });
  };
});
