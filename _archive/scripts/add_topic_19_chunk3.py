import sys

content = """
defineAlgo('19_intervals', {
  title: 'Car Pooling', short: 'Car Pooling',
  idea: 'Sweep-line algorithm. Create events: `(start, passengers)` and `(end, -passengers)`. Sort events (process drop-offs before pick-ups at same time). Accumulate passengers and check against capacity.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '2,1,5; 3,3,7| 4', hint: 'triplets (passengers, start, end) split by ; | capacity',
  code: [
    'def carPooling(trips, capacity):',
    '    events = []',
    '    for num, start, end in trips:',
    '        events.append((start, num))',
    '        events.append((end, -num))',
    '        ',
    '    events.sort(key=lambda x: (x[0], x[1]))',
    '    ',
    '    curr_cap = 0',
    '    for time, change in events:',
    '        curr_cap += change',
    '        if curr_cap > capacity:',
    '            return False',
    '            ',
    '    return True'
  ],
  parse(str) {
    const parts = str.split('|');
    const trips = parts[0].split(';').map(t => t.split(',').map(Number));
    const capacity = parseInt(parts[1]);
    return { trips, capacity };
  },
  run({ trips, capacity }) {
    const { F, snap } = avRecorder();
    let events = [];
    for (const [num, start, end] of trips) {
       events.push({time: start, diff: num, type: 'pickup'});
       events.push({time: end, diff: -num, type: 'dropoff'});
    }
    events.sort((a,b) => a.time === b.time ? a.diff - b.diff : a.time - b.time);
    
    let curr_cap = 0;
    const s = { events, capacity, curr_cap, i: null };
    snap(6, 'Create events for pickup (+passengers) and dropoff (-passengers). Sort by time.', s);
    
    for (let i = 0; i < events.length; i++) {
       s.i = i;
       curr_cap += events[i].diff;
       s.curr_cap = curr_cap;
       
       if (curr_cap > capacity) {
          snap(12, `Time ${events[i].time}: ${events[i].diff > 0 ? 'Pick up' : 'Drop off'} ${Math.abs(events[i].diff)}. Current load = ${curr_cap}. EXCEEDS capacity ${capacity}! Return False.`, s);
          return F;
       }
       
       snap(10, `Time ${events[i].time}: ${events[i].diff > 0 ? 'Pick up' : 'Drop off'} ${Math.abs(events[i].diff)}. Current load = ${curr_cap}.`, s);
    }
    
    s.i = null;
    snap(14, 'Successfully completed all trips within capacity. Return True.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>Max Capacity: <span style="font-weight:bold; color:var(--text);">${state.capacity}</span></div>
        <div>Current Load: <span style="font-weight:bold; color:${state.curr_cap > state.capacity ? '#ef4444' : 'var(--accent)'};">${state.curr_cap}</span></div>
    </div>`;
    
    html += '<div style="display:flex; gap:10px; overflow-x:auto;">';
    for (let i=0; i<state.events.length; i++) {
       const ev = state.events[i];
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = ev.type === 'pickup' ? 'rgba(239,68,68,0.1)' : 'rgba(52,211,153,0.1)';
       if (isCurr) bg = 'rgba(56,189,248,0.2)';
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; min-width:60px; padding:5px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-family:var(--mono); font-size:12px;">T=${ev.time}</div>
          <div style="font-weight:bold; font-size:18px; color:${ev.diff>0?'#ef4444':'#34d399'};">${ev.diff > 0 ? '+'+ev.diff : ev.diff}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'My Calendar I', short: 'My Calendar I',
  idea: 'We need to book events without double booking. Keep a list of valid bookings. For a new booking `[start, end]`, check if it overlaps any existing booking. Overlap condition: `new_start < existing_end` AND `new_end > existing_start`.',
  complexity: 'Time O(N) per book · Space O(N)',
  input: '10,20; 15,25; 20,30', hint: 'comma-separated pairs, separated by ;',
  code: [
    'class MyCalendar:',
    '    def __init__(self):',
    '        self.calendar = []',
    '        ',
    '    def book(self, start, end):',
    '        for s, e in self.calendar:',
    '            if start < e and end > s:',
    '                return False',
    '        self.calendar.append((start, end))',
    '        return True'
  ],
  parse(str) {
    const books = str.split(';').map(s => s.split(',').map(Number));
    return { books };
  },
  run({ books }) {
    const { F, snap } = avRecorder();
    let calendar = [];
    const s = { books, calendar: [...calendar], curBook: null, checkIdx: null, status: null };
    
    snap(2, 'Initialize empty calendar.', s);
    
    for (const [start, end] of books) {
       s.curBook = [start, end];
       s.checkIdx = null; s.status = 'checking';
       snap(6, `Try to book [${start}, ${end}].`, s);
       
       let overlap = false;
       for (let i = 0; i < calendar.length; i++) {
          s.checkIdx = i;
          const [s2, e2] = calendar[i];
          if (start < e2 && end > s2) {
             overlap = true;
             s.status = 'failed';
             snap(7, `Overlap detected with [${s2}, ${e2}]! (${start} < ${e2} and ${end} > ${s2}). Booking failed.`, s);
             break;
          }
       }
       
       if (!overlap) {
          calendar.push([start, end]);
          s.calendar = JSON.parse(JSON.stringify(calendar));
          s.status = 'success';
          snap(9, `No overlaps found. Successfully booked [${start}, ${end}].`, s);
       }
    }
    
    s.curBook = null; s.checkIdx = null; s.status = null;
    snap(10, 'Finished processing all booking requests.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    
    if (state.curBook) {
       let color = state.status === 'success' ? '#34d399' : (state.status === 'failed' ? '#ef4444' : 'var(--accent)');
       html += `<div>Processing: <span style="font-weight:bold; color:${color};">[${state.curBook[0]}, ${state.curBook[1]}] - ${state.status.toUpperCase()}</span></div>`;
    }
    
    const maxVal = Math.max(...state.calendar.map(x=>x[1]), state.curBook ? state.curBook[1] : 20, 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Calendar:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.calendar.length; j++) {
       const [start, end] = state.calendar[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = 'rgba(52,211,153,0.8)';
       let border = state.checkIdx === j ? '2px solid #ef4444' : '1px solid var(--border)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:${border};">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'My Calendar II', short: 'My Calendar II',
  idea: 'Allows double bookings, but NO triple bookings. Keep a list of `calendar` (single bookings) and `overlaps` (double bookings). For a new booking, check if it overlaps any in `overlaps` (if so, return False). Then find overlaps with `calendar` and add them to `overlaps`. Add booking to `calendar`.',
  complexity: 'Time O(N) per book · Space O(N)',
  input: '10,20; 50,60; 10,40; 5,15; 5,10; 25,55', hint: 'comma-separated pairs, separated by ;',
  code: [
    'class MyCalendarTwo:',
    '    def __init__(self):',
    '        self.calendar = []',
    '        self.overlaps = []',
    '        ',
    '    def book(self, start, end):',
    '        for s, e in self.overlaps:',
    '            if start < e and end > s:',
    '                return False',
    '                ',
    '        for s, e in self.calendar:',
    '            if start < e and end > s:',
    '                self.overlaps.append((max(start, s), min(end, e)))',
    '                ',
    '        self.calendar.append((start, end))',
    '        return True'
  ],
  parse(str) {
    const books = str.split(';').map(s => s.split(',').map(Number));
    return { books };
  },
  run({ books }) {
    const { F, snap } = avRecorder();
    let calendar = [];
    let overlaps = [];
    const s = { books, calendar: [...calendar], overlaps: [...overlaps], curBook: null, status: null };
    
    snap(3, 'Initialize calendar (single bookings) and overlaps (double bookings).', s);
    
    for (const [start, end] of books) {
       s.curBook = [start, end];
       s.status = 'checking';
       snap(6, `Try to book [${start}, ${end}]. First check against double bookings (overlaps array).`, s);
       
       let tripleOverlap = false;
       for (const [s2, e2] of overlaps) {
          if (start < e2 && end > s2) {
             tripleOverlap = true;
             s.status = 'failed';
             snap(8, `Overlap detected with double booking [${s2}, ${e2}]! TRIPLE BOOKING ATTEMPT! Failed.`, s);
             break;
          }
       }
       
       if (tripleOverlap) continue;
       
       snap(11, `No triple bookings. Now find any overlaps with existing single bookings and add them to double bookings array.`, s);
       for (const [s2, e2] of calendar) {
          if (start < e2 && end > s2) {
             const overlapStart = Math.max(start, s2);
             const overlapEnd = Math.min(end, e2);
             overlaps.push([overlapStart, overlapEnd]);
             s.overlaps = JSON.parse(JSON.stringify(overlaps));
             snap(13, `Overlaps with single booking [${s2}, ${e2}]. Created double booking [${overlapStart}, ${overlapEnd}].`, s);
          }
       }
       
       calendar.push([start, end]);
       s.calendar = JSON.parse(JSON.stringify(calendar));
       s.status = 'success';
       snap(15, `Added [${start}, ${end}] to single bookings. Booking successful.`, s);
    }
    
    s.curBook = null; s.status = null;
    snap(17, 'Finished processing all booking requests.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    
    if (state.curBook) {
       let color = state.status === 'success' ? '#34d399' : (state.status === 'failed' ? '#ef4444' : 'var(--accent)');
       html += `<div>Processing: <span style="font-weight:bold; color:${color};">[${state.curBook[0]}, ${state.curBook[1]}] - ${state.status.toUpperCase()}</span></div>`;
    }
    
    const maxVal = Math.max(...state.calendar.map(x=>x[1]), ...state.overlaps.map(x=>x[1]), state.curBook ? state.curBook[1] : 60, 60);
    
    const renderList = (title, list, color) => {
       let out = `<div><div style="margin-bottom:5px; color:var(--text-dim);">${title} (${list.length}):</div><div style="display:flex; flex-direction:column; gap:4px;">`;
       if (list.length === 0) out += `<div style="font-size:12px; color:var(--text-dim);">Empty</div>`;
       for (let j=0; j<list.length; j++) {
          const [start, end] = list[j];
          const w = ((end - start) / maxVal) * 100;
          const left = (start / maxVal) * 100;
          out += `<div style="position:relative; width:100%; height:16px; background:var(--surface); border:1px solid var(--border);">
             <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:bold; color:#000;">[${start},${end}]</div>
          </div>`;
       }
       out += '</div></div>';
       return out;
    };
    
    html += renderList('Single Bookings (Calendar)', state.calendar, 'rgba(52,211,153,0.8)');
    html += renderList('Double Bookings (Overlaps)', state.overlaps, 'rgba(239,68,68,0.8)');
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 19 chunk 3.")
