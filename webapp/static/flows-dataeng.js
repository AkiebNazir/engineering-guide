/* Live flows for the dataeng module (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ======================================================== Spark shuffle == */
const LdeSpark = lane([
  { label: 'DRIVER · INPUT', nodes: [
    { id: 'drv', label: 'Driver', sub: 'DAG scheduler', icon: 'scheduler', row: 0 },
    { id: 'in', label: 'Parquet in S3', sub: '2 file splits', icon: 'storage', row: 2 }] },
  { label: 'STAGE 1 · MAP', nodes: [
    { id: 'm1', label: 'Map task 1', sub: 'executor A', icon: 'worker', row: 1 },
    { id: 'm2', label: 'Map task 2', sub: 'executor B', icon: 'worker', row: 3 }] },
  { label: 'SHUFFLE', nodes: [
    { id: 'shuf', label: 'Shuffle files', sub: 'local disk, by key', icon: 'disk', row: 2 }] },
  { label: 'STAGE 2 · REDUCE', nodes: [
    { id: 'r1', label: 'Reduce task 1', sub: 'countries A–M', icon: 'sigma', row: 1 },
    { id: 'r2', label: 'Reduce task 2', sub: 'countries N–Z', icon: 'sigma', row: 3 }] },
  { label: 'OUTPUT', nodes: [{ id: 'out', label: 'Output table', sub: 'Parquet / Iceberg', icon: 'table', row: 2 }] },
]);
defineFlow('flow-spark-shuffle', {
  title: 'Live flow: one Spark job, two stages and the shuffle between them',
  hint: 'Follow groupBy(country).count() through map tasks, shuffle files and reduce tasks, then watch a skewed key and a lost executor.',
  zones: LdeSpark.zones, h: LdeSpark.h, nodes: LdeSpark.nodes,
  edges: [
    ['in', 'm1'], ['in', 'm2'], ['m1', 'shuf'], ['m2', 'shuf'],
    ['shuf', 'r1'], ['shuf', 'r2'], ['r1', 'out'], ['r2', 'out'],
    ['drv', 'm1'], ['drv', 'r1'],
  ],
  scenarios: [
    {
      id: 'happy', name: 'groupBy: one shuffle',
      summary: 'The action <code>write</code> starts a job. The <code>groupBy</code> is a wide dependency, so the driver cuts the job into <b>two stages</b> at the shuffle.',
      steps: [
        { at: 'drv', badge: 'job → 2 stages', title: 'The driver plans the job',
          detail: 'Catalyst pushes the date filter into the Parquet scan and reads two columns only. The <code>Exchange</code> (shuffle) in the physical plan becomes the boundary between stage 1 and stage 2.' },
        { path: ['drv', 'm1'], label: 'launch stage 1 tasks', title: 'One task per input partition',
          detail: 'Each map task gets one file split (≈128 MB by default). Filter and projection are pipelined inside the task, with no data movement.' },
        { path: ['in', 'm1'], label: 'read split 1', ms: 4000, title: 'Read only what is needed',
          detail: 'Row groups whose min/max stats rule out the date are skipped. The ≈4 s is illustrative.' },
        { at: 'm1', badge: 'partial count per country', tone: 'ok', title: 'Map-side combine',
          detail: 'Before shuffling, each task pre-aggregates: one row per country instead of millions of clicks. This is why <code>count</code> and <code>sum</code> shuffle so little.' },
        { path: ['m1', 'shuf'], label: 'write sorted by partition', title: 'Shuffle write',
          detail: 'Each row goes to reduce partition <code>hash(country) mod N</code>. The task writes one data file plus an index file to its executor\'s local disk.' },
        { path: ['m2', 'shuf'], label: 'write sorted by partition', title: 'The other map task does the same',
          detail: 'Stage 2 cannot start until every map task has finished, because any of them may hold rows for any country.' },
        { path: ['drv', 'r1'], label: 'launch stage 2', title: 'The barrier lifts',
          detail: 'The driver\'s MapOutputTracker knows where every map output block is. With AQE on, it first coalesces the 200 default shuffle partitions into a few right-sized ones.' },
        { path: ['shuf', 'r1'], label: 'fetch A–M blocks', title: 'Shuffle read',
          detail: 'Each reduce task fetches its block from every map output over the network (M × N fetches in total), merges them, and finishes the count.' },
        { path: ['r1', 'out'], label: 'write part files', tone: 'ok', title: 'Results written',
          detail: 'With dynamic partition overwrite or an Iceberg commit, a retry replaces this output instead of duplicating it.' },
      ],
    },
    {
      id: 'skew', name: 'Skewed key',
      summary: 'One key holds most of the rows. Its reduce partition becomes a <b>straggler</b>, and the stage waits for it.',
      steps: [
        { path: ['m1', 'shuf'], label: 'write by hash(country)', title: 'Map tasks write as usual',
          detail: 'Most rows have <code>country = NULL</code> because a client bug stopped sending it.' },
        { at: 'shuf', badge: 'partition 7: 40 GB', tone: 'warn', title: 'One partition is huge',
          detail: 'Every NULL hashes to the same reduce partition. The other partitions hold ≈200 MB each.' },
        { path: ['shuf', 'r2'], label: 'fetch 40 GB', tone: 'warn', title: 'One reducer gets it all',
          detail: 'The Spark UI shows it: median task 40 s, max task 45 min, and the stage stuck at 199/200.' },
        { at: 'r2', badge: 'spilling, 45 min', tone: 'err', title: 'The straggler',
          detail: 'The task spills to disk repeatedly and may die with an out-of-memory error. More executors do not help: one key goes to one task.' },
        { at: 'drv', badge: 'AQE: split skewed partition', tone: 'ok', title: 'Fix: split or salt the key',
          detail: 'For joins, AQE splits a partition over 5× the median and over 256 MB into several tasks. For aggregations, filter the NULLs or salt the key and aggregate twice.' },
        { path: ['shuf', 'r1'], label: 'balanced sub-partitions', tone: 'ok', title: 'Work spreads out again',
          detail: 'With the key handled, no reduce task is much bigger than the others and the stage finishes in minutes.' },
      ],
    },
    {
      id: 'lost', name: 'Executor lost',
      summary: 'Shuffle files live on executors\' local disks. Lose the executor and its map outputs are gone.',
      steps: [
        { path: ['m2', 'shuf'], label: 'map output on executor B', title: 'Stage 1 finishes',
          detail: 'Map task 2\'s shuffle files sit on executor B\'s local disk.' },
        { at: 'm2', badge: 'executor B lost', tone: 'err', title: 'A node disappears',
          detail: 'A spot instance is reclaimed or the container is killed for exceeding its memory overhead (exit code 137).' },
        { path: ['shuf', 'r1'], label: 'FetchFailedException', tone: 'err', title: 'A reducer cannot fetch its block',
          detail: 'The reduce task fails, and this is not an ordinary task retry: its input no longer exists anywhere.' },
        { at: 'drv', badge: 'resubmit lost map task', tone: 'warn', title: 'Lineage to the rescue',
          detail: 'The driver marks executor B\'s map outputs as lost and re-runs only map task 2, from its lineage. Stage 1\'s other outputs are kept.' },
        { path: ['in', 'm2'], label: 're-read split 2', title: 'Recompute from the source',
          detail: 'The input in S3 is immutable, so recomputing gives the same result. An external shuffle service or graceful decommissioning would have kept the files available.' },
        { path: ['m2', 'shuf'], label: 'rewrite map output', title: 'Map output restored' },
        { path: ['shuf', 'r1', 'out'], label: 'retry reduce, write', tone: 'ok', title: 'The job completes',
          detail: 'The only cost of the failure was re-running one map task and one reduce task.' },
      ],
    },
  ],
});

