/* Live flows for the mlops module (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ============================================= feature store: offline + online == */
const LmlFs = lane([
  { label: 'SOURCES', nodes: [
    { id: 'events', label: 'Click events', sub: 'event stream', kind: 'queue', icon: 'stream', row: 0 },
    { id: 'wh', label: 'Warehouse', sub: 'raw tables', kind: 'db', icon: 'db', row: 1 }] },
  { label: 'PIPELINES', nodes: [
    { id: 'stream', label: 'Stream job', sub: '10-min windows', icon: 'workflow', row: 0 },
    { id: 'batch', label: 'Batch job', sub: 'nightly SQL', icon: 'cron', row: 1 }] },
  { label: 'FEATURE STORE', nodes: [
    { id: 'online', label: 'Online store', sub: 'latest value per key', kind: 'cache', icon: 'kv', row: 0 },
    { id: 'offline', label: 'Offline store', sub: 'history + timestamps', icon: 'table', row: 1 }] },
  { label: 'CONSUMERS', nodes: [
    { id: 'server', label: 'Model server', sub: 'one row, now', icon: 'model', row: 0 },
    { id: 'train', label: 'Training job', sub: 'as-of join', icon: 'cpu', row: 1 }] },
]);
defineFlow('flow-feature-store', {
  title: 'Live flow: one feature, two paths, point-in-time correct',
  hint: 'Build a training set with an as-of join, then watch a batch feature and a streaming feature reach the online store.',
  zones: LmlFs.zones, h: LmlFs.h, nodes: LmlFs.nodes,
  edges: [
    ['events', 'stream'], ['stream', 'online'], ['wh', 'batch'], ['batch', 'offline'],
    ['offline', 'online'], ['online', 'server'], ['offline', 'train'], ['events', 'wh'],
  ],
  scenarios: [
    {
      id: 'pit', name: 'Training set, point in time',
      summary: 'Build training rows for a churn model. For each labelled moment, every feature must take the value production <b>could have seen then</b>, never a later one.',
      steps: [
        { at: 'train', badge: 'labels: user, time', title: 'Start from labelled moments',
          detail: 'The entity dataframe lists (user_id, event_timestamp, label) rows, e.g. user 1 at 1 April 12:00, churned = 1.' },
        { path: ['train', 'offline'], label: 'entity rows + timestamps', ms: 50, title: 'Ask for features as of each row',
          detail: 'The request names feature views, not SQL. The feature store generates the join against the full history.' },
        { at: 'offline', badge: 'as-of join', title: 'Latest value strictly before each timestamp',
          detail: 'For user 1 at 1 April 12:00 it picks <code>sessions_7d = 3</code>, computed 31 March 02:00. It does <b>not</b> pick the 2 April value of 0, computed after the user churned: that would be leakage.' },
        { at: 'offline', badge: 'older than TTL → null', tone: 'warn', title: 'Too-old values count as missing',
          detail: 'With a 2-day TTL, a value from last month comes back empty, just as serving would see no recent value. Training and serving agree about "unknown".' },
        { path: ['offline', 'train'], label: 'training rows', tone: 'ok', title: 'Rows arrive, with no future data in them',
          detail: 'At scale this range join is the expensive part of building a training set; partitioning history by date keeps it bounded.' },
      ],
    },
    {
      id: 'batch', name: 'Batch feature, online read',
      summary: 'A nightly job computes <code>orders_90d</code>. The history goes to the offline store; the latest value per user is <b>materialized</b> into the online store for serving.',
      steps: [
        { path: ['wh', 'batch'], label: 'nightly SQL', title: 'Compute from the warehouse',
          detail: 'One definition of the feature, run once for every user. The ≈10 minutes is illustrative.' },
        { path: ['batch', 'offline'], label: 'append values + timestamps', title: 'History keeps every value',
          detail: 'Each row carries the time it became true, so tomorrow\'s training can still ask "what was it on the 3rd?".' },
        { path: ['offline', 'online'], label: 'materialize latest', badgeAt: 'online', badge: 'user:42 updated', title: 'Copy the latest value per key',
          detail: 'Only the newest value per user goes to the key-value store, which is sized for entities × features, not for history.' },
        { path: ['server', 'online', 'server'], label: 'GET user:42', tone: 'ok', ms: 2, title: 'A prediction reads it in milliseconds',
          detail: 'The model server fetches one row per entity, batched into one round trip, well inside its latency budget.' },
        { at: 'online', badge: 'value is 26 h old', tone: 'warn', title: 'Freshness is the price of batch',
          detail: 'If last night\'s job failed, this read silently returns older data. Emit the age of every value read and alert when it passes a threshold.' },
      ],
    },
    {
      id: 'stream', name: 'Streaming feature',
      summary: '<code>clicks_10m</code> must be fresh within seconds, so a stream job computes it. The hard part is keeping the offline history identical.',
      steps: [
        { path: ['events', 'stream'], label: 'click event', ms: 50, title: 'An event arrives',
          detail: 'The stream job is partitioned by user, so all of one user\'s clicks land on the same worker.' },
        { at: 'stream', badge: 'window count 7 → 8', title: 'Update the window',
          detail: 'Windows use <b>event time</b>, with a stated allowed lateness. "Last 10 minutes" must mean the same thing here and in any offline recomputation.' },
        { path: ['stream', 'online'], label: 'push clicks_10m = 8', title: 'Push the fresh value',
          detail: 'The value reaches the online store about a second after the click.' },
        { path: ['server', 'online', 'server'], label: 'read fresh value', tone: 'ok', ms: 2, title: 'Serving sees the click',
          detail: 'The next prediction for this user already reflects what they did a moment ago.' },
        { path: ['events', 'wh'], label: 'land raw events', async: true, title: 'Raw events also land in the warehouse',
          detail: 'Training will need this feature\'s history too.' },
        { path: ['wh', 'batch', 'offline'], label: 'recompute same window', tone: 'warn', title: 'A second implementation risks skew',
          detail: 'If the batch recomputation uses processing time or a tumbling bucket while the stream used a sliding event-time window, training and serving values differ. Fixes: have the stream job write offline too, generate both from one definition, or log served values.' },
      ],
    },
  ],
});

