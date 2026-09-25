/* Live request flows (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ======================================================= write-ahead log == */
const Lwal = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', sub: 'app or psql', kind: 'client', row: 1 }] },
  { label: 'DB ENGINE · RAM', nodes: [
    { id: 'ckpt', label: 'Checkpointer', sub: 'background', icon: 'timer', row: 0 },
    { id: 'txn', label: 'Transaction', sub: 'backend process', icon: 'process', row: 1 },
    { id: 'buf', label: 'Buffer pool', sub: 'dirty pages in RAM', icon: 'memory', row: 2 }] },
  { label: 'DISK', nodes: [
    { id: 'wal', label: 'WAL', sub: 'append-only, fsync', icon: 'logs', row: 1 },
    { id: 'pages', label: 'Data pages', sub: 'B-tree / SSTables', icon: 'disk', row: 2 }] },
]);
defineFlow('flow-wal', {
  title: 'Live flow: a commit is durable at the WAL fsync, not at the page write',
  hint: 'Follow one UPDATE to disk, watch a checkpoint, then pull the plug and watch recovery replay the log.',
  zones: Lwal.zones, h: Lwal.h, nodes: Lwal.nodes,
  edges: [
    ['client', 'txn'], ['txn', 'buf'], ['txn', 'wal'], ['buf', 'pages'],
    ['ckpt', 'buf'], ['ckpt', 'wal'], ['wal', 'pages'],
  ],
  scenarios: [
    {
      id: 'commit', name: 'Commit is durable at fsync',
      summary: 'Two writes happen, at two different times. The <b>WAL record</b> is fsynced before the commit is acknowledged. The <b>data page</b> is written whenever it suits the engine.',
      steps: [
        { path: ['client', 'txn'], label: 'UPDATE …; COMMIT', ms: 1, title: 'Client sends the change',
          detail: 'The engine has to make this survive a crash. It does not want to rewrite a random 8 KB page on disk for every row it touches.' },
        { path: ['txn', 'buf'], label: 'modify page', badgeAt: 'buf', badge: 'page dirty', ms: .01, title: 'Change the page in memory only',
          detail: 'The page is updated in the buffer pool and marked <b>dirty</b>, so the copy in RAM is now newer than the one on disk. This takes microseconds.' },
        { path: ['txn', 'wal'], label: 'append + fsync', badgeAt: 'wal', badge: 'durable', tone: 'ok', ms: 1, title: 'Append the log record and fsync',
          detail: 'A small sequential append, then <code>fsync</code>, typically around a millisecond on an SSD. <b>This is the moment the commit becomes durable</b>, because the log alone is enough to rebuild the change.' },
        { path: ['txn', 'client'], label: 'COMMIT OK', tone: 'ok', ms: 1, title: 'Acknowledge the client',
          detail: 'The client hears "committed" even though the data page on disk still holds the old value.' },
        { path: ['buf', 'pages'], label: 'flush dirty page', async: true, title: 'Write the page later',
          detail: 'The page is written in place, or a new SSTable is written, whenever the engine chooses. Many commits to the same hot page can share one page write.' },
      ],
    },
    {
      id: 'checkpoint', name: 'Checkpoint',
      summary: 'A checkpoint bounds recovery time. Everything logged before it is already in the data files, so replay can start there.',
      steps: [
        { at: 'ckpt', badge: 'checkpoint starts', ms: 1, title: 'Checkpoint begins',
          detail: 'Checkpoints run in the background on a timer or after a set amount of WAL. Without them, recovery would have to replay the log from the beginning.' },
        { path: ['ckpt', 'buf'], label: 'flush all dirty pages', ms: 200, title: 'Collect every dirty page',
          detail: 'The checkpointer walks the buffer pool. The ≈200 ms here is illustrative; real checkpoints are spread out so they do not starve foreground I/O.' },
        { path: ['buf', 'pages'], label: 'write pages', ms: 100, title: 'Pages reach the data files',
          detail: 'After this, the data files hold every change logged before the checkpoint started.' },
        { path: ['ckpt', 'wal'], label: 'checkpoint record', badgeAt: 'wal', badge: 'redo starts here', tone: 'ok', ms: 1, title: 'Log where replay can begin',
          detail: 'The checkpoint record marks the log position recovery will start from, so everything before it is no longer needed to recover from a crash.' },
        { at: 'wal', badge: 'old segments recyclable', tone: 'ok', ms: 1, title: 'Older WAL can be recycled',
          detail: 'Log segments before the checkpoint can be reused or deleted, unless a replica or an archive still needs them.' },
      ],
    },
    {
      id: 'crash', name: 'Crash and recovery',
      summary: 'Power fails after the commit was acknowledged but before its page was flushed. The WAL still has the change.',
      steps: [
        { path: ['txn', 'wal'], label: 'commit record + fsync', badgeAt: 'wal', badge: 'x = v2 logged', tone: 'ok', ms: 1, title: 'The commit reaches the log',
          detail: 'The log record describing <code>x = v2</code> is on disk.' },
        { path: ['txn', 'client'], label: 'COMMIT OK', tone: 'ok', ms: 1, title: 'Client is told it committed',
          detail: 'From here on the database has promised the change will survive.' },
        { at: 'buf', badge: 'power loss: RAM gone', tone: 'err', ms: 0, title: 'Crash before the page flush',
          detail: 'The dirty page holding <code>v2</code> existed only in memory, and now it is gone.' },
        { at: 'pages', badge: 'page still says v1', tone: 'warn', ms: 0, title: 'The data file is behind',
          detail: 'On its own, the data file would lose an acknowledged commit. This gap is the reason the WAL exists.' },
        { path: ['wal', 'pages'], label: 'redo since checkpoint', badgeAt: 'pages', badge: 'x = v2 restored', tone: 'ok', ms: 500, title: 'Startup replays the log',
          detail: 'Recovery reads the WAL forward from the last checkpoint and reapplies every change. Transactions with no commit record in the log are not kept. The ≈500 ms is illustrative, and it grows with the WAL written since the last checkpoint.' },
        { path: ['client', 'txn', 'client'], label: 'SELECT x → v2', tone: 'ok', ms: 2, title: 'The acknowledged write is there',
          detail: 'The database opens only after replay finishes, so no client ever sees the pre-crash data file.' },
      ],
    },
  ],
});