/* ======================================================= stream watermark == */
const LdeWm = lane([
  { label: 'PHONES', nodes: [
    { id: 'pa', label: 'Phone A', sub: 'online', kind: 'client', icon: 'mobile', row: 0 },
    { id: 'pb', label: 'Phone B', sub: 'offline in a tunnel', kind: 'client', icon: 'mobile', row: 2 }] },
  { label: 'LOG', nodes: [{ id: 'kafka', label: 'Kafka', sub: 'topic: clicks', row: 1 }] },
  { label: 'SOURCE', nodes: [{ id: 'src', label: 'Source', sub: 'wm = max ts − 20 s', icon: 'timer', row: 1 }] },
  { label: 'WINDOW', nodes: [
    { id: 'win', label: 'Window op', sub: '1-min tumbling', icon: 'worker', row: 1 },
    { id: 'state', label: 'Window state', sub: 'RocksDB', icon: 'kv', row: 2 }] },
  { label: 'OUTPUTS', nodes: [
    { id: 'sink', label: 'Results', sub: 'upsert by window', icon: 'table', row: 1 },
    { id: 'late', label: 'Late events', sub: 'side output', icon: 'warn', row: 2 }] },
]);
defineFlow('flow-stream-watermark', {
  title: 'Live flow: event time, a watermark, a late event and a too-late one',
  hint: 'Watch a 1-minute window fire when the watermark passes it, update for a late click, and send a very late click to the side output.',
  zones: LdeWm.zones, h: LdeWm.h, nodes: LdeWm.nodes,
  edges: [
    ['pa', 'kafka'], ['pb', 'kafka'], ['kafka', 'src'], ['src', 'win'],
    ['win', 'state'], ['win', 'sink'], ['win', 'late'],
  ],
  scenarios: [
    {
      id: 'fire', name: 'Window fires on the watermark',
      summary: 'Window <b>[12:00, 12:01)</b> collects clicks by <b>event time</b>. It fires when the watermark, not the wall clock, passes 12:01.',
      steps: [
        { path: ['pa', 'kafka', 'src'], label: 'click @12:00:05', title: 'A click arrives',
          detail: 'The phone stamps the event time. Kafka keeps the click in order within its partition.' },
        { at: 'src', badge: 'watermark 11:59:45', title: 'The source tracks the watermark',
          detail: 'watermark = largest event time seen − 20 s. It moves only when newer events arrive.' },
        { path: ['src', 'win', 'state'], label: 'count[12:00] = 1', title: 'Add to the window\'s state',
          detail: 'The window is keyed by ad and by window start. Its count lives in RocksDB and is included in every checkpoint.' },
        { path: ['pa', 'kafka', 'src', 'win'], label: 'clicks @12:00:12, :58, :47', title: 'More clicks, one out of order',
          detail: 'The 12:00:47 click arrives after 12:00:58. It is out of order but <b>not late</b>: the watermark has not passed 12:01 yet, so it is simply counted.' },
        { path: ['pa', 'kafka', 'src'], label: 'click @12:01:23', title: 'A click from the next minute',
          detail: 'The largest event time is now 12:01:23.' },
        { at: 'src', badge: 'watermark 12:01:03', tone: 'ok', title: 'The watermark passes 12:01',
          detail: 'The job now asserts that no more events at or before 12:01:03 are expected.' },
        { path: ['win', 'sink'], label: '[12:00,12:01) → 4', tone: 'ok', title: 'The window fires',
          detail: 'The on-time result is written. The state is kept for the allowed lateness (30 s of event time) in case stragglers arrive.' },
      ],
    },
    {
      id: 'late', name: 'Late but allowed',
      summary: 'A click stamped 12:00:55 arrives after the window fired. It is within <b>allowed lateness</b>, so the window fires again with a corrected count.',
      steps: [
        { at: 'pb', badge: 'buffered 45 s', title: 'Phone B was in a tunnel',
          detail: 'The SDK kept the click and sends it once the network is back.' },
        { path: ['pb', 'kafka', 'src'], label: 'click @12:00:55', tone: 'warn', title: 'It arrives behind the watermark',
          detail: 'The watermark is already 12:01:03, so this event is <b>late</b>.' },
        { path: ['src', 'win', 'state'], label: 'count 4 → 5', title: 'The window\'s state still exists',
          detail: 'The window end (12:01:00) plus 30 s of allowed lateness is still ahead of the watermark, so the state has not been purged.' },
        { path: ['win', 'sink'], label: '[12:00,12:01) → 5', tone: 'ok', title: 'The window fires again',
          detail: 'The sink must <b>upsert</b> by (window, ad), or the first result and the correction will both be counted downstream.' },
      ],
    },
    {
      id: 'toolate', name: 'Too late: side output',
      summary: 'Once the watermark passes window end + allowed lateness, the window\'s state is gone. Later events go to a <b>side output</b>.',
      steps: [
        { path: ['pa', 'kafka', 'src'], label: 'click @12:01:50', title: 'Time moves on',
          detail: 'The watermark rises to 12:01:30, which is 12:01:00 + 30 s of allowed lateness.' },
        { path: ['win', 'state'], label: 'purge [12:00,12:01)', title: 'State cleanup',
          detail: 'The window\'s state is deleted. This is what keeps memory bounded on an infinite stream.' },
        { path: ['pb', 'kafka', 'src'], label: 'click @12:00:40', tone: 'warn', title: 'A very late click',
          detail: 'Another offline phone reconnects and sends a click from almost a minute ago.' },
        { path: ['src', 'win', 'late'], label: 'no window to update', tone: 'err', title: 'Routed to the side output',
          detail: 'The event is not silently lost. It is written to a late-events topic or table, and the late-event rate is a monitored metric.' },
        { at: 'late', badge: 'batch reconciliation', tone: 'ok', title: 'Someone reconciles it',
          detail: 'A nightly batch job over complete data corrects the totals where money is involved. A looser watermark would have caught it, at the cost of later results and more state.' },
      ],
    },
  ],
});

