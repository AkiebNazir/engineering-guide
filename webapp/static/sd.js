/* ============================================================================
   System Design pages — animated labs placed next to the text they explain,
   and a 45-minute Google L5 interview coach on every practice problem.

   Labs come from viz-sd*.js. SD_LABS says which labs go on which page and,
   optionally, which heading they follow. On practice problems, labs only
   appear inside the reference design, so they never spoil the question.
   ========================================================================= */
'use strict';

/* page id → [lab, options?, heading pattern?] */
const SD_LABS = {
  'building_blocks/00_overview': [['sd-request', /request path/i]],
  'building_blocks/02_networking': [['sd-request', /latency budget/i]],
  'building_blocks/03_api_design_high_level': [['sd-realtime', /choosing an api style/i], ['sd-idempotency', /idempotency/i]],
  'building_blocks/04_api_design_low_level': [['sd-ratelimit', /rate limiting/i]],
  'building_blocks/05_databases': [['sd-replication', /replica/i]],
  'building_blocks/06_database_internals': [['sd-lsm', /storage engine/i], ['sd-shard', /partitioning/i], ['sd-quorum', /replication modes/i], ['sd-raft', /consensus/i], ['flow-wal', /write-ahead log/i]],
  'building_blocks/07_caching': [['sd-cache', /stampede/i], ['flow-cache-aside', /cache-aside, write-through/i]],
  'building_blocks/09_messaging_and_streaming': [['sd-kafka', /ordering scope|visibility/i], ['flow-outbox', /transactional outbox/i]],
  'building_blocks/10_distributed_systems_theory': [['sd-quorum', /consistency models|cap theorem/i], ['sd-collab', /conflict resolution/i], ['sd-snowflake', /unique ids/i]],
  'building_blocks/11_transactions_and_concurrency': [['sd-saga', /saga/i]],
  'building_blocks/12_application_resilience_patterns': [['sd-retry', /circuit breaker|retry/i]],
  'building_blocks/13_scaling_and_load_balancing': [['sd-lb', /load balancing algorithms/i], ['sd-ring', /load balancing algorithms/i], ['sd-autoscale', /scale-out lag|autoscale/i]],
  'building_blocks/15_observability_and_reliability': [['sd-tail', /slo|golden signals|four signal/i]],
  'building_blocks/17_decision_framework': [['sd-estimate', /decision worksheet/i]],
  'building_blocks/18_back_of_envelope_estimation': [['sd-estimate', /worked|calculator|method/i], ['sd-tail', /latency numbers/i]],
  'building_blocks/19_consensus_and_coordination': [['sd-raft', /raft/i], ['sd-quorum', /quorum/i], ['sd-snowflake', /clocks|time/i]],
  'building_blocks/20_specialized_data_structures': [['sd-sketch', /bloom/i], ['sd-sketch', { mode: 'cms' }, /count-min/i], ['sd-geo', /geospatial|geohash/i], ['sd-lsm', /lsm|sstable/i]],
  'building_blocks/21_batch_and_stream_processing': [['sd-windows', /window/i], ['sd-kafka', /log|kappa/i]],
  'building_blocks/22_realtime_and_collaboration': [['sd-realtime', /transport|websocket/i], ['sd-collab', /operational|crdt/i]],
  'building_blocks/23_ml_and_llm_systems': [['sd-tail', /retrieval|candidate/i], ['sd-autoscale', /llm serving|model serving/i]],
  'building_blocks/25_partitioning_and_hot_keys': [['sd-shard', /hot key|shard key/i], ['sd-ring', /rebalanc|consistent/i]],
  'building_blocks/26_distributed_log_internals': [['sd-quorum', /replication/i], ['sd-kafka', /consumer groups/i], ['flow-kafka-isr', /isr, high watermark/i]],
  'building_blocks/27_multi_region_and_global_traffic': [['sd-request', /traffic steering/i], ['sd-replication', /data replication/i]],
  'building_blocks/28_overload_control_and_graceful_degradation': [['sd-retry', /retry budgets/i], ['sd-tail', /hedged requests/i], ['sd-autoscale', /after the storm/i]],
  'building_blocks/29_cdn_and_streaming_media': [['sd-cache', /what a cdn is/i], ['flow-cdn', /what a cdn is/i]],
  'building_blocks/31_ranking_recommendation_and_experimentation': [['sd-tail', /the cascade/i]],
  '00_google_l5_playbook': [['sd-estimate', /estimat/i]],
  guide: [['sd-request', /mental model/i], ['sd-snowflake', /url shortener/i], ['sd-fanout', /news feed/i], ['sd-ratelimit', /rate limiting/i], ['sd-ring', /partitioning/i]],
  'problem/001_url_shortener': [['sd-flow-shortener', /baseline architecture|flows/i], ['sd-snowflake', /code generation/i], ['sd-cache', /cache trade/i]],
  'problem/002_rate_limiter': [['sd-ratelimit', /algorithm/i], ['sd-flow-ratelimiter', /architecture and policy/i]],
  'problem/003_pastebin': [['sd-flow-pastebin', /architecture/i]],
  'problem/004_notification_platform': [['sd-flow-notifications', /data and architecture/i], ['sd-kafka', /queue|data|architecture/i], ['sd-retry', /failure|retry|provider/i]],
  'problem/005_photo_pipeline': [['sd-flow-photopipeline', /source of truth and flow/i]],
  'problem/006_chat': [['sd-flow-chat', /architecture and data/i], ['sd-realtime', /architecture|connection/i]],
  'problem/007_news_feed': [['sd-flow-newsfeed', /architecture and data flow/i], ['sd-fanout', /fanout/i]],
  'problem/008_checkout': [['sd-flow-checkout', /architecture and flow/i], ['sd-saga', /saga|payment|order/i], ['sd-idempotency', /idempot/i]],
  'problem/009_search_and_autocomplete': [['sd-flow-search', /data ownership/i], ['sd-tail', /serving|query|latency/i]],
  'problem/010_seat_reservation': [['sd-flow-seats', /architecture and flow/i]],
  'problem/011_web_crawler': [['sd-flow-crawler', /architecture and flow/i], ['sd-sketch', /dedup|frontier|seen/i]],
  'problem/012_workflow_scheduler': [['sd-flow-scheduler', /architecture and flow/i], ['sd-raft', /leader|lease|scheduler/i]],
  'problem/013_metrics_platform': [['sd-flow-metrics', /architecture and flow/i], ['sd-windows', /aggregat|rollup|ingest/i]],
  'problem/014_logging_platform': [['sd-flow-logging', /architecture and flow/i], ['sd-kafka', /ingest|pipeline|architecture/i]],
  'problem/015_drive': [['sd-flow-drive', /architecture and data flow/i]],
  'problem/016_video_on_demand': [['sd-flow-vod', /architecture and data flow/i]],
  'problem/017_payment_ledger': [['sd-flow-ledger', /architecture and data flow/i], ['sd-idempotency', /idempot|api/i], ['sd-saga', /provider|settle|external/i]],
  'problem/018_distributed_cache': [['sd-flow-cache', /architecture and data flow/i], ['sd-ring', /partition|shard|hash/i], ['sd-cache', /stampede|hot|eviction/i]],
  'problem/019_feature_flags': [['sd-flow-flags', /architecture and data flow/i]],
  'problem/020_ride_dispatch': [['sd-flow-ride', /architecture and data flow/i], ['sd-geo', /location|match|geo/i]],
  'problem/021_multi_tenant_api_gateway': [['sd-flow-gateway', /architecture and data flow/i], ['sd-ratelimit', /quota|rate|limit/i], ['sd-lb', /routing|balanc/i]],
  'problem/022_unique_id_generator': [['sd-snowflake', /snowflake|layout/i], ['sd-flow-snowflake', /^architecture$/i]],
  'problem/023_distributed_key_value_store': [['sd-flow-dynamo', /partitioning with consistent hashing/i], ['sd-ring', /partition|consistent/i], ['sd-quorum', /replication|quorum/i]],
  'problem/024_collaborative_document_editor': [['sd-flow-editor', /session servers and connections/i], ['sd-collab', /concurrency|crdt/i], ['sd-realtime', /session servers|connection/i]],
  'problem/025_web_search_engine': [['sd-flow-searchengine', /query serving and fan-out/i], ['sd-tail', /serving|fan-out|query/i], ['sd-sketch', /crawl|dedup/i]],
  'problem/026_nearby_places': [['sd-flow-places', /architecture and flows/i], ['sd-geo', /index|geo/i]],
  'problem/027_ad_click_aggregation': [['sd-flow-adclick', /^architecture$/i], ['sd-windows', /window|stream/i], ['sd-idempotency', /exactly|dedup/i]],
  'problem/028_top_k_trending': [['sd-flow-trending', /^architecture$/i], ['sd-sketch', { mode: 'cms' }, /sketch|count/i], ['sd-windows', /window/i]],
  'problem/029_realtime_leaderboard': [['sd-flow-leaderboard', /write path and durability/i], ['sd-shard', /shard|partition|scale/i]],
  'problem/030_llm_assistant_feature': [['sd-flow-llm', /^architecture$/i], ['sd-ratelimit', /quota|rate|limit/i], ['sd-autoscale', /capacity|serving|gpu/i]],
};