/* ========================================================== cache-aside == */
const Lca = lane([
  { label: 'CALLERS', nodes: [
    { id: 'reader', label: 'Reader', sub: 'GET product 9', kind: 'client', row: 0 },
    { id: 'writer', label: 'Writer', sub: 'updates product 9', kind: 'client', row: 1 }] },
  { label: 'APP', nodes: [{ id: 'app', label: 'App', sub: 'cache + DB client', icon: 'app', row: 0.5 }] },
  { label: 'CACHE', nodes: [{ id: 'cache', label: 'Redis', sub: 'TTL is the backstop', kind: 'cache', row: 0 }] },
  { label: 'SOURCE', nodes: [{ id: 'db', label: 'Database', sub: 'source of truth', kind: 'db', row: 1 }] },
]);
defineFlow('flow-cache-aside', {
  title: 'Live flow: cache-aside reads, writes and the set-after-delete race',
  hint: 'Watch a miss pay the database once, a write delete the key, and a slow reader put a stale value back.',
  zones: Lca.zones, h: Lca.h, nodes: Lca.nodes,
  edges: [['reader', 'app'], ['writer', 'app'], ['app', 'cache'], ['app', 'db']],
  scenarios: [
    {
      id: 'read', name: 'Read: miss, then hit',
      summary: 'The app checks the cache and, on a miss, reads the database and fills the cache itself. Timings are from a local run with a fake 50 ms database: <b>56.5 ms</b> on the miss, <b>0.6 ms</b> on the hit.',
      steps: [
        { path: ['reader', 'app'], label: 'GET product 9', title: 'A request arrives',
          detail: 'The network time to the app is left out, so the numbers match what the app measured.' },
        { path: ['app', 'cache', 'app'], label: 'GET product:9', badgeAt: 'cache', badge: 'miss', tone: 'warn', ms: .5, title: 'Try the cache first',
          detail: 'The key is not there (cold start, eviction or expiry), and Redis returns nil. The cache never reads the database itself.' },
        { path: ['app', 'db', 'app'], label: 'slow_db_lookup(9)', ms: 55.5, title: 'Pay the full source latency once',
          detail: 'The fake database sleeps 50 ms, and the rest is client overhead. If many callers miss the same key at once, they all do this together, which is a stampede.' },
        { path: ['app', 'cache'], label: 'SET product:9 EX 30', badgeAt: 'cache', badge: 'TTL 30 s', ms: .5, title: 'Fill the cache for the next caller',
          detail: 'The app writes the value with a TTL. The TTL bounds how long a wrong value can live, whatever else goes wrong.' },
        { path: ['app', 'reader'], label: 'value (56.5 ms)', title: 'First caller answered',
          detail: 'Only the first reader after a miss pays for the database read.' },
        { path: ['reader', 'app', 'cache', 'app', 'reader'], label: 'GET again → hit', badgeAt: 'reader', badge: '0.6 ms', tone: 'ok', ms: .6, title: 'Every later read is a hit',
          detail: 'Roughly 90× faster in this run. The cache can be wiped at any time without losing data, because the database is untouched.' },
      ],
    },
    {
      id: 'write', name: 'Write: update DB, delete key',
      summary: 'Writes go to the database. Then the app <b>deletes</b> the cache key rather than updating it, and the next reader refills it.',
      steps: [
        { path: ['writer', 'app'], label: 'update product 9', ms: 1, title: 'A write arrives' },
        { path: ['app', 'db', 'app'], label: 'UPDATE …; COMMIT', badgeAt: 'db', badge: 'v2 committed', tone: 'ok', ms: 5, title: 'Write the source of truth first',
          detail: 'The database is the only copy that matters. The ≈5 ms is illustrative.' },
        { path: ['app', 'cache'], label: 'DEL product:9', badgeAt: 'cache', badge: 'key gone', ms: .5, title: 'Delete, don\'t update',
          detail: 'If two writers each <code>SET</code> the cache, their sets can arrive out of order and leave the older value cached indefinitely. A delete is idempotent and order-insensitive.' },
        { path: ['app', 'writer'], label: 'OK', tone: 'ok', ms: 1, title: 'Writer is done',
          detail: 'The write path never waits on filling the cache.' },
        { path: ['reader', 'app', 'cache', 'app'], label: 'GET product:9', badgeAt: 'app', badge: 'miss', tone: 'warn', ms: .5, title: 'The next reader misses',
          detail: 'The key is gone, so the reader takes the miss path.' },
        { path: ['app', 'db', 'app', 'cache'], label: 'read v2, SET EX 30', badgeAt: 'cache', badge: 'v2 cached', tone: 'ok', ms: 56, title: 'The reader refills with v2',
          detail: 'The cache holds the new value again, until it is evicted or the TTL fires.' },
      ],
    },
    {
      id: 'race', name: 'Race: set after delete',
      summary: 'The classic cache-aside race. A slow reader reads the old row, the writer commits and deletes, and then the reader <b>sets the old value</b>.',
      steps: [
        { path: ['reader', 'app', 'cache', 'app'], label: 'R: GET x', badgeAt: 'app', badge: 'miss', tone: 'warn', ms: .5, title: 'Reader misses',
          detail: 'One request in the app, serving the reader, finds the key missing.' },
        { path: ['app', 'db', 'app'], label: 'R: read x → v1', badgeAt: 'app', badge: 'holding v1', ms: 50, title: 'Reader gets v1 and then stalls',
          detail: 'A GC pause, a slow network hop or a busy thread holds the reader\'s request between its read and its set.' },
        { path: ['writer', 'app', 'db'], label: 'W: x = v2', badgeAt: 'db', badge: 'v2 committed', ms: 5, title: 'Writer commits v2',
          detail: 'Meanwhile, another request in the app writes the database.' },
        { path: ['app', 'cache'], label: 'W: DEL x', badgeAt: 'cache', badge: 'key gone', ms: .5, title: 'Writer deletes the key',
          detail: 'The writer follows the rule correctly. The cache is empty and the database holds v2.' },
        { path: ['app', 'cache'], label: 'R: SET x = v1', badgeAt: 'cache', badge: 'stale v1', tone: 'err', ms: .5, title: 'Reader sets the old value',
          detail: 'The reader wakes up and caches the <code>v1</code> it read before the write. No further delete is coming.' },
        { at: 'cache', badge: 'v1 until TTL', tone: 'err', ms: 0, title: 'Stale until the TTL fires',
          detail: 'The cache says v1 and the database says v2. To close the race, use a <b>lease token</b> (a delete voids it) or a <b>versioned</b> compare-and-set. The TTL is the backstop either way.' },
      ],
    },
  ],
});