/* ======================================== online inference + dynamic batching == */
const LmlSv = lane([
  { label: 'CALLER', nodes: [{ id: 'app', label: 'Checkout svc', sub: 'calls /predict', kind: 'client', icon: 'app', row: 1 }] },
  { label: 'PREDICTION API', nodes: [{ id: 'api', label: 'Prediction API', sub: 'validate, assemble', icon: 'api', row: 1 }] },
  { label: 'FEATURES · LOGS', nodes: [
    { id: 'fs', label: 'Online store', sub: 'Redis multi-get', kind: 'cache', icon: 'kv', row: 0 },
    { id: 'log', label: 'Prediction log', sub: 'async, sampled', icon: 'logs', row: 2 }] },
  { label: 'MODEL SERVER', nodes: [
    { id: 'queue', label: 'Batch queue', sub: 'max wait 2 ms', icon: 'queue', row: 1 },
    { id: 'gpu', label: 'GPU runtime', sub: 'batch up to 32', icon: 'cpu', row: 2 }] },
]);
defineFlow('flow-ml-serving', {
  title: 'Live flow: an online prediction, dynamic batching and a slow feature store',
  hint: 'Follow one request at low traffic, then a burst that dynamic batching absorbs, then a feature-store timeout that degrades instead of failing.',
  zones: LmlSv.zones, h: LmlSv.h, nodes: LmlSv.nodes,
  edges: [['app', 'api'], ['api', 'fs'], ['api', 'log'], ['api', 'queue'], ['queue', 'gpu']],
  scenarios: [
    {
      id: 'one', name: 'One prediction',
      summary: 'A checkout asks for a fraud score. Timings are illustrative for a 50 ms p99 budget.',
      steps: [
        { path: ['app', 'api'], label: 'POST /predict {user, cart}', ms: 2, title: 'The request arrives',
          detail: 'It carries entity IDs and request-time context (cart value, device), not a ready-made feature vector.' },
        { path: ['api', 'fs', 'api'], label: 'MGET user, device, merchant', ms: 3, title: 'Fetch stored features in one round trip',
          detail: 'All entity lookups are batched. Feature fetches often cost as much of the budget as the model itself.' },
        { at: 'api', badge: 'vector: 300 features', title: 'Assemble the feature vector',
          detail: 'Same order, encoding and defaults for missing values as in training. Any difference here is training–serving skew.' },
        { path: ['api', 'queue'], label: 'enqueue', ms: .1, title: 'Join the batching queue',
          detail: 'The model server holds requests briefly so that concurrent ones can share one forward pass.' },
        { at: 'queue', badge: 'alone: waits 2 ms', tone: 'warn', ms: 2, title: 'At low traffic, the wait is pure cost',
          detail: 'No other request arrives, so this one waits the full maximum queue delay and runs alone. That is why the delay is kept to a few milliseconds.' },
        { path: ['queue', 'gpu', 'queue'], label: 'batch of 1', ms: 8, title: 'One forward pass',
          detail: 'Most of these ≈8 ms is fixed overhead (kernel launches, moving weights), which a bigger batch would have shared.' },
        { path: ['queue', 'api', 'app'], label: 'score 0.83, model v7', tone: 'ok', ms: 2, title: 'Answer with the model version',
          detail: 'Returning the version lets later analysis separate a regression from a rollout.' },
        { path: ['api', 'log'], label: 'features, score, version', async: true, title: 'Log it off the request path',
          detail: 'The prediction log feeds drift monitoring, label joins and the next training set.' },
      ],
    },
    {
      id: 'burst', name: 'Burst: dynamic batching',
      summary: 'A flash sale sends 400 requests at once. Numbers come from the chapter\'s micro-batcher simulation (8 ms fixed + 0.2 ms per row), not a real GPU.',
      steps: [
        { at: 'app', badge: '400 requests at once', title: 'A burst arrives',
          detail: 'Without batching the accelerator would run 400 forward passes of one row each.' },
        { path: ['app', 'api', 'queue'], label: '400 enqueued', ms: 5, title: 'The queue fills faster than the delay expires',
          detail: 'At high traffic a batch fills to its maximum size before the 2 ms delay runs out, so the delay costs nothing.' },
        { at: 'queue', badge: 'batches of ≈ 31', tone: 'ok', title: 'Group into batches',
          detail: 'The simulation averaged 30.8 rows per batch against a maximum of 32.' },
        { path: ['queue', 'gpu', 'queue'], label: '≈ 13 forward passes', ms: 190, title: 'Few passes instead of 400',
          detail: 'Each pass costs ≈ 8 + 0.2 × 32 ms, so the whole burst needs ≈ 13 passes instead of 400. Throughput went from 96 to about 1,865 requests per second.' },
        { path: ['queue', 'api', 'app'], label: 'p99 ≈ 210 ms (vs ≈ 4 s)', tone: 'ok', ms: 5, title: 'Latency under the burst collapses too',
          detail: 'Without batching, requests queued behind 400 single-row passes: p99 ≈ 4.1 s in the same simulation. Batching is both the throughput and the tail-latency fix.' },
      ],
    },
    {
      id: 'degraded', name: 'Feature store timeout',
      summary: 'The online store is slow. The service must still answer inside its budget, with a <b>degraded</b> flag, instead of failing the checkout.',
      steps: [
        { path: ['app', 'api'], label: 'POST /predict', ms: 2, title: 'A normal request' },
        { path: ['api', 'fs'], label: 'MGET …', badgeAt: 'fs', badge: 'timeout at 10 ms', tone: 'err', ms: 10, title: 'The feature fetch times out',
          detail: 'Every hop has its own timeout, derived from the overall deadline, so one slow dependency cannot eat the whole budget.' },
        { at: 'api', badge: 'defaults + degraded=true', tone: 'warn', title: 'Fall back to training-time defaults',
          detail: 'Missing features get the same defaults the model saw for missing values in training. Critical decisions (like fraud) may fall back to rules only instead.' },
        { path: ['api', 'queue', 'gpu', 'queue', 'api'], label: 'score with defaults', ms: 12, title: 'Score anyway',
          detail: 'The model still runs; its answer is less informed and is marked as such.' },
        { path: ['api', 'app'], label: 'score, degraded=true', tone: 'warn', ms: 1, title: 'Answer within the deadline',
          detail: 'The caller can choose a more conservative action, such as a step-up challenge, for degraded scores.' },
        { path: ['api', 'log'], label: 'degraded prediction', async: true, title: 'Count it',
          detail: 'Alert on the degraded rate: a slowly failing feature store looks like a quality drop, not an outage.' },
      ],
    },
  ],
});