function enhanceSystemDesign(host, prose, item, key) {
  prose.classList.add('sd-doc');
  if (item.kind === 'problem') buildCoach(host, prose, key);
  const labs = mountSdLabs(prose, item);
  if (labs) $('.doc-meta', host)?.insertAdjacentHTML('beforeend', `<span class="doc-labs">${labs} animated lab${labs > 1 ? 's' : ''}</span>`);
  return { afterRender: async () => {} };
}

function mountSdLabs(prose, item) {
  const plan = SD_LABS[item.id];
  if (!plan || typeof createLab !== 'function') return 0;
  let secs = $$('.sec', prose);
  if (item.kind === 'problem') {
    const divider = $('.sol-divider', prose);
    if (!divider) return 0;
    const at = secs.indexOf(divider.closest('.sec'));
    secs = secs.slice(at + 1);
  }
  const heads = secs.flatMap(sec => [$(':scope > h2', sec), ...$$(':scope > h3', sec)].filter(Boolean));
  const usedSpot = new Map();
  let count = 0;
  plan.forEach(entry => {
    const [name, ...rest] = entry;
    const opts = rest.find(x => x && typeof x === 'object' && !(x instanceof RegExp)) || {};
    const re = rest.find(x => x instanceof RegExp);
    const fig = createLab(name, opts);
    if (!fig) return;
    const h = (re && heads.find(x => re.test(x.dataset.label || x.textContent))) || null;
    let anchor;
    if (h && h.tagName === 'H3') {
      let n = h.nextElementSibling;
      while (n && !/^(H2|H3)$/.test(n.tagName) && !n.classList.contains('sec-foot')) n = n.nextElementSibling;
      anchor = n;
      if (!anchor) { h.parentElement.append(fig); count++; return; }
    } else {
      const sec = h ? h.closest('.sec') : secs.find(x => !x.classList.contains('sec-intro')) || secs[0];
      if (!sec) return;
      anchor = $(':scope > .sec-foot', sec);
      if (!anchor) { sec.append(fig); count++; return; }
    }
    const prev = usedSpot.get(anchor);
    (prev || anchor).before(fig);
    usedSpot.set(anchor, anchor);
    count++;
  });
  return count;
}