/* ================================================== transactional outbox == */
const Lob = lane([
  { label: 'SERVICE', nodes: [{ id: 'app', label: 'Order service', sub: 'business logic', icon: 'service', row: 0 }] },
  { label: 'DATABASE', nodes: [{ id: 'db', label: 'Orders DB', sub: 'orders + outbox', kind: 'db', row: 0 }] },
  { label: 'RELAY', nodes: [{ id: 'relay', label: 'Outbox relay', sub: 'polling or CDC', icon: 'worker', row: 0 }] },
  { label: 'STREAM', nodes: [{ id: 'stream', label: 'Queue / stream', sub: 'at-least-once', icon: 'stream', row: 0 }] },
  { label: 'CONSUMER', nodes: [
    { id: 'cons', label: 'Consumer', sub: 'ships the order', icon: 'worker', row: 0 },
    { id: 'dedup', label: 'Processed IDs', sub: 'unique event_id', icon: 'table', row: 1 }] },
]);
defineFlow('flow-outbox', {
  title: 'Live flow: the transactional outbox, from lost events to safe duplicates',
  hint: 'See the dual-write gap, then how one transaction plus a relay closes it, and why the consumer still has to dedup.',
  zones: Lob.zones, h: Lob.h, nodes: Lob.nodes,
  edges: [
    ['app', 'db'], ['db', 'relay'], ['relay', 'stream'], ['stream', 'cons'], ['cons', 'dedup'],
  ],
  scenarios: [
    {
      id: 'dual', name: 'Dual write: lost event',
      summary: 'Without an outbox the service commits and <i>then</i> publishes. A crash between the two leaves the database and the rest of the system disagreeing. Publishing first has the mirror problem: a rollback after the event went out.',
      steps: [
        { path: ['app', 'db', 'app'], label: 'INSERT order; COMMIT', badgeAt: 'app', badge: 'order 42 saved', tone: 'ok', ms: 5, title: 'The order commits',
          detail: 'The database now says order 42 exists. The event is supposed to be sent next, as a separate call to the broker.' },
        { at: 'app', badge: 'crash before publish()', tone: 'err', ms: 0, title: 'Process dies between the two writes',
          detail: 'A deploy, OOM kill or node failure lands between the commit and the publish. Nothing retries the publish, because nothing recorded that it was owed.' },
        { at: 'stream', badge: 'no OrderPlaced', tone: 'warn', ms: 0, title: 'The event never exists',
          detail: 'No retry or dead-letter queue can help, because there is no message to retry.' },
        { at: 'cons', badge: 'order never ships', tone: 'err', ms: 0, title: 'Downstream never finds out',
          detail: 'The customer was charged and nothing ships. Two separate writes cannot be made atomic without a distributed transaction.' },
      ],
    },
    {
      id: 'happy', name: 'Outbox: happy path',
      summary: 'The order row and the event row commit in <b>one local transaction</b>. A separate relay publishes the event afterwards and marks it done.',
      steps: [
        { path: ['app', 'db'], label: 'INSERT order + INSERT outbox', badgeAt: 'db', badge: 'one transaction', ms: 5, title: 'Write the change and the event together',
          detail: 'The outbox row is <code>(OrderPlaced, published=false)</code> in the same database, so no distributed transaction is needed. The ≈5 ms is illustrative.' },
        { path: ['db', 'app'], label: 'COMMIT', badgeAt: 'app', badge: 'both rows or neither', tone: 'ok', ms: 1, title: 'Commit is atomic',
          detail: 'If the transaction rolls back, the event row rolls back with it, so an event is never published for an order that did not happen.' },
        { path: ['relay', 'db', 'relay'], label: 'SELECT … WHERE published=false', async: true, title: 'Relay finds unpublished rows',
          detail: 'The relay is a separate process. It polls the table, or tails the commit log with CDC, which avoids the polling delay.' },
        { path: ['relay', 'stream'], label: 'publish OrderPlaced', async: true, title: 'Relay publishes to the broker',
          detail: 'The order service has already answered its caller, so none of this adds to its latency.' },
        { path: ['stream', 'relay', 'db'], label: 'ack → published=true', badgeAt: 'db', badge: 'row marked', tone: 'ok', async: true, title: 'Mark the row only after the ack',
          detail: 'The relay marks the row only after the broker has the event. If it marked the row first and then crashed, the event would be lost.' },
        { path: ['stream', 'cons'], label: 'OrderPlaced e17', async: true, title: 'Consumer receives the event',
          detail: 'Each event carries a unique ID, <code>e17</code> here.' },
        { path: ['cons', 'dedup', 'cons'], label: 'INSERT e17 + apply', badgeAt: 'cons', badge: 'shipped', tone: 'ok', async: true, title: 'Apply once, record the ID',
          detail: 'The consumer records the event ID with a unique constraint in the same transaction as its effect, so a replay of <code>e17</code> becomes a no-op.' },
      ],
    },
    {
      id: 'dup', name: 'Relay crash: duplicate',
      summary: 'The relay can publish a row and crash before marking it. That is allowed: the outbox guarantees <b>never lost, never invented</b>, not "exactly once".',
      steps: [
        { path: ['relay', 'stream'], label: 'publish e17', ms: 5, title: 'Relay publishes the event',
          detail: 'The broker acks, and the row is still <code>published=false</code>.' },
        { path: ['stream', 'cons', 'dedup'], label: 'e17 → record + apply', badgeAt: 'dedup', badge: 'e17 stored', tone: 'ok', ms: 10, title: 'First copy is processed',
          detail: 'The consumer ships the order and stores <code>e17</code>.' },
        { at: 'relay', badge: 'crash before UPDATE', tone: 'err', ms: 0, title: 'Relay dies before marking the row',
          detail: 'The publish happened, but the database does not know that.' },
        { path: ['relay', 'db', 'relay'], label: 'restart: still published=false', badgeAt: 'relay', badge: 'e17 again', tone: 'warn', ms: 100, title: 'The restarted relay picks the row up again',
          detail: 'From the relay\'s point of view this row was never sent, so it has to send it. That is how it guarantees no event is lost.' },
        { path: ['relay', 'stream'], label: 're-publish e17', tone: 'warn', ms: 5, title: 'Same event published twice',
          detail: 'The same thing happens with a producer retry after a timeout, or a broker redelivery. Duplicates are normal with at-least-once delivery.' },
        { path: ['stream', 'cons'], label: 'e17 (duplicate)', tone: 'warn', ms: 10, title: 'Consumer gets it again' },
        { path: ['cons', 'dedup', 'cons'], label: 'e17 seen → skip', badgeAt: 'cons', badge: 'no second shipment', tone: 'ok', ms: 1, title: 'Idempotent consumer absorbs it',
          detail: 'The insert of <code>e17</code> hits the unique constraint, so the effect is skipped. The outbox and dedup together make the effect happen once.' },
      ],
    },
  ],
});