/* ============================================= drift alert → triage → retrain == */
const LmlDr = lane([
  { label: 'SERVING', nodes: [
    { id: 'reg', label: 'Model registry', sub: '@champion alias', icon: 'archive', row: 0 },
    { id: 'server', label: 'Model server', sub: 'serves @champion', icon: 'model', row: 1 },
    { id: 'plog', label: 'Prediction log', sub: 'features + scores', icon: 'logs', row: 2 }] },
  { label: 'MONITORING', nodes: [
    { id: 'alert', label: 'Alerting', sub: 'page or ticket', icon: 'alert', row: 1 },
    { id: 'drift', label: 'Drift job', sub: 'PSI, null rates', icon: 'sigma', row: 2 }] },
  { label: 'RESPONSE', nodes: [
    { id: 'pipe', label: 'Retrain pipeline', sub: 'gates, train, eval', icon: 'workflow', row: 0 },
    { id: 'oncall', label: 'On-call engineer', sub: 'runbook', kind: 'client', icon: 'user', row: 1 }] },
  { label: 'UPSTREAM', nodes: [{ id: 'up', label: 'Orders service', sub: 'owns a feature source', icon: 'service', row: 1 }] },
]);
defineFlow('flow-drift-retrain', {
  title: 'Live flow: a drift alert, triage, and a gated retrain',
  hint: 'The same alert pipeline catches a broken upstream field (fix it, don\'t retrain) and a real population shift (retrain, gate, canary, promote).',
  zones: LmlDr.zones, h: LmlDr.h, nodes: LmlDr.nodes,
  edges: [
    ['reg', 'server'], ['server', 'plog'], ['plog', 'drift'], ['drift', 'alert'],
    ['alert', 'oncall'], ['oncall', 'pipe'], ['pipe', 'reg'], ['oncall', 'up'],
  ],
  scenarios: [
    {
      id: 'broken', name: 'Upstream break',
      summary: 'An upstream deploy renames a field. The model keeps returning 200 OK with worse answers. The first signal is a <b>data-quality</b> alert, and the right fix is upstream, not a retrain.',
      steps: [
        { path: ['server', 'plog'], label: 'predictions + features', async: true, title: 'Every prediction is logged',
          detail: 'Request ID, model version, the feature vector and the score.' },
        { path: ['plog', 'drift'], label: 'last hour', title: 'The hourly job reads a window',
          detail: 'It compares each feature\'s distribution and null rate with the training reference and last week\'s same hour.' },
        { at: 'drift', badge: 'null rate 0.1% → 31%', tone: 'err', title: 'A top feature went missing',
          detail: '<code>order_status</code> is now null for a third of requests. Null-rate checks catch this faster than any distribution test.' },
        { path: ['drift', 'alert', 'oncall'], label: 'page + runbook link', tone: 'err', title: 'Page the owner',
          detail: 'A data-quality break on a top feature is worth waking someone for. Most "drift" pages turn out to be exactly this.' },
        { at: 'oncall', badge: 'pipeline, not the world?', title: 'Runbook step 1: rule out the pipeline',
          detail: 'Check upstream deploys, schema changes, feature freshness, and whether one source accounts for the change.' },
        { path: ['oncall', 'up'], label: 'deploy 14:05 renamed field', badgeAt: 'up', badge: 'rolled back', tone: 'ok', title: 'Fix it where it broke',
          detail: 'Retraining now would teach the model the bug. A data contract with the upstream team prevents the next one.' },
        { path: ['plog', 'drift'], label: 'next window', badgeAt: 'drift', badge: 'null rate normal', tone: 'ok', title: 'The next window is clean',
          detail: 'Same model, same weights: nothing about the model needed to change.' },
      ],
    },
    {
      id: 'real', name: 'Real drift → retrain',
      summary: 'A marketing campaign brings many users aged 50–65, whom the model rarely saw. Inputs drift for a real reason, so the response is a <b>gated retrain</b> and a canary.',
      steps: [
        { path: ['plog', 'drift'], label: 'last day', title: 'The daily comparison runs' },
        { at: 'drift', badge: 'PSI(age) = 0.45', tone: 'warn', title: 'A significant shift in a top feature',
          detail: 'Above the 0.25 rule of thumb. The KS p-value is effectively 0, but that is true for trivial shifts too, which is why the alert uses the effect size.' },
        { path: ['drift', 'alert', 'oncall'], label: 'ticket, not a page', title: 'Route by urgency',
          detail: 'No data broke and mature-label quality has not dropped yet, so this goes to the daily queue.' },
        { at: 'oncall', badge: 'real: new audience', title: 'Confirm it is the world, not the pipeline',
          detail: 'Data quality is clean, the change is broad and persistent, and marketing confirms the campaign. Slice metrics show worse calibration for 50–65s.' },
        { path: ['oncall', 'pipe'], label: 'trigger retrain', title: 'Retrain on recent data',
          detail: 'The window now includes the new users. Recent rows may be up-weighted.' },
        { at: 'pipe', badge: 'gates pass', tone: 'ok', title: 'Same gates as any model',
          detail: 'Data validation, beats the champion overall, no slice worse by more than the limit, latency within budget on the serving hardware.' },
        { path: ['pipe', 'reg'], label: 'v8 → @challenger', title: 'Register the candidate',
          detail: 'With lineage: code SHA, data version, params, metrics per slice.' },
        { path: ['reg', 'server'], label: 'canary 5%', badgeAt: 'server', badge: 'guardrails ok', tone: 'ok', title: 'Canary on live traffic',
          detail: 'Error rate, latency and prediction distribution are compared with the champion before any wider rollout.' },
        { at: 'reg', badge: '@champion → v8', tone: 'ok', title: 'Promote by moving an alias',
          detail: 'Rollback is moving the alias back to v7: one step, no rebuild.' },
      ],
    },
  ],
});

}
