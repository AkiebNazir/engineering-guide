/* Live request flows (see sd-flow.js for the engine and data format). */
'use strict';
{ // block scope: keeps these lane consts out of the shared global scope

/* ================================================= SQL/15: how Postgres runs a query == */
const Lpq = lane([
  { label: 'CLIENT', nodes: [
    { id: 'client', label: 'psql / driver', sub: 'one connection', kind: 'client', icon: 'cli', row: 0 }] },
  { label: 'PARSE · REWRITE', nodes: [
    { id: 'parser', label: 'Parser', sub: 'syntax + catalog', icon: 'code', row: 0 },
    { id: 'rewriter', label: 'Rewriter', sub: 'expands views', icon: 'edit', row: 1 }] },
  { label: 'PLAN · EXECUTE', nodes: [
    { id: 'planner', label: 'Planner', sub: 'cost model + stats', icon: 'speed', row: 1 },
    { id: 'exec', label: 'Executor', sub: 'node tree, pull', icon: 'process', row: 2 }] },
  { label: 'STORAGE', nodes: [
    { id: 'wal', label: 'WAL', sub: 'fsync at COMMIT', icon: 'logs', row: 1 },
    { id: 'buf', label: 'Buffer cache', sub: 'shared_buffers', kind: 'cache', row: 2 },
    { id: 'heap', label: 'Heap + index', sub: 'pages on disk', icon: 'disk', row: 3 }] },
]);
defineFlow('flow-pg-query', {
  title: 'Live flow: one query through parser, rewriter, planner and executor',
  hint: 'Pick a scenario and follow the query text as it becomes a parse tree, a plan and finally rows. Only the executor ever touches storage.',
  zones: Lpq.zones, h: Lpq.h, nodes: Lpq.nodes,
  edges: [
    ['client', 'parser'], ['parser', 'rewriter'], ['rewriter', 'planner'], ['planner', 'exec'],
    ['exec', 'buf'], ['buf', 'heap'], ['exec', 'wal'], ['exec', 'client'],
  ],
  scenarios: [
    {
      id: 'index', name: 'Indexed point lookup',
      summary: '<code>SELECT * FROM accounts_big WHERE email = \'user123456@example.com\'</code> on 300,000 rows, with <code>idx_accounts_big_email</code> in place (level 10).',
      steps: [
        { path: ['client', 'parser'], label: 'SQL text', ms: .1, title: 'The query string reaches its backend process',
          detail: 'Postgres gives every connection its own backend process, and all four stages run inside it. What arrives is just text; nothing has been checked yet.' },
        { at: 'parser', badge: 'parse tree ✓', ms: .01, title: 'Parser: is this valid SQL, and do these names exist?',
          detail: 'It builds a purely syntactic parse tree and resolves <code>accounts_big</code> and <code>email</code> against the catalog. A typo like <code>SELCT</code> fails here, before any planning.' },
        { path: ['parser', 'rewriter'], label: 'parse tree', ms: .01, title: 'Rewriter: apply rules such as views',
          detail: '<code>accounts_big</code> is a plain table, so there is nothing to expand and the tree passes through unchanged.' },
        { path: ['rewriter', 'planner'], label: 'query tree', ms: 0, title: 'Hand the query to the planner',
          detail: 'The planner now knows <i>what</i> is wanted. Its job is to decide <i>how</i> to get it most cheaply.' },
        { at: 'planner', badge: 'Index Scan · cost 8.44', tone: 'ok', ms: .059, title: 'Planner: compare plans by estimated cost',
          detail: 'A parallel seq scan is estimated at about 6,236 and the index scan at 8.44, using the statistics <code>ANALYZE</code> collected. You never asked for the index; it wins because it is the cheapest option. Planning time: 0.059 ms.' },
        { path: ['planner', 'exec'], label: 'plan tree', ms: 0, title: 'The chosen plan goes to the executor',
          detail: 'This tree is exactly what <code>EXPLAIN</code> prints. Here it is a single node: <code>Index Scan using idx_accounts_big_email</code>.' },
        { path: ['exec', 'buf', 'heap'], label: 'B-tree → heap tuple', badgeAt: 'heap', badge: 'hit=1 read=3', ms: .024,
          title: 'Executor walks the B-tree, then fetches the row',
          detail: 'Only 4 pages are touched: 1 was already in <code>shared_buffers</code> and 3 had to be read in from outside it. Execution time: <b>0.024 ms</b>.' },
        { path: ['exec', 'client'], label: '1 row', tone: 'ok', ms: .1, title: 'Row streams back to the client',
          detail: 'The top plan node pulls rows one at a time from the nodes below it and sends them as they are produced, so nothing is materialized first.' },
      ],
    },
    {
      id: 'seq', name: 'No index: Parallel Seq Scan',
      summary: 'The same query before the index existed. Same rows come back; the planner just has no cheap path.',
      steps: [
        { path: ['client', 'parser'], label: 'same SQL text', ms: .1, title: 'Identical query text arrives',
          detail: 'Parsing and rewriting do not care whether an index exists. Only the planner\'s choice changes.' },
        { path: ['parser', 'rewriter', 'planner'], label: 'query tree', ms: .02, title: 'Parse and rewrite, as before',
          detail: 'Valid syntax, known names, no views. The same tree reaches the planner.' },
        { at: 'planner', badge: 'Gather → Parallel Seq Scan', tone: 'warn', ms: .05, title: 'Planner: the only path is to read every page',
          detail: 'Without an index on <code>email</code>, finding one row means scanning the whole table. With 300,000 rows it is worth planning 1 extra worker process to split the scan. Planning time: 0.050 ms.' },
        { path: ['planner', 'exec'], label: 'Gather + worker', ms: 0, title: 'Executor starts the leader and one worker',
          detail: 'A <code>Gather</code> node sits on top and collects rows from the parallel scan below it. The parallel part is another demand-pull node tree.' },
        { path: ['exec', 'buf'], label: 'scan all pages', badgeAt: 'buf', badge: 'shared hit=3030', ms: 5.8,
          title: 'Read all 3,030 pages, every one already cached',
          detail: 'No disk reads at all, and it is still slow: each process filters out about 150,000 rows to find one match. The cost here is <b>volume</b>, not I/O.' },
        { path: ['exec', 'client'], label: '1 row', tone: 'warn', ms: .1, title: 'Same row, about 244× slower',
          detail: 'Execution time <b>5.865 ms</b> against 0.024 ms with the index. The result is identical; only the path the planner could choose differs.' },
      ],
    },
    {
      id: 'view', name: 'View + UPDATE',
      summary: '<code>UPDATE active_users SET … WHERE id = 42</code>, where <code>active_users</code> is a view over <code>users WHERE status = \'active\'</code>. Writes also go through the WAL.',
      steps: [
        { path: ['client', 'parser'], label: 'UPDATE active_users …', ms: .1, title: 'An UPDATE against a view arrives',
          detail: 'To the parser a view name is just a relation in the catalog, so it resolves fine.' },
        { path: ['parser', 'rewriter'], label: 'parse tree', ms: .01, title: 'Parse tree goes to the rewriter',
          detail: 'This is the stage that knows <code>active_users</code> is a view and not a table.' },
        { at: 'rewriter', badge: '→ users WHERE status=\'active\'', ms: .01, title: 'Rewriter expands the view',
          detail: 'The view reference is replaced by its definition, so the planner only ever sees the real table <code>users</code> with the extra filter added.' },
        { path: ['rewriter', 'planner', 'exec'], label: 'plan', ms: .05, title: 'Plan it like any other query',
          detail: 'The planner picks, for example, a primary-key index scan on <code>users</code>. It has no idea a view was ever involved.' },
        { path: ['exec', 'buf'], label: 'new row version', badgeAt: 'buf', badge: 'page dirty', ms: .02, title: 'Executor writes a new row version',
          detail: 'Constraints are checked as the row is written. Under MVCC an UPDATE adds a new version and marks the old one dead; the change sits in a cached page that is not on disk yet.' },
        { path: ['exec', 'wal'], label: 'WAL record', badgeAt: 'wal', badge: 'fsync at COMMIT', ms: 1, title: 'The change is logged in the WAL first',
          detail: 'COMMIT only returns once the WAL is fsynced (roughly 1 ms, depending on the disk). After a crash, replaying the WAL rebuilds the dirty page, so the page itself can be flushed later.' },
        { path: ['exec', 'client'], label: 'UPDATE 1', tone: 'ok', ms: .1, title: 'Client sees UPDATE 1',
          detail: 'The row count comes from the executor. Durability comes from the WAL fsync, not from the data page reaching disk.' },
      ],
    },
  ],
});

/* ================================================= SQL/09: the lost update and its fixes == */
const Llu = lane([
  { label: 'SESSIONS', nodes: [
    { id: 'a', label: 'Session A', sub: 'withdraw 10', kind: 'client', icon: 'app', row: 0 },
    { id: 'b', label: 'Session B', sub: 'withdraw 10', kind: 'client', icon: 'app', row: 2 }] },
  { label: 'BACKENDS', nodes: [
    { id: 'beA', label: 'Backend A', sub: 'READ COMMITTED', icon: 'process', row: 0 },
    { id: 'beB', label: 'Backend B', sub: 'READ COMMITTED', icon: 'process', row: 2 }] },
  { label: 'ROW LOCK', nodes: [
    { id: 'lock', label: 'Row lock', sub: 'accounts id=1', icon: 'lock', row: 1 }] },
  { label: 'TABLE', nodes: [
    { id: 'row', label: 'accounts', sub: 'id=1 · balance', kind: 'db', icon: 'table', row: 1 }] },
]);
defineFlow('flow-lost-update', {
  title: 'Live flow: two withdrawals race on one balance',
  hint: 'Balance starts at 100 and two sessions each withdraw 10. Watch where each session reads, where it waits, and which value finally lands.',
  zones: Llu.zones, h: Llu.h, nodes: Llu.nodes,
  edges: [
    ['a', 'beA'], ['b', 'beB'], ['beA', 'lock'], ['beB', 'lock'], ['lock', 'row'],
    ['beA', 'row'], ['beB', 'row'],
  ],
  scenarios: [
    {
      id: 'race', name: 'Race: 100 → 90, not 80',
      summary: 'Plain read-modify-write with no locking: <code>SELECT balance</code>, compute in the app, then <code>UPDATE … SET balance = &lt;computed&gt;</code>. Real result: final balance <b>90</b>.',
      steps: [
        { path: ['a', 'beA', 'row'], label: 'SELECT balance', badgeAt: 'row', badge: '100', ms: 1, title: 'A reads the balance',
          detail: 'A plain SELECT reads from an MVCC snapshot and takes no row lock, so nothing stops B from reading the same row at the same moment.' },
        { path: ['b', 'beB', 'row'], label: 'SELECT balance', badgeAt: 'row', badge: '100', ms: 1, title: 'B reads the same balance',
          detail: 'Both sessions now hold 100 in application memory. The demo forces this interleaving with a barrier so that both read before either writes.' },
        { at: 'a', badge: '100 − 10 = 90', ms: 200, title: 'A computes the new balance in the app',
          detail: 'The arithmetic happens outside the database, on a value that is about to be stale. The demo sleeps 0.2 s here to widen the window.' },
        { at: 'b', badge: '100 − 10 = 90', ms: 0, title: 'B computes the same number',
          detail: 'Both sessions intend to write the literal value 90.' },
        { path: ['a', 'beA', 'lock', 'row'], label: 'UPDATE … = 90', badgeAt: 'lock', badge: 'held by A', ms: 1, title: 'A updates, which takes the row lock',
          detail: 'Every UPDATE locks the row it changes until the transaction ends. The lock is real, but it arrives too late: A\'s 90 was computed from an unlocked read.' },
        { path: ['b', 'beB', 'lock'], label: 'UPDATE … = 90', tone: 'warn', badgeAt: 'lock', badge: 'B waits', ms: 1, title: 'B\'s UPDATE queues behind A\'s lock',
          detail: 'Writers block writers on the same row. B waits, but only to write its own stale value a little later.' },
        { path: ['a', 'beA', 'lock'], label: 'COMMIT', badgeAt: 'lock', badge: 'released', ms: 1, title: 'A commits: balance is 90',
          detail: 'The lock is released at COMMIT and B\'s blocked UPDATE wakes up.' },
        { path: ['lock', 'row'], label: 'B writes 90', tone: 'err', badgeAt: 'row', badge: '90, expected 80', ms: 1, title: 'Lost update: B overwrites with 90',
          detail: 'B\'s statement sets a <b>literal</b> 90, so writing it again changes nothing. One withdrawal silently vanished, at the default <code>READ COMMITTED</code> level.' },
      ],
    },
    {
      id: 'forupdate', name: 'SELECT … FOR UPDATE',
      summary: 'The fix from Demo 1: take the row lock <b>when reading</b>, so the second session waits before it reads. Real result: final balance <b>80</b>.',
      steps: [
        { path: ['a', 'beA', 'lock', 'row'], label: 'SELECT … FOR UPDATE', badgeAt: 'lock', badge: 'held by A', ms: 1, title: 'A reads 100 and locks the row',
          detail: 'The row lock is held until A commits or rolls back. Which session gets there first is just timing; in the Python run it happened to be B.' },
        { path: ['b', 'beB', 'lock'], label: 'SELECT … FOR UPDATE', tone: 'warn', badgeAt: 'lock', badge: 'B blocks', ms: 1, title: 'B\'s locking read blocks',
          detail: 'This is the key difference from the race: B waits <b>before</b> reading, so it cannot compute anything from a value that is about to change.' },
        { path: ['a', 'beA', 'lock', 'row'], label: 'UPDATE = 90; COMMIT', badgeAt: 'row', badge: '90', ms: 200, title: 'A writes 90 and commits',
          detail: 'A does its application logic (the demo sleeps 0.2 s), writes and commits. The commit releases the lock.' },
        { path: ['lock', 'beB', 'b'], label: 'balance = 90', badgeAt: 'b', badge: 'reads 90', ms: 1, title: 'B wakes up and reads the post-commit value',
          detail: 'Under <code>READ COMMITTED</code>, a <code>FOR UPDATE</code> that had to wait returns the newest committed version of the row: 90, not the stale 100.' },
        { at: 'b', badge: '90 − 10 = 80', ms: 1, title: 'B computes from fresh data', detail: 'Same code as the race, but now its input is correct.' },
        { path: ['b', 'beB', 'lock', 'row'], label: 'UPDATE = 80; COMMIT', tone: 'ok', badgeAt: 'row', badge: '80 ✓', ms: 1, title: 'Both withdrawals land',
          detail: 'Final balance 80. The row lock enforces this at any isolation level; you did not need <code>SERIALIZABLE</code>.' },
      ],
    },
    {
      id: 'atomic', name: 'Atomic conditional UPDATE',
      summary: 'Defense #1 on the list: do the read and write in <b>one</b> statement, <code>UPDATE accounts SET balance = balance - 10 WHERE id = 1 AND balance &gt;= 10</code>.',
      steps: [
        { path: ['a', 'beA', 'lock', 'row'], label: 'balance = balance − 10', badgeAt: 'row', badge: '90', ms: 1, title: 'A runs the single-statement update',
          detail: 'The new value is computed from the row inside the database, while A holds the lock. There is no gap between reading and writing for anyone to slip into.' },
        { path: ['b', 'beB', 'lock'], label: 'same UPDATE', tone: 'warn', badgeAt: 'lock', badge: 'B waits', ms: 1, title: 'B\'s identical statement waits for A',
          detail: 'Both statements want the same row lock, so they run one after the other.' },
        { path: ['a', 'beA', 'lock'], label: 'COMMIT', badgeAt: 'lock', badge: 'released', ms: 1, title: 'A commits',
          detail: 'The lock passes to B.' },
        { path: ['lock', 'row'], label: 're-check WHERE on 90', badgeAt: 'row', badge: '80', tone: 'ok', ms: 1, title: 'B re-evaluates against the new row',
          detail: 'After waiting, Postgres re-checks <code>balance &gt;= 10</code> against the committed 90 and computes <code>balance - 10</code> from it. The result is 80, not 90.' },
        { path: ['row', 'beB', 'b'], label: 'UPDATE 1', tone: 'ok', ms: 1, title: 'Check the affected row count',
          detail: '<code>UPDATE 1</code> means the withdrawal happened. <code>UPDATE 0</code> would mean the balance was too low, so the app must check the count instead of assuming success.' },
      ],
    },
  ],
});

/* ================================================= SQL/13: connection pooling and PgBouncer == */
const Lpo = lane([
  { label: 'APP PROCESS', nodes: [
    { id: 'app', label: 'App worker', sub: 'handles a request', kind: 'client', icon: 'app', row: 0 },
    { id: 'pool', label: 'psycopg_pool', sub: '4 open connections', kind: 'cache', icon: 'layers', row: 1 }] },
  { label: 'PROXY', nodes: [
    { id: 'bouncer', label: 'PgBouncer', sub: 'transaction mode', icon: 'proxy', row: 2 }] },
  { label: 'POSTGRES', nodes: [
    { id: 'beN', label: 'New backend', sub: 'forked per connect', icon: 'process', row: 0 },
    { id: 'be1', label: 'Backend #1', sub: 'long-lived process', icon: 'process', row: 1 },
    { id: 'be2', label: 'Backend #2', sub: 'long-lived process', icon: 'process', row: 2 }] },
]);
defineFlow('flow-pg-pooling', {
  title: 'Live flow: a new connection per request vs a pool vs PgBouncer',
  hint: 'Every Postgres connection is a forked OS process. Compare paying for one per request, borrowing one from an in-process pool, and sharing backends through PgBouncer.',
  zones: Lpo.zones, h: Lpo.h, nodes: Lpo.nodes,
  edges: [
    ['app', 'beN'], ['app', 'pool'], ['pool', 'be1'],
    ['app', 'bouncer'], ['bouncer', 'be1'], ['bouncer', 'be2'],
  ],
  scenarios: [
    {
      id: 'new', name: 'New connection per request',
      summary: 'Open, run <code>SELECT 1</code>, close, 50 times. Measured on localhost with no TLS: <b>3.88 ms per request</b>. The per-step split below is approximate.',
      steps: [
        { path: ['app', 'beN'], label: 'TCP connect + startup', ms: .5, title: 'Connect to Postgres',
          detail: 'A TCP handshake plus the startup message reach the postmaster, Postgres\'s listening process (≈0.5 ms here). Over a real network, and with TLS on, this alone costs one or more round trips.' },
        { at: 'beN', badge: 'fork()', ms: 1, title: 'The postmaster forks a new backend process',
          detail: 'Postgres gives every connection its own OS process, not a thread, and hands it the socket. Creating that process is real work for the kernel (roughly 1 ms here).' },
        { path: ['beN', 'app'], label: 'auth OK · ready', ms: 1.5, title: 'Authentication and session setup',
          detail: 'Password check, loading catalog caches, applying session defaults: roughly 1.5 ms. All of it is thrown away when the connection closes.' },
        { path: ['app', 'beN', 'app'], label: 'SELECT 1', ms: .6, title: 'The query itself',
          detail: 'The part you actually wanted is a small slice of the total.' },
        { path: ['app', 'beN'], label: 'close', tone: 'warn', badgeAt: 'beN', badge: 'process exits', ms: .28, title: 'Close: the backend process exits',
          detail: 'Total <b>3.88 ms</b> per request, and the next request pays all of it again.' },
      ],
    },
    {
      id: 'pool', name: 'Pooled (psycopg_pool)',
      summary: '<code>ConnectionPool(min_size=4, max_size=4)</code> inside the app process. Same 50 requests: <b>0.50 ms per request, 7.8× faster</b>.',
      steps: [
        { at: 'pool', badge: '4 conns ready', ms: 0, title: 'The pool opened its connections at startup',
          detail: 'Connect, fork and authenticate were paid 4 times, once, before the first request. <code>pool.wait()</code> blocks until they are ready.' },
        { path: ['app', 'pool'], label: 'borrow', ms: .05, title: 'Borrow an already-open connection',
          detail: '<code>with pool.connection() as conn:</code> takes an idle one from memory: no network and no fork.' },
        { path: ['pool', 'be1'], label: 'SELECT 1', ms: .2, title: 'Query on a warm backend',
          detail: 'Backend #1 already exists with its caches loaded, so only the query runs.' },
        { path: ['be1', 'pool'], label: '1 row', ms: .2, title: 'Result comes back',
          detail: 'The connection stays open after the query; only its ownership changes.' },
        { path: ['pool', 'app'], label: 'row · conn returned', tone: 'ok', ms: .05, title: 'Connection goes back to the pool',
          detail: 'Leaving the <code>with</code> block returns it. <b>0.50 ms</b> per request, and on a real network with TLS the gap would be far larger.' },
      ],
    },
    {
      id: 'bouncer', name: 'PgBouncer transaction-mode gotcha',
      summary: 'PgBouncer lets many clients share a few real backends by handing a backend out <b>per transaction</b>. Anything stored in the session does not follow you.',
      steps: [
        { path: ['app', 'bouncer'], label: 'SET search_path = tenant_a', ms: .1, title: 'The app sets session state',
          detail: 'A plain <code>SET</code> outside <code>BEGIN</code> is its own one-statement transaction. The app assumes the setting now sticks to "its" connection.' },
        { path: ['bouncer', 'be1'], label: 'runs on backend #1', badgeAt: 'be1', badge: 'search_path = tenant_a', ms: .2, title: 'PgBouncer runs it on backend #1',
          detail: 'The setting is stored in backend #1\'s session, which is not the app\'s session.' },
        { at: 'bouncer', badge: '#1 back in pool', ms: 0, title: 'Transaction over, backend returned',
          detail: 'In transaction mode the backend goes back to PgBouncer\'s pool the moment the transaction ends. This is how 50 app processes share a handful of real backends.' },
        { path: ['app', 'bouncer'], label: 'SELECT * FROM orders', ms: .1, title: 'Next statement from the same app',
          detail: 'From the app\'s side it is the same connection. PgBouncer is free to choose any idle backend.' },
        { path: ['bouncer', 'be2'], label: 'runs on backend #2', tone: 'warn', ms: .2, title: 'It lands on a different backend',
          detail: 'Backend #2 never saw the <code>SET</code>.' },
        { at: 'be2', badge: 'default search_path', tone: 'err', ms: 0, title: 'Wrong schema, silently',
          detail: 'The query reads the default schema\'s <code>orders</code>, or fails if there is none. <code>PREPARE</code>d statements and advisory locks break the same way.' },
        { at: 'be1', badge: 'tenant_a leaks', tone: 'err', ms: 0, title: 'Meanwhile backend #1 still carries the setting',
          detail: 'The next client to borrow backend #1 inherits <code>tenant_a</code>. Fix it with <code>SET LOCAL</code> inside a transaction, or use session mode for code that needs session state.' },
      ],
    },
  ],
});

/* ================================================= SQL/17: replication and failover == */
const Lha = lane([
  { label: 'APP', nodes: [
    { id: 'app', label: 'App', sub: 'writes + reads', kind: 'client', icon: 'app', row: 1 }] },
  { label: 'ROUTING', nodes: [
    { id: 'proxy', label: 'Proxy / VIP', sub: 'finds the primary', icon: 'proxy', row: 1 }] },
  { label: 'DATABASES', nodes: [
    { id: 'primary', label: 'Primary', sub: 'Postgres · writes', kind: 'db', icon: 'postgresql', row: 0 },
    { id: 'replica', label: 'Replica', sub: 'replays WAL', kind: 'db', icon: 'replica', row: 2 }] },
  { label: 'HA CONTROL', nodes: [
    { id: 'patroni', label: 'Patroni', sub: 'agents + DCS', icon: 'sync', row: 1 }] },
]);
defineFlow('flow-pg-ha', {
  title: 'Live flow: async commit, sync commit and a real failover',
  hint: 'Replication is shipping the WAL to a second server. Failover is separate tooling: something must detect, promote and reroute. Pick a scenario.',
  zones: Lha.zones, h: Lha.h, nodes: Lha.nodes,
  edges: [
    ['app', 'proxy'], ['proxy', 'primary'], ['proxy', 'replica'],
    ['primary', 'replica', { async: true }], ['patroni', 'primary'], ['patroni', 'replica'],
  ],
  scenarios: [
    {
      id: 'async', name: 'Async commit (default)',
      summary: 'Postgres\'s default: COMMIT returns as soon as the <b>primary</b> has the WAL on disk. The replica catches up afterwards.',
      steps: [
        { path: ['app', 'proxy', 'primary'], label: 'INSERT; COMMIT', ms: 1, title: 'Write goes to the primary',
          detail: 'All writes go to the single primary. The proxy exists so the app never hard-codes which server that is.' },
        { at: 'primary', badge: 'WAL fsync', ms: 1, title: 'Primary makes the commit durable locally',
          detail: 'The WAL record is fsynced before COMMIT is reported. This is the same WAL used for crash recovery, and it is also what gets shipped to replicas.' },
        { path: ['primary', 'proxy', 'app'], label: 'COMMIT ok', tone: 'ok', ms: 1, title: 'Client is told "committed"',
          detail: 'The replica has nothing yet. If the primary died right now, this commit would be missing from any replica you promoted.' },
        { path: ['app', 'proxy', 'replica'], label: 'SELECT (read replica)', tone: 'warn', badgeAt: 'replica', badge: 'row not there yet', ms: 1,
          title: 'An immediate read from the replica is stale',
          detail: 'Read-your-writes is not automatic across servers. Fixes: send this user\'s reads to the primary for a short window, or wait until the replica has reached the write\'s LSN.' },
        { path: ['primary', 'replica'], label: 'WAL stream', async: true, badgeAt: 'replica', badge: 'lag ≈26 ms', title: 'The WAL arrives and is replayed',
          detail: 'Measured lag in this level: about 26 ms from Python and 2.5 ms from Go. Expect single-digit to tens of milliseconds, growing under load.' },
        { path: ['app', 'proxy', 'replica'], label: 'SELECT again', tone: 'ok', badgeAt: 'replica', badge: 'row visible', ms: 1, title: 'Now the replica has it',
          detail: 'Same query, a few milliseconds later. Async replication is eventually consistent for reads.' },
      ],
    },
    {
      id: 'sync', name: 'Synchronous commit',
      summary: '<code>synchronous_standby_names</code> set on the primary: a commit <b>waits</b> for a named replica to confirm the WAL.',
      steps: [
        { path: ['app', 'proxy', 'primary'], label: 'INSERT; COMMIT', ms: 1, title: 'Same write, same primary', detail: 'Nothing changes on the app side.' },
        { at: 'primary', badge: 'WAL fsync', ms: 1, title: 'Local WAL flush', detail: 'Still required, but no longer enough to answer the client.' },
        { path: ['primary', 'replica'], label: 'WAL', ms: 2, title: 'Ship the WAL and wait',
          detail: 'The commit is held open while the WAL crosses the network (≈2 ms here; far more across zones or regions).' },
        { path: ['replica', 'primary'], label: 'flushed up to LSN', ms: 2, title: 'Replica confirms',
          detail: 'Whether it confirms on receive, on flush or on replay depends on <code>synchronous_commit</code>. Stricter settings cost more latency.' },
        { path: ['primary', 'proxy', 'app'], label: 'COMMIT ok', tone: 'ok', ms: 1, title: 'Only now is the client told',
          detail: 'A promoted replica can never be missing a commit the client saw succeed. The price is a network round trip on every write.' },
        { at: 'replica', badge: 'if down: commits wait', tone: 'warn', ms: 0, title: 'The other side of the trade',
          detail: 'If the synchronous replica is unreachable, commits on the primary stall. Writes now depend on the replica\'s health too.' },
      ],
    },
    {
      id: 'failover', name: 'Failover',
      summary: 'Postgres does not fail over by itself. Patroni (or repmgr, or a managed service) provides the <b>detect → promote → reconfigure</b> steps.',
      steps: [
        { at: 'primary', badge: 'crash', tone: 'err', ms: 0, title: 'The primary dies',
          detail: 'Writes start failing. Plain Postgres just waits; the replica keeps its read-only role.' },
        { path: ['patroni', 'primary'], label: 'health check ✗', tone: 'warn', ms: 10000, title: 'Detection: is it really down?',
          detail: 'The primary must keep renewing a leader key in a consensus store (the DCS). The key has to expire first, which takes seconds (≈10 s here), so that a network partition is not mistaken for a crash and two primaries never exist (split brain).' },
        { path: ['patroni', 'replica'], label: 'pg_ctl promote', ms: 500, title: 'Promotion',
          detail: 'The replica stops replaying WAL and starts accepting writes. With async replication, commits still inside the lag window are lost here.' },
        { at: 'replica', badge: 'new primary', tone: 'ok', ms: 0, title: 'One writable server again',
          detail: 'A physical replica is read-only until promoted because it cannot replay someone else\'s WAL and take its own writes at the same time.' },
        { path: ['proxy', 'replica'], label: 'who is primary now?', ms: 100, title: 'Reconfiguration',
          detail: 'The routing layer learns the new address (a proxy health check, a moved virtual IP or updated DNS). App code does not need to know a failover happened.' },
        { path: ['app', 'proxy', 'replica'], label: 'writes resume', tone: 'ok', ms: 2, title: 'Writes flow again',
          detail: 'The outage lasted roughly detection plus promotion plus reconfiguration, and detection is by far the longest part.' },
        { at: 'primary', badge: 'back → resync / rebuild', tone: 'warn', ms: 0, title: 'The old primary returns',
          detail: 'It may hold WAL the new primary never received, so it must be resynced or rebuilt as a replica, never simply restarted as a second writer.' },
      ],
    },
  ],
});

/* ================================================= Redis/08: distributed lock release == */
const Lrk = lane([
  { label: 'CLIENTS', nodes: [
    { id: 'a', label: 'Client A', sub: 'token tokA', kind: 'client', icon: 'worker', row: 0 },
    { id: 'b', label: 'Client B', sub: 'token tokB', kind: 'client', icon: 'worker', row: 2 }] },
  { label: 'LOCK', nodes: [
    { id: 'redis', label: 'Redis', sub: 'key lock:job', kind: 'cache', row: 1 }] },
  { label: 'RESOURCE', nodes: [
    { id: 'res', label: 'Protected resource', sub: 'one writer at a time', kind: 'db', row: 1 }] },
]);
defineFlow('flow-redis-lock', {
  title: 'Live flow: acquiring and releasing a Redis lock safely',
  hint: 'The lock is one key set with NX and a TTL, holding a random token. Watch what goes wrong when a paused client wakes up after its TTL has expired.',
  zones: Lrk.zones, h: Lrk.h, nodes: Lrk.nodes,
  edges: [['a', 'redis'], ['b', 'redis'], ['a', 'res'], ['b', 'res']],
  scenarios: [
    {
      id: 'happy', name: 'Safe acquire and release',
      summary: '<code>SET lock:job &lt;token&gt; NX PX 5000</code> to acquire, and a Lua compare-and-delete to release.',
      steps: [
        { path: ['a', 'redis'], label: 'SET … tokA NX PX 5000', badgeAt: 'redis', badge: 'OK', tone: 'ok', ms: .5, title: 'A acquires the lock',
          detail: '<code>NX</code> makes it set only if the key is absent, in one atomic command, so there is no check-then-set race. <code>PX 5000</code> is a safety net if A crashes. The random token identifies this acquisition.' },
        { path: ['b', 'redis'], label: 'SET … tokB NX PX 5000', badgeAt: 'redis', badge: 'nil', tone: 'warn', ms: .5, title: 'B tries and is refused',
          detail: 'The key already exists, so <code>NX</code> fails. B can retry later or skip the job.' },
        { path: ['a', 'res'], label: 'do the work', ms: 100, title: 'A does the protected work',
          detail: 'This must finish well inside the 5 s TTL (≈100 ms here). Size the TTL with real margin, or renew it for long jobs.' },
        { path: ['a', 'redis'], label: 'EVAL compare-and-delete tokA', badgeAt: 'redis', badge: '1 · released', tone: 'ok', ms: .5, title: 'A releases only its own lock',
          detail: 'The Lua script runs <code>GET</code>, compares with <code>tokA</code>, then <code>DEL</code>, all as one atomic unit inside Redis. It returns 1 because the key still holds A\'s token.' },
      ],
    },
    {
      id: 'del', name: 'GC pause + plain DEL',
      summary: 'The bug this section warns about: releasing with <code>DEL lock:job</code> after the TTL has already expired.',
      steps: [
        { path: ['a', 'redis'], label: 'SET … tokA NX PX 5000', badgeAt: 'redis', badge: 'OK', ms: .5, title: 'A acquires the lock', detail: 'Same as the happy path.' },
        { at: 'a', badge: 'GC pause ≈6 s', tone: 'warn', ms: 6000, title: 'A freezes longer than the TTL',
          detail: 'A garbage-collection pause, a network stall or the OS descheduling the process. A cannot notice time passing while it is frozen.' },
        { at: 'redis', badge: 'TTL expired · key gone', ms: 0, title: 'Redis expires the lock',
          detail: 'The safety net works as designed: Redis cannot tell a crashed holder from a paused one.' },
        { path: ['b', 'redis'], label: 'SET … tokB NX PX 5000', badgeAt: 'redis', badge: 'OK', tone: 'ok', ms: .5, title: 'B legitimately acquires it',
          detail: 'The key was absent, so <code>NX</code> succeeds. B now correctly holds the lock.' },
        { path: ['b', 'res'], label: 'B works', ms: 1, title: 'B starts the protected work', detail: 'As far as B knows, it is the only holder, and it is right.' },
        { path: ['a', 'redis'], label: 'DEL lock:job', tone: 'err', badgeAt: 'redis', badge: 'deleted B\'s lock', ms: .5, title: 'A wakes up and deletes B\'s lock',
          detail: 'Plain <code>DEL</code> does not check whose lock it is. The key is now free while B is still working, so a third client can acquire it and two clients believe they hold the lock.' },
      ],
    },
    {
      id: 'fence', name: 'Safe release + fencing token',
      summary: 'The same pause, with a compare-and-delete release <b>and</b> a fencing token checked by the resource itself.',
      steps: [
        { path: ['a', 'redis'], label: 'acquire · token 33', badgeAt: 'redis', badge: 'OK', ms: .5, title: 'A acquires the lock and a number',
          detail: 'A fencing token is a strictly increasing number handed out with each acquisition, from a counter in a linearizable store. Plain <code>SET NX</code> does not return one.' },
        { at: 'a', badge: 'GC pause ≈6 s', tone: 'warn', ms: 6000, title: 'A pauses past the TTL', detail: 'Exactly the same failure as before.' },
        { at: 'redis', badge: 'TTL expired', ms: 0, title: 'The lock expires', detail: 'Nothing on the Redis side has changed.' },
        { path: ['b', 'redis'], label: 'acquire · token 34', badgeAt: 'redis', badge: 'OK', ms: .5, title: 'B acquires with a higher token', detail: 'Every new holder gets a larger number.' },
        { path: ['b', 'res'], label: 'write · token 34', badgeAt: 'res', badge: 'highest seen: 34', tone: 'ok', ms: 1, title: 'The resource records token 34',
          detail: 'The resource remembers the highest token it has accepted.' },
        { path: ['a', 'res'], label: 'write · token 33', tone: 'err', badgeAt: 'res', badge: 'rejected: 33 < 34', ms: 1, title: 'A\'s late write is refused by the resource',
          detail: 'A still believes it holds the lock. The resource, not the lock, rejects the stale token. Neither single-node <code>SET NX</code> nor Redlock can prevent this late write on its own.' },
        { path: ['a', 'redis'], label: 'compare-and-delete tokA', badgeAt: 'redis', badge: '0 · refused', tone: 'ok', ms: .5, title: 'A\'s release leaves B\'s lock alone',
          detail: 'The key now holds <code>tokB</code>, so the script returns 0 and deletes nothing. The safe release protects B\'s lock; the fencing token protects the data.' },
      ],
    },
  ],
});

/* ================================================= MongoDB/10: write concern == */
const Lwc = lane([
  { label: 'CLIENT', nodes: [
    { id: 'drv', label: 'Driver', sub: 'pymongo / Go', kind: 'client', icon: 'app', row: 1 }] },
  { label: 'PRIMARY', nodes: [
    { id: 'p', label: 'Primary', sub: 'MongoDB · oplog', kind: 'db', icon: 'mongodb-icon', row: 1 }] },
  { label: 'SECONDARIES', nodes: [
    { id: 's1', label: 'Secondary 1', sub: 'tails the oplog', kind: 'db', icon: 'replica', row: 0 },
    { id: 's2', label: 'Secondary 2', sub: 'tails the oplog', kind: 'db', icon: 'replica', row: 2 }] },
]);
defineFlow('flow-mongo-wc', {
  title: 'Live flow: what a write concern actually waits for',
  hint: 'A 3-member replica set rs0. The write is applied on the primary either way; w only decides how many members must have it before the driver hears "done". Multi-node timings are approximate.',
  zones: Lwc.zones, h: Lwc.h, nodes: Lwc.nodes,
  edges: [['drv', 'p'], ['p', 's1', { async: true }], ['p', 's2', { async: true }]],
  scenarios: [
    {
      id: 'w1', name: 'w: 1',
      summary: 'Acknowledged as soon as the <b>primary alone</b> has the write. Fastest, and the write can still be lost.',
      steps: [
        { path: ['drv', 'p'], label: 'insertOne · w:1', ms: 1, title: 'Driver sends the insert',
          detail: 'Every write goes to the primary. <code>w</code> travels with the operation; it is a per-operation choice.' },
        { at: 'p', badge: 'applied + oplog entry', ms: .2, title: 'Primary applies the write',
          detail: 'The document is written and an entry is appended to the oplog, the log secondaries copy from.' },
        { path: ['p', 'drv'], label: 'ack', tone: 'ok', ms: 1, title: 'Acknowledged immediately',
          detail: 'With <code>w: 1</code> the primary does not wait for anyone else. The secondaries will copy the oplog asynchronously, a few milliseconds later if all goes well.' },
        { at: 'p', badge: 'crash before replication', tone: 'err', ms: 0, title: 'The primary dies first',
          detail: 'Neither secondary has copied the new oplog entry yet. The client already believes the write succeeded.' },
        { at: 's1', badge: 'elected primary', tone: 'warn', ms: 0, title: 'The survivors elect a new primary',
          detail: 'Typically within a handful of seconds, using a Raft-like election. The new primary has never seen the write.' },
        { at: 'p', badge: 'rejoins → write rolled back', tone: 'err', ms: 0, title: 'The acknowledged write is gone',
          detail: 'When the old primary comes back as a secondary, its unreplicated write is rolled back to match the new primary. "Acknowledged" meant only "one node had it".' },
      ],
    },
    {
      id: 'wmaj', name: 'w: "majority"',
      summary: 'Acknowledged once a <b>majority of voting members</b> (2 of 3) have the write. It costs a network round trip and survives any single-node failure.',
      steps: [
        { path: ['drv', 'p'], label: 'insertOne · w:majority', ms: 1, title: 'Same insert, stronger concern',
          detail: 'The primary applies the write exactly as with <code>w: 1</code>. Only the waiting differs.' },
        { at: 'p', badge: 'applied · waiting for 1 more', ms: .2, title: 'Primary has 1 of the 2 it needs',
          detail: 'A majority of 3 voting members is 2, and the primary counts as one of them.' },
        { path: ['p', 's1'], label: 'oplog entry', ms: 1.5, title: 'Secondary 1 copies the oplog entry',
          detail: 'This network hop is the extra cost (≈1–2 ms in one zone, much more across regions). The single-node lab could not show it: there, "majority" was the one node itself.' },
        { path: ['s1', 'p'], label: 'replicated + journaled', badgeAt: 'p', badge: '2 of 3 ✓', ms: 1.5, title: 'Majority reached',
          detail: 'The lab config has <code>writeConcernMajorityJournalDefault: true</code>, so members count only once the write is in their on-disk journal.' },
        { path: ['p', 'drv'], label: 'ack', tone: 'ok', ms: 1, title: 'Acknowledged: survives failover',
          detail: 'Any majority that could elect a new primary includes a member that has this write, so no single failure, including the primary\'s, can lose it.' },
        { path: ['p', 's2'], label: 'oplog entry', async: true, title: 'Secondary 2 catches up later',
          detail: 'Nobody waited for the third member. <code>w: "majority"</code> means a majority, not all of them.' },
      ],
    },
    {
      id: 'w2', name: 'w: 2 on the lab\'s 1-node set',
      down: ['s1', 's2'],
      summary: 'The real lab result: the lab\'s replica set has only <b>one</b> member (the secondaries are greyed out), and the write asks for 2 acknowledgements.',
      steps: [
        { path: ['drv', 'p'], label: 'insertOne · w:2, wtimeout 2000', ms: .2, title: 'Ask for 2 acknowledging members',
          detail: '<code>WriteConcern(w=2, wtimeout=2000)</code>: wait for 2 data-bearing members, giving up after 2 s.' },
        { at: 'p', badge: 'write applied', ms: .1, title: 'The primary applies the write anyway',
          detail: 'Write concern controls acknowledgement, not whether the write happens. The primary always applies it to its own data first.' },
        { at: 'p', badge: 'only 1 data-bearing node', tone: 'err', ms: .1, title: 'The concern can never be met',
          detail: 'Because the server knows this immediately, it does not wait for <code>wtimeout</code>. A concern that could be met but is not met in time returns <code>WTimeoutError</code> instead.' },
        { path: ['p', 'drv'], label: 'UnsatisfiableWriteConcern', tone: 'err', ms: .2, title: 'Rejected after 0.6 ms',
          detail: 'Error code 100, "Not enough data-bearing nodes". Python and Go see the same server-side check.' },
        { at: 'p', badge: 'doc who=w2 present', tone: 'warn', ms: 0, title: 'Yet the document is in the collection',
          detail: 'A write-concern error or timeout is <b>not</b> a rollback. During an incident, do not assume such an error means the data did not change.' },
      ],
    },
  ],
});
}