/* ======================================================== Kafka ISR / HW == */
const Lisr = lane([
  { label: 'CLIENTS', nodes: [
    { id: 'p', label: 'Producer', sub: 'acks=all', kind: 'client', icon: 'app', row: 0 },
    { id: 'c', label: 'Consumer', sub: 'reads up to HW', kind: 'client', icon: 'worker', row: 1 }] },
  { label: 'PARTITION LEADER', nodes: [
    { id: 'l', label: 'Leader B1', sub: 'tracks ISR and HW', icon: 'kafka-icon', row: 0.5 }] },
  { label: 'FOLLOWERS (PULL)', nodes: [
    { id: 'f2', label: 'Follower B2', sub: 'fetches from leader', icon: 'kafka-icon', row: 0 },
    { id: 'f3', label: 'Follower B3', sub: 'fetches from leader', icon: 'kafka-icon', row: 1 }] },
]);
defineFlow('flow-kafka-isr', {
  title: 'Live flow: Kafka ISR, high watermark and what acks really promise',
  hint: 'Follow one acks=all write to the high watermark, watch a slow replica get dropped, then see acks=1 lose an acknowledged record.',
  zones: Lisr.zones, h: Lisr.h, nodes: Lisr.nodes,
  edges: [['p', 'l'], ['c', 'l'], ['l', 'f2'], ['l', 'f3']],
  scenarios: [
    {
      id: 'all', name: 'acks=all commit',
      summary: 'RF 3 and <code>min.insync.replicas=2</code>. A record is <b>committed</b> when every in-sync replica has it. Only then does the producer get its ack and do consumers see the record.',
      steps: [
        { path: ['p', 'l'], label: 'produce batch (acks=all)', badgeAt: 'l', badge: 'offset 100 · ISR B1 B2 B3', ms: 2, title: 'Leader appends at offset 100',
          detail: 'The leader writes the batch to its own log. It does not push to followers; they come and ask. The ms figures in this flow are rough.' },
        { path: ['f2', 'l', 'f2'], label: 'B2: fetch from 100', badgeAt: 'f2', badge: 'has 100', ms: 2, title: 'B2 pulls the record',
          detail: 'Followers fetch exactly like consumers, from the offset after the last one they hold.' },
        { path: ['f3', 'l', 'f3'], label: 'B3: fetch from 100', badgeAt: 'f3', badge: 'has 100', ms: 2, title: 'B3 pulls the record',
          detail: 'The leader cannot yet tell that either follower has written it.' },
        { path: ['f2', 'l'], label: 'B2: fetch from 101', badgeAt: 'l', badge: 'B2 confirms 100', ms: 1, title: 'The next fetch is the acknowledgement',
          detail: 'Asking for 101 tells the leader that B2 now holds 100. There is no separate ack message.' },
        { path: ['f3', 'l'], label: 'B3: fetch from 101', badgeAt: 'l', badge: 'HW → 101', tone: 'ok', ms: 1, title: 'Every ISR member has it, so it commits',
          detail: 'With all three ISR members at 100, the <b>high watermark</b> moves to 101. This is not a majority vote: all of the current ISR must have the record.' },
        { path: ['l', 'p'], label: 'ack offset 100', tone: 'ok', ms: 1, title: 'Producer is acknowledged',
          detail: 'The ack means at least <code>min.insync.replicas</code> copies exist. With 2, the record survives losing any one broker.' },
        { path: ['c', 'l', 'c'], label: 'fetch → up to HW', badgeAt: 'c', badge: 'sees 100', tone: 'ok', ms: 2, title: 'Consumers read only committed records',
          detail: 'Records above the high watermark are hidden, so a consumer never reads a record that a failover could remove.' },
      ],
    },
    {
      id: 'slow', name: 'Slow ISR member',
      summary: 'Commit latency follows the <b>slowest</b> ISR member, not the median. A stalled follower holds up every acks=all write until it is removed from the ISR.',
      down: ['f3'],
      steps: [
        { path: ['p', 'l'], label: 'produce @101 (acks=all)', ms: 2, title: 'A new batch arrives',
          detail: 'Offset 101, and the ISR is still B1, B2 and B3.' },
        { path: ['f2', 'l', 'f2'], label: 'B2: fetch 101', badgeAt: 'f2', badge: 'has 101', ms: 2, title: 'B2 keeps up' },
        { at: 'f3', badge: 'stalled (GC, disk)', tone: 'warn', ms: 0, title: 'B3 stops fetching',
          detail: 'The broker is alive but slow, for example stuck in a long GC pause or on a saturated disk.' },
        { at: 'l', badge: 'HW stuck at 101', tone: 'warn', ms: 30000, title: 'The ack waits on B3',
          detail: 'B3 is still in the ISR, so 101 is not committed, and every acks=all producer on this partition waits.' },
        { at: 'l', badge: 'ISR → B1 B2', tone: 'warn', ms: 0, title: 'After 30 s, B3 is dropped from the ISR',
          detail: '<code>replica.lag.time.max.ms</code> (30 s) has passed without B3 catching up, so the leader shrinks the ISR.' },
        { path: ['f2', 'l'], label: 'B2: fetch 102', badgeAt: 'l', badge: 'HW → 102', tone: 'ok', ms: 1, title: 'The smaller ISR commits 101' },
        { path: ['l', 'p'], label: 'ack offset 101', tone: 'ok', ms: 1, title: 'Producer unblocks',
          detail: 'Two in-sync replicas still satisfy <code>min.insync.replicas=2</code>. If the ISR fell to 1, the leader would reject acks=all writes instead of silently accepting less durability.' },
      ],
    },
    {
      id: 'acks1', name: 'acks=1 loses data',
      summary: 'With <code>acks=1</code> the producer is acknowledged as soon as the leader has written the record, before any follower has it.',
      steps: [
        { path: ['p', 'l'], label: 'produce @100 (acks=1)', badgeAt: 'l', badge: 'written locally', ms: 2, title: 'Leader appends offset 100',
          detail: 'No follower has fetched it yet.' },
        { path: ['l', 'p'], label: 'ack offset 100', ms: 1, title: 'Producer is told it succeeded',
          detail: 'The application moves on and considers the record safe.' },
        { at: 'l', badge: 'broker dies', tone: 'err', ms: 0, title: 'Leader fails before followers fetch',
          detail: 'Offset 100 exists only on B1\'s disk, and B1 is gone.' },
        { at: 'f2', badge: 'new leader · epoch 6', tone: 'warn', ms: 0, title: 'B2 is elected with a new leader epoch',
          detail: 'B2 was in the ISR, so it is a legal leader. Its log ends at 99, and each leadership term gets a higher epoch (6 here is illustrative).' },
        { path: ['l', 'f2', 'l'], label: 'B1 back: where did epoch 5 end?', badgeAt: 'l', badge: 'truncate offset 100', tone: 'err', ms: 2, title: 'Returning B1 truncates to match',
          detail: 'Using leader epochs (KIP-101), B1 asks the new leader where the previous epoch ended and cuts its log there. <b>The acknowledged write is gone</b>, and consistently gone on every replica.' },
      ],
    },
  ],
});

