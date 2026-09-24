import sys

content = """
defineAlgo('19_intervals', {
  title: 'Meeting Rooms II', short: 'Meeting Rooms II',
  idea: 'Extract start and end times separately and sort them. Use two pointers. If `start[i] < end[j]`, a room is occupied, so increment rooms. Else, a room freed up, so move both pointers.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '0,30; 5,10; 15,20', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def minMeetingRooms(intervals):',
    '    starts = sorted([i[0] for i in intervals])',
    '    ends = sorted([i[1] for i in intervals])',
    '    ',
    '    res, count = 0, 0',
    '    s, e = 0, 0',
    '    ',
    '    while s < len(intervals):',
    '        if starts[s] < ends[e]:',
    '            count += 1',
    '            s += 1',
    '        else:',
    '            count -= 1',
    '            e += 1',
    '        res = max(res, count)',
    '        ',
    '    return res'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    const starts = intervals.map(i => i[0]).sort((a,b)=>a-b);
    const ends = intervals.map(i => i[1]).sort((a,b)=>a-b);
    
    let res = 0, count = 0;
    let s_ptr = 0, e_ptr = 0;
    const s = { starts, ends, s_ptr, e_ptr, res, count };
    
    snap(3, 'Extract and sort start and end times separately.', s);
    
    while (s_ptr < starts.length) {
       if (starts[s_ptr] < ends[e_ptr]) {
          count++;
          res = Math.max(res, count);
          s.count = count; s.res = res;
          snap(9, `starts[${s_ptr}] (${starts[s_ptr]}) < ends[${e_ptr}] (${ends[e_ptr]}). A new meeting started before the earliest end time. Rooms active: ${count}. Max: ${res}`, s);
          s_ptr++;
          s.s_ptr = s_ptr;
       } else {
          count--;
          s.count = count;
          snap(12, `starts[${s_ptr}] (${starts[s_ptr]}) >= ends[${e_ptr}] (${ends[e_ptr]}). A meeting ended. Rooms active: ${count}.`, s);
          e_ptr++;
          s.e_ptr = e_ptr;
       }
    }
    
    snap(16, `All meetings processed. Max rooms required = ${res}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px; font-size:14px;">
        <div>Active Rooms: <span style="font-weight:bold; color:var(--text);">${state.count}</span></div>
        <div>Max Rooms (Ans): <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px; color:var(--text-dim);">Starts:</div>';
    for(let i=0; i<state.starts.length; i++) {
       let border = i === state.s_ptr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = i < state.s_ptr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.starts[i]}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px; color:var(--text-dim);">Ends:</div>';
    for(let i=0; i<state.ends.length; i++) {
       let border = i === state.e_ptr ? '2px solid #ef4444' : '1px solid var(--border)';
       let bg = i < state.e_ptr ? 'rgba(239,68,68,0.2)' : 'var(--surface)';
       html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.ends[i]}</div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Interval List Intersections', short: 'Intersections',
  idea: 'Two pointers over two sorted lists. The intersection is `[max(start1, start2), min(end1, end2)]`. Add if valid. Move the pointer of the interval that ends earlier.',
  complexity: 'Time O(M + N) · Space O(M + N)',
  input: '0,2; 5,10; 13,23| 1,5; 8,12; 15,24; 25,26', hint: 'list1 | list2',
  code: [
    'def intervalIntersection(firstList, secondList):',
    '    res = []',
    '    i, j = 0, 0',
    '    ',
    '    while i < len(firstList) and j < len(secondList):',
    '        s = max(firstList[i][0], secondList[j][0])',
    '        e = min(firstList[i][1], secondList[j][1])',
    '        ',
    '        if s <= e:',
    '            res.append([s, e])',
    '            ',
    '        if firstList[i][1] < secondList[j][1]:',
    '            i += 1',
    '        else:',
    '            j += 1',
    '            ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const firstList = parts[0].split(';').map(s => s.split(',').map(Number));
    const secondList = parts[1].split(';').map(s => s.split(',').map(Number));
    return { firstList, secondList };
  },
  run({ firstList, secondList }) {
    const { F, snap } = avRecorder();
    let res = [], i = 0, j = 0;
    const s = { firstList, secondList, res: [...res], i, j };
    
    snap(3, 'Start two pointers at 0.', s);
    
    while (i < firstList.length && j < secondList.length) {
       const [s1, e1] = firstList[i];
       const [s2, e2] = secondList[j];
       
       const start = Math.max(s1, s2);
       const end = Math.min(e1, e2);
       
       if (start <= end) {
          res.push([start, end]);
          s.res = JSON.parse(JSON.stringify(res));
          snap(10, `Intersection found between [${s1},${e1}] and [${s2},${e2}]: [${start},${end}]`, s);
       } else {
          snap(9, `No overlap between [${s1},${e1}] and [${s2},${e2}].`, s);
       }
       
       if (e1 < e2) {
          snap(13, `List1 ends earlier (${e1} < ${e2}). Move pointer i.`, s);
          i++;
          s.i = i;
       } else {
          snap(15, `List2 ends earlier or equal (${e2} <= ${e1}). Move pointer j.`, s);
          j++;
          s.j = j;
       }
    }
    
    snap(17, 'Done checking intersections.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.firstList.map(x=>x[1]), ...state.secondList.map(x=>x[1]), 20);
    
    const renderRow = (title, list, ptr, color) => {
       let out = `<div style="display:flex; gap:10px; align-items:center;"><div style="width:60px;">${title}</div>`;
       out += `<div style="position:relative; width:calc(100% - 70px); height:20px; background:var(--surface); border:1px solid var(--border);">`;
       for (let k=0; k<list.length; k++) {
          const [start, end] = list[k];
          const w = ((end - start) / maxVal) * 100;
          const left = (start / maxVal) * 100;
          let bg = k === ptr ? color : 'rgba(100,100,100,0.5)';
          let brd = k === ptr ? `1px solid ${color}` : 'none';
          out += `<div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${bg}; border:${brd}; border-radius:4px;"></div>`;
       }
       out += `</div></div>`;
       return out;
    };
    
    html += renderRow('List 1', state.firstList, state.i, 'rgba(56,189,248,0.8)');
    html += renderRow('List 2', state.secondList, state.j, 'rgba(239,68,68,0.8)');
    
    html += `<div style="margin-top:10px; font-weight:bold; color:var(--accent);">Intersections: [${state.res.map(x=>`[${x}]`).join(', ')}]</div>`;
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Min Number of Arrows to Burst Balloons', short: 'Burst Balloons',
  idea: 'Greedy. Sort by END coordinate. If the next balloon starts after the current arrow position (`prev_end`), shoot a new arrow at its end.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '10,16; 2,8; 1,6; 7,12', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def findMinArrowShots(points):',
    '    points.sort(key=lambda x: x[1])',
    '    arrows = 1',
    '    prev_end = points[0][1]',
    '    ',
    '    for i in range(1, len(points)):',
    '        start, end = points[i]',
    '        if start > prev_end:',
    '            arrows += 1',
    '            prev_end = end',
    '            ',
    '    return arrows'
  ],
  parse(str) {
    const points = str.split(';').map(s => s.split(',').map(Number));
    return { points };
  },
  run({ points }) {
    const { F, snap } = avRecorder();
    points.sort((a,b) => a[1] - b[1]);
    let arrows = 1;
    let prev_end = points[0][1];
    
    const s = { points: JSON.parse(JSON.stringify(points)), arrows, prev_end, i: null };
    snap(4, `Sort balloons by END time. Shoot first arrow at ${prev_end}.`, s);
    
    for (let i = 1; i < points.length; i++) {
       s.i = i;
       const [start, end] = points[i];
       if (start > prev_end) {
          arrows++;
          prev_end = end;
          s.arrows = arrows; s.prev_end = prev_end;
          snap(9, `Balloon ${i} [${start}, ${end}] starts AFTER arrow at ${s.prev_end}. Need new arrow at ${end}. Total = ${arrows}.`, s);
       } else {
          snap(7, `Balloon ${i} [${start}, ${end}] overlaps with arrow at ${prev_end}. Burst it with the same arrow!`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished. Min arrows required = ${arrows}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:14px;">Arrows Used: <span style="font-weight:bold; color:var(--accent);">${state.arrows}</span> | Current Arrow Pos: <span style="font-weight:bold; color:#ef4444;">${state.prev_end}</span></div>`;
    
    const maxVal = Math.max(...state.points.map(x=>x[1]), 20);
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    
    for (let j=0; j<state.points.length; j++) {
       const [start, end] = state.points[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = 'rgba(100,100,100,0.5)';
       if (state.i === j) color = 'rgba(56,189,248,0.8)';
       else if (j < (state.i || state.points.length)) color = 'rgba(52,211,153,0.5)'; // Burst
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:10px;"></div>
       </div>`;
    }
    
    // Draw arrow line
    if (state.prev_end !== null) {
       const arrowLeft = (state.prev_end / maxVal) * 100;
       html += `<div style="position:absolute; left:${arrowLeft}%; top:0; width:2px; height:100%; background:#ef4444; z-index:10;"></div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px; position:relative;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Employee Free Time', short: 'Free Time',
  idea: 'Flatten all schedules and sort by start time. Keep track of the `max_end` seen so far. If a new interval starts strictly after `max_end`, the gap is a common free time!',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,2; 5,6| 1,3| 4,10', hint: 'schedules separated by |',
  code: [
    'def employeeFreeTime(schedule):',
    '    intervals = []',
    '    for emp in schedule:',
    '        intervals.extend(emp)',
    '    intervals.sort(key=lambda x: x[0])',
    '    ',
    '    res = []',
    '    max_end = intervals[0][1]',
    '    ',
    '    for i in range(1, len(intervals)):',
    '        start, end = intervals[i]',
    '        if start > max_end:',
    '            res.append([max_end, start])',
    '        max_end = max(max_end, end)',
    '        ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const schedule = parts.map(p => p.split(';').map(s => s.split(',').map(Number)));
    return { schedule };
  },
  run({ schedule }) {
    const { F, snap } = avRecorder();
    let intervals = [];
    for (const emp of schedule) intervals.push(...emp);
    intervals.sort((a,b) => a[0] - b[0]);
    
    let res = [];
    let max_end = intervals[0][1];
    
    const s = { intervals, res: [...res], max_end, i: null };
    snap(7, `Flatten and sort all intervals. Initial max_end = ${max_end}.`, s);
    
    for (let i = 1; i < intervals.length; i++) {
       s.i = i;
       const [start, end] = intervals[i];
       
       if (start > max_end) {
          res.push([max_end, start]);
          s.res = JSON.parse(JSON.stringify(res));
          snap(12, `Interval ${i} [${start}, ${end}] starts AFTER max_end ${max_end}. We found a GAP! Added [${max_end}, ${start}] to free time.`, s);
       } else {
          snap(10, `Interval ${i} [${start}, ${end}] overlaps with max_end ${max_end}. No gap.`, s);
       }
       
       max_end = Math.max(max_end, end);
       s.max_end = max_end;
       snap(13, `Update max_end = max(old, ${end}) = ${max_end}.`, s);
    }
    
    s.i = null;
    snap(15, `Done. Free times: [${res.map(x=>`[${x}]`).join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:14px;">
        Max End Horizon: <span style="font-weight:bold; color:#ef4444;">${state.max_end}</span> | 
        Free Time: <span style="font-weight:bold; color:var(--accent);">[${state.res.map(x=>`[${x}]`).join(', ')}]</span>
    </div>`;
    
    const maxVal = Math.max(...state.intervals.map(x=>x[1]), 20);
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono); position:relative;">';
    
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px;"></div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending Topic 19 chunk 2.")