/* ============================================================ CDC pipeline == */
const LdeCdc = lane([
  { label: 'APP', nodes: [{ id: 'app', label: 'Order service', sub: 'writes orders', icon: 'service', row: 1 }] },
  { label: 'POSTGRES', nodes: [
    { id: 'pg', label: 'Postgres', sub: 'primary', kind: 'db', row: 1 },
    { id: 'slot', label: 'Repl. slot', sub: 'holds WAL', icon: 'logs', row: 2 }] },
  { label: 'KAFKA CONNECT', nodes: [{ id: 'dbz', label: 'Debezium', sub: 'source connector', icon: 'worker', row: 2 }] },
  { label: 'KAFKA', nodes: [{ id: 'topic', label: 'Kafka topic', sub: 'key = order id', row: 2 }] },
  { label: 'LAKEHOUSE', nodes: [
    { id: 'sink', label: 'Sink job', sub: 'dedupe + MERGE', icon: 'worker', row: 2 },
    { id: 'lake', label: 'Iceberg table', sub: 'orders, by LSN', icon: 'table', row: 1 }] },
]);
defineFlow('flow-cdc-pipeline', {
  title: 'Live flow: change data capture from Postgres to the lakehouse',
  hint: 'Follow a committed UPDATE out of the WAL into Kafka and the lakehouse, then a delete, then a stopped connector filling the primary\'s disk.',
  zones: LdeCdc.zones, h: LdeCdc.h, nodes: LdeCdc.nodes,
  edges: [
    ['app', 'pg'], ['pg', 'slot'], ['slot', 'dbz'], ['dbz', 'topic'],
    ['topic', 'sink'], ['sink', 'lake'],
  ],
  scenarios: [
    {
      id: 'update', name: 'An update flows through',
      summary: 'CDC reads the database\'s own log, so every <b>committed</b> change is captured in commit order without querying the tables.',
      steps: [
        { path: ['app', 'pg'], label: 'UPDATE status=refunded', ms: 3, title: 'The app commits a change',
          detail: 'Nothing about the app changes for CDC. The commit writes a WAL record, as every Postgres commit does.' },
        { path: ['pg', 'slot'], label: 'WAL @ LSN 0/8EF3A1C0', title: 'The change is in the WAL',
          detail: 'With <code>wal_level=logical</code>, the record carries enough information to decode into a row change. The replication slot remembers how far its consumer has read.' },
        { path: ['slot', 'dbz'], label: 'pgoutput decode', title: 'Logical decoding',
          detail: 'Debezium streams from the slot and receives only committed changes, in commit order. Uncommitted or rolled-back work never appears.' },
        { path: ['dbz', 'topic'], label: 'op=u, before, after', title: 'One event per row change',
          detail: 'The message key is the primary key, so all changes to order 812 land on one partition, in order. The value has the before and after images, the op and the source LSN.' },
        { at: 'dbz', badge: 'offset committed', tone: 'ok', title: 'Acknowledge the slot',
          detail: 'Once Kafka has the event, Debezium confirms the LSN back to Postgres, so the primary can recycle older WAL.' },
        { path: ['topic', 'sink'], label: 'micro-batch', ms: 30000, title: 'The sink consumes',
          detail: 'The sink keeps only the latest change per key in each batch (ordered by LSN). The 30 s batch interval is illustrative.' },
        { path: ['sink', 'lake'], label: 'MERGE if newer LSN', tone: 'ok', title: 'Apply idempotently',
          detail: 'The MERGE updates only if the event\'s LSN is newer than the stored one, so a replay after a crash cannot overwrite newer data.' },
      ],
    },
    {
      id: 'delete', name: 'A hard delete',
      summary: 'The case a <code>updated_at</code> extract can never see: the row is gone. CDC turns it into an event.',
      steps: [
        { path: ['app', 'pg'], label: 'DELETE order 813', title: 'The app deletes a row',
          detail: 'An incremental <code>SELECT ... WHERE updated_at &gt; mark</code> would find nothing to copy.' },
        { path: ['pg', 'slot', 'dbz'], label: 'decoded delete', title: 'The delete is in the log',
          detail: 'With <code>REPLICA IDENTITY FULL</code>, the event carries the whole old row. By default it carries only the key.' },
        { path: ['dbz', 'topic'], label: 'op=d, then tombstone', title: 'Delete event plus tombstone',
          detail: 'A null-value tombstone with the same key follows, so log compaction can eventually drop the key from the topic.' },
        { path: ['topic', 'sink', 'lake'], label: 'WHEN MATCHED AND op=d THEN DELETE', tone: 'ok', title: 'The lakehouse row is removed',
          detail: 'With merge-on-read, Iceberg writes a small delete file now and compaction rewrites data files later.' },
      ],
    },
    {
      id: 'slot', name: 'Stopped connector fills the disk',
      summary: 'A replication slot keeps <b>all WAL</b> since its consumer\'s last confirmed position. A consumer that stops can take the primary down.',
      steps: [
        { at: 'dbz', badge: 'connector stopped', tone: 'err', title: 'Debezium stops',
          detail: 'A bad deploy, an expired credential, or a schema change it cannot handle.' },
        { path: ['app', 'pg', 'slot'], label: 'writes continue', title: 'The app keeps writing',
          detail: 'Every commit adds WAL, and the slot will not let Postgres recycle any of it.' },
        { at: 'slot', badge: 'retained WAL: 180 GB', tone: 'warn', title: 'WAL piles up',
          detail: 'The alert that should fire: <code>pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)</code> per slot.' },
        { at: 'pg', badge: 'disk full: writes fail', tone: 'err', title: 'The primary is in danger',
          detail: 'An analytics pipeline has now caused a production outage.' },
        { at: 'slot', badge: 'max_slot_wal_keep_size', tone: 'ok', title: 'The guard rail',
          detail: 'Since Postgres 13 this setting invalidates a slot that falls too far behind instead of filling the disk. The pipeline then needs a re-snapshot, which is a much better failure.' },
        { path: ['slot', 'dbz', 'topic'], label: 'resume or re-snapshot', tone: 'ok', title: 'Recover',
          detail: 'If the slot survived, Debezium resumes from its offset and catches up. If not, an incremental snapshot rebuilds the table while streaming continues.' },
      ],
    },
  ],
});

}