/* ---------------------------------------------------- the L5 interview coach -- */
const COACH_PHASES = [
  {
    name: 'Requirements', from: 0, to: 5,
    goal: 'Agree on what you are building and how big it is, before drawing anything.',
    checks: ['3–5 core features, and what is explicitly out of scope', 'Who the users are and the scale: DAU, read:write ratio, growth', 'Latency target, and availability vs consistency for each flow', 'Durability, retention, privacy or compliance constraints'],
    l5: 'You propose the requirements and ask the interviewer to confirm them. You do not wait to be told what matters.',
  },
  {
    name: 'Estimates & API', from: 5, to: 10,
    goal: 'Put numbers on the problem, and say which number will shape the design.',
    checks: ['Average and peak QPS for the main reads and writes', 'Storage per year, including replication', 'Bandwidth, if media is involved', 'The 3–5 main API endpoints with request and response shapes', 'Name the number that forces a decision (e.g. “peak writes rule out one primary”)'],
    l5: 'Every estimate is followed by “so we need…”. Numbers without a consequence are just arithmetic.',
  },
  {
    name: 'Data model', from: 10, to: 15,
    goal: 'Choose storage from the access patterns, not from habit.',
    checks: ['Core entities, their keys and relationships', 'The top access patterns, including the hot path', 'Database choice, and the alternative you rejected and why', 'A first partition/shard key and the indexes you need'],
    l5: 'You explain the rejected option too: “a relational store would give us X, but this access pattern needs Y”.',
  },
  {
    name: 'High-level design', from: 15, to: 25,
    goal: 'Draw a baseline that works, then walk real requests through it.',
    checks: ['Clients, load balancer or gateway, services, storage, cache, queues', 'Walk one write end to end', 'Walk one read end to end', 'Say where the source of truth is and what is derived'],
    l5: 'Start simple. Add each component only when a requirement or number from earlier justifies it.',
  },
  {
    name: 'Deep dives', from: 25, to: 38,
    goal: 'Go deep on the two hardest parts, compare alternatives, and commit.',
    checks: ['Pick the two hardest problems (see suggestions below)', 'For each, compare at least two approaches', 'Make an explicit decision with a trade-off sentence', 'Quantify: use your estimates to justify the choice'],
    l5: '“I’ll use X. We give up A, which is acceptable because B.” Committing to a decision matters more than listing every option.',
  },
  {
    name: 'Failure & evolution', from: 38, to: 45,
    goal: 'Show you have operated systems: what breaks, how you would notice, what changes at 10×.',
    checks: ['What happens when the cache, a shard, or a whole region fails', 'Bottlenecks and hot spots as traffic grows', 'SLIs/SLOs and the alerts you would page on', 'What you would change at 10× scale or multi-region'],
    l5: 'Raise failure modes before you are asked. That is one of the clearest seniority signals.',
  },
];

