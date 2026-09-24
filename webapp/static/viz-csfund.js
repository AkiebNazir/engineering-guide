/* ============================================================================
   Interactive labs for CS Fundamentals Deep Dives.
   1. OS: False Sharing (MESI Cache Ping-Pong)
   2. Networking: TCP CUBIC vs BBR Race
   3. DBs: LSM Tree Compaction Engine
   4. SW Arch: Saga Compensating Transactions
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