/* ==================================================================== CDN == */
const Lcdn = lane([
  { label: 'VIEWERS', nodes: [{ id: 'v', label: 'Viewers', sub: 'players worldwide', kind: 'client', icon: 'users' }] },
  { label: 'EDGE POP', nodes: [{ id: 'edge', label: 'Edge POP', sub: 'TLS, key → 1 of N', icon: 'cdn' }] },
  { label: 'MID-TIER', nodes: [{ id: 'mid', label: 'Mid-tier', sub: 'regional cache', icon: 'cache' }] },
  { label: 'SHIELD', nodes: [{ id: 'shield', label: 'Origin shield', sub: 'last cache tier', icon: 'shield' }] },
  { label: 'ORIGIN', nodes: [{ id: 'origin', label: 'Origin', sub: 'store + packager', icon: 'storage' }] },
]);
defineFlow('flow-cdn', {
  title: 'Live flow: a CDN hit, a collapsed cold miss, and stale-if-error',
  hint: 'Follow one video segment through the cache hierarchy: served at the edge, fetched once for a premiere, and served stale when the origin fails.',
  zones: Lcdn.zones, h: Lcdn.h, nodes: Lcdn.nodes,
  edges: [['v', 'edge'], ['edge', 'mid'], ['mid', 'shield'], ['shield', 'origin']],
  scenarios: [
    {
      id: 'hit', name: 'Edge hit',
      summary: 'The common case, roughly 90% of requests in the file\'s example. The viewer is steered to a nearby POP, and the POP serves the segment from its own cache.',
      steps: [
        { path: ['v', 'edge'], label: 'GET seg_42?token=…', ms: 10, title: 'Viewer reaches a nearby POP',
          detail: 'DNS steering returns a POP by resolver location, or anycast lets BGP pick one. TLS terminates here, close to the viewer. The ≈10 ms is illustrative.' },
        { at: 'edge', badge: 'signature ✓ · key excludes token', tone: 'ok', ms: .2, title: 'Check the signed URL, then drop the token from the key',
          detail: 'The edge verifies signature, expiry and path prefix. The token is <b>not</b> part of the cache key; if it were, every viewer would have a different key and the hit ratio would be about 0.' },
        { at: 'edge', badge: 'hash(key) → server 7 of 20', ms: .1, title: 'Hash to one server inside the POP',
          detail: 'Each object is stored once per POP, not once per server: 20 servers × 10 TB hold 200 TB of unique content.' },
        { path: ['edge', 'v'], label: '200 from cache', tone: 'ok', ms: 10, title: 'Served from the edge',
          detail: 'The origin never sees this request.' },
      ],
    },
    {
      id: 'cold', name: 'Cold object: collapsed misses',
      summary: 'The worst moment: a premiere segment that every edge server wants in the same second. <b>Request collapsing</b> at every tier turns thousands of misses into one origin fetch.',
      steps: [
        { path: ['v', 'edge'], label: 'thousands of GETs, same segment', ms: 10, title: 'Everyone asks at once',
          detail: 'The segment is not cached anywhere yet.' },
        { at: 'edge', badge: 'collapse → 1 fetch', tone: 'warn', ms: .1, title: 'Concurrent misses become one',
          detail: 'The first miss for the key goes upstream and the rest wait for it. They share its latency, and they also share its failure.' },
        { path: ['edge', 'mid'], label: 'miss (1 fetch)', tone: 'warn', ms: 20, title: 'Edge asks the mid-tier',
          detail: 'The mid-tier also collapses the same miss arriving from many POPs.' },
        { path: ['mid', 'shield'], label: 'miss (1 fetch)', tone: 'warn', ms: 30, title: 'Mid-tier asks the shield',
          detail: 'Without a shield, 200 POPs each fetch a cold object, which is 200 origin requests instead of 1.' },
        { path: ['shield', 'origin'], label: '1 request', ms: 50, title: 'The origin sees one request',
          detail: 'Without collapsing, 4,000 edge servers × 3.75 MB would be about 15 GB of origin egress in one burst. Here the segment ships once.' },
        { path: ['origin', 'shield', 'mid', 'edge', 'v'], label: 'fill every tier', tone: 'ok', ms: 100, title: 'Every tier fills on the way back',
          detail: 'The next viewer is an edge hit. In steady state, with 90% edge hits and the mid-tier catching 80% of misses, the origin sees 0.1 × 0.2 = 2% of requests.' },
      ],
    },
    {
      id: 'stale', name: 'Origin down: stale-if-error',
      summary: 'A mutable manifest has expired and the origin is returning errors. <b>stale-if-error</b> (RFC 5861) serves the old copy instead of failing the viewer.',
      down: ['origin'],
      steps: [
        { path: ['v', 'edge'], label: 'GET manifest.m3u8', ms: 10, title: 'Player refreshes the manifest',
          detail: 'Manifests are mutable, so they get short TTLs. Segments use immutable versioned URLs and rarely need this.' },
        { path: ['edge', 'mid', 'shield'], label: 'TTL expired → revalidate', tone: 'warn', ms: 50, title: 'The cached copy is stale',
          detail: 'Each tier holds an expired copy and asks upstream whether it is still valid.' },
        { path: ['shield', 'origin', 'shield'], label: 'GET → 5xx', badgeAt: 'shield', badge: 'origin error', tone: 'err', ms: 50, title: 'Origin fails',
          detail: 'The origin is overloaded or down. Passing the 5xx through would make every viewer fail at once.' },
        { at: 'shield', badge: 'serve stale-if-error', tone: 'warn', ms: .1, title: 'Serve the expired copy on purpose',
          detail: 'The response headers allowed stale content for a bounded window when the origin errors. Bounded staleness buys origin protection.' },
        { path: ['shield', 'mid', 'edge', 'v'], label: '200 (stale)', tone: 'ok', ms: 60, title: 'Viewer keeps playing',
          detail: 'The viewer sees a slightly old manifest instead of an error, and the origin gets room to recover.' },
      ],
    },
  ],
});
}