function buildCoach(host, prose, key) {
  const task = $$('h2', prose).find(h => /your task/i.test(h.dataset.label || h.textContent));
  const taskItems = task ? $$('li', task.closest('.sec')).map(li => li.textContent.replace(/\s+/g, ' ').trim()) : [];
  const deep = taskItems.filter(t => !/clarifying|back-of-envelope|estimate|api contract|baseline architecture|trade-off you would revisit/i.test(t)).slice(0, 3);
  const st = () => ({ phase: 0, checks: {}, notes: {}, elapsed: 0, ...(docRec(key).coach || {}) });
  const save = patch => docSave(key, { coach: { ...st(), ...patch } });

  const card = document.createElement('section');
  card.className = 'coach';
  card.innerHTML = `
    <div class="coach-head">
      <div class="coach-titles">
        <p class="coach-kicker">Google L5 mock round</p>
        <h3 class="coach-title">Run it like the real thing: 45 minutes, six phases</h3>
      </div>
      <div class="coach-clock" data-state="idle">
        <b class="coach-time">45:00</b>
        <button type="button" class="btn-mod" data-coach="toggle">Start the clock</button>
        <button type="button" class="btn-mod ghost" data-coach="reset">Reset</button>
      </div>
    </div>
    <ol class="coach-track">${COACH_PHASES.map((p, i) => `
      <li data-i="${i}"><button type="button" data-coach="phase" data-i="${i}">
        <span class="ct-bar"><i></i></span>
        <span class="ct-time">${p.from}–${p.to} min</span><span class="ct-name">${p.name}</span>
      </button></li>`).join('')}</ol>
    <div class="coach-body"></div>`;
  const firstSec = $('.sec:not(.sec-intro)', prose) || prose.firstElementChild;
  firstSec ? firstSec.before(card) : prose.append(card);

  let timer = null;
  const body = $('.coach-body', card);
  const paint = () => {
    const s = st(), p = COACH_PHASES[s.phase], mins = s.elapsed / 60;
    const done = s.checks[s.phase] || [];
    body.innerHTML = `
      <p class="coach-goal"><b>${p.name}.</b> ${p.goal}</p>
      <ul class="coach-checks">${p.checks.map((c, i) => `<li class="${done.includes(i) ? 'is-done' : ''}"><button type="button" class="cc-box" data-coach="check" data-i="${i}" aria-pressed="${done.includes(i)}"><svg viewBox="0 0 24 24">${CHECK_PATH}</svg></button><span>${esc(c)}</span></li>`).join('')}</ul>
      ${s.phase === 4 && deep.length ? `<div class="coach-deep"><p>Deep-dive candidates for this problem</p><ul>${deep.map(d => `<li>${esc(d)}</li>`).join('')}</ul></div>` : ''}
      <p class="coach-l5"><span>What reads as L5</span>${p.l5}</p>
      <textarea class="coach-notes" data-i="${s.phase}" rows="4" placeholder="Write what you would say in this phase…">${esc(s.notes[s.phase] || '')}</textarea>
      <div class="coach-nav">
        <button type="button" class="btn-mod ghost" data-coach="prev" ${s.phase === 0 ? 'disabled' : ''}>← ${s.phase ? COACH_PHASES[s.phase - 1].name : ''}</button>
        ${s.phase < 5 ? `<button type="button" class="btn-mod" data-coach="next">${COACH_PHASES[s.phase + 1].name} →</button>` : `<button type="button" class="btn-mod" data-coach="finish">Finish and compare with the reference</button>`}
      </div>`;
    $$('.coach-track li', card).forEach((li, i) => {
      const ph = COACH_PHASES[i], got = (s.checks[i] || []).length;
      li.classList.toggle('is-on', i === s.phase);
      li.classList.toggle('is-done', got === ph.checks.length);
      li.classList.toggle('is-now', mins >= ph.from && mins < ph.to && s.elapsed > 0);
      $('i', li).style.width = `${clamp((mins - ph.from) / (ph.to - ph.from), 0, 1) * 100}%`;
    });
    const left = Math.max(0, 45 * 60 - s.elapsed);
    $('.coach-time', card).textContent = `${Math.floor(left / 60)}:${String(Math.floor(left % 60)).padStart(2, '0')}`;
    $('.coach-time', card).classList.toggle('is-late', mins > COACH_PHASES[s.phase].to && s.elapsed > 0);
  };
  const tick = () => {
    if (!card.isConnected) { clearInterval(timer); return; }
    const s = st();
    const elapsed = s.elapsed + 1;
    const nowPhase = COACH_PHASES.findIndex(p => elapsed / 60 >= p.from && elapsed / 60 < p.to);
    const patch = { elapsed };
    if (nowPhase > s.phase) { patch.phase = nowPhase; toast(`${COACH_PHASES[nowPhase].from} minutes: move on to ${COACH_PHASES[nowPhase].name.toLowerCase()}.`, 'warn'); }
    docRec(key).coach = { ...s, ...patch };
    if (elapsed % 15 === 0) save(patch);
    if (elapsed >= 45 * 60) { stop(); toast('45 minutes. Time to wrap up and compare with the reference design.', 'warn'); }
    paint();
  };
  const stop = () => { clearInterval(timer); timer = null; $('.coach-clock', card).dataset.state = 'paused'; $('[data-coach="toggle"]', card).textContent = 'Resume'; save({}); };
  card.addEventListener('click', e => {
    const b = e.target.closest('[data-coach]');
    if (!b) return;
    const s = st(), act = b.dataset.coach;
    if (act === 'toggle') {
      if (timer) { stop(); return; }
      timer = setInterval(tick, 1000);
      $('.coach-clock', card).dataset.state = 'running'; b.textContent = 'Pause';
    } else if (act === 'reset') { clearInterval(timer); timer = null; $('.coach-clock', card).dataset.state = 'idle'; $('[data-coach="toggle"]', card).textContent = 'Start the clock'; save({ elapsed: 0, phase: 0 }); }
    else if (act === 'phase') save({ phase: +b.dataset.i });
    else if (act === 'next') save({ phase: Math.min(5, s.phase + 1) });
    else if (act === 'prev') save({ phase: Math.max(0, s.phase - 1) });
    else if (act === 'check') {
      const i = +b.dataset.i, cur = s.checks[s.phase] || [];
      save({ checks: { ...s.checks, [s.phase]: cur.includes(i) ? cur.filter(x => x !== i) : [...cur, i] } });
    } else if (act === 'finish') {
      stop();
      const total = COACH_PHASES.reduce((a, p) => a + p.checks.length, 0), got = Object.values(s.checks).reduce((a, x) => a + x.length, 0);
      toast(`You covered ${got} of ${total} checkpoints in ${Math.round(s.elapsed / 60)} minutes.`, got >= total * .8 ? 'ok' : 'warn');
      (host.querySelector('[data-gate], .gate') || host.querySelector('[data-banner], .sol-divider'))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    paint();
  });
  let noteT;
  card.addEventListener('input', e => {
    const ta = e.target.closest('.coach-notes');
    if (!ta) return;
    clearTimeout(noteT);
    noteT = setTimeout(() => { const s = st(); save({ notes: { ...s.notes, [ta.dataset.i]: ta.value } }); }, 600);
  });
  paint();
}
