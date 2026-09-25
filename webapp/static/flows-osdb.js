/* Live request flows (see sd-flow.js for the engine and data format). */
'use strict';
{ // block scope: keeps the Los* layout constants out of the shared global scope

/* ================================================= page fault (CS/01 §5) == */
const LosPF = lane([
  { label: 'USER SPACE', nodes: [
    { id: 'proc', label: 'Process', sub: 'loads a virtual addr', kind: 'client', icon: 'process', row: 0 }] },
  { label: 'CPU · MMU', nodes: [
    { id: 'tlb', label: 'TLB', sub: 'recent translations', kind: 'cache', icon: 'cache', row: 0 },
    { id: 'pt', label: 'Page table', sub: '4 levels (5 w/ LA57)', icon: 'layers', row: 1 }] },
  { label: 'KERNEL', nodes: [
    { id: 'fault', label: 'Fault handler', sub: 'page-fault trap', icon: 'alert', row: 1 },
    { id: 'pcache', label: 'Page cache', sub: 'file pages in RAM', kind: 'cache', icon: 'cache', row: 2 }] },
  { label: 'HARDWARE', nodes: [
    { id: 'ram', label: 'RAM', sub: 'physical frames', kind: 'db', icon: 'memory', row: 0 },
    { id: 'disk', label: 'Disk / swap', sub: 'SSD or HDD', kind: 'db', icon: 'disk', row: 2 }] },
]);
defineFlow('flow-page-fault', {
  title: 'Live flow: from virtual address to physical memory',
  hint: 'Follow one memory access: a TLB hit, a TLB miss with a page walk, a copy-on-write minor fault after fork(), and a major fault that has to go to disk.',
  zones: LosPF.zones, h: LosPF.h, nodes: LosPF.nodes,
  edges: [
    ['proc', 'tlb'], ['tlb', 'ram'], ['tlb', 'pt'], ['pt', 'fault'],
    ['fault', 'ram'], ['fault', 'pcache'], ['pcache', 'disk'],
  ],
  scenarios: [
    {
      id: 'tlb', name: 'TLB hit, then a miss',
      summary: 'Every load and store uses a <b>virtual address</b>. The CPU must turn it into a physical one before touching memory, and the TLB decides whether that is nearly free or costs a page walk. Times here are nanoseconds, far below 1 ms.',
      steps: [
        { path: ['proc', 'tlb'], label: 'load VA 0x7f3a…', ms: 0, title: 'The program reads a variable',
          detail: 'The address in the instruction is virtual. Before the load can go anywhere, the MMU needs the physical frame behind this virtual page, so it asks the TLB first.' },
        { at: 'tlb', badge: 'hit → frame 0x1c4', tone: 'ok', ms: 0, title: 'TLB hit: one lookup',
          detail: 'The TLB is a small cache of recent page → frame translations. A hit costs about a cycle, which is why most memory accesses pay nothing for virtual memory.' },
        { path: ['tlb', 'ram'], label: 'physical access', tone: 'ok', ms: 0, title: 'Load from the physical address',
          detail: 'Now the access goes to the CPU caches and, if they miss, to RAM (≈ 100 ns). Translation was not the bottleneck.' },
        { path: ['proc', 'tlb'], label: 'load VA on a new page', ms: 0, title: 'Next access touches a different page',
          detail: 'Same process, but a page whose translation is not in the TLB, for example after a context switch or on a large heap.' },
        { path: ['tlb', 'pt'], label: 'miss → page walk', tone: 'warn', badgeAt: 'pt', badge: '4 levels = 4 memory reads', ms: 0, title: 'TLB miss: walk the page table',
          detail: 'The hardware walks the multi-level page table: 4 levels on x86-64, 5 with LA57, each one a memory access. This is why <b>huge pages</b> (2 MB, 1 GB) help big heaps: one TLB entry covers far more memory.' },
        { path: ['pt', 'tlb'], label: 'PTE → fill TLB', ms: 0, title: 'Cache the translation',
          detail: 'The page-table entry is present, so no kernel is involved. The translation goes into the TLB so the next access to this page is a hit.' },
        { path: ['tlb', 'ram'], label: 'physical access', tone: 'ok', ms: 0, title: 'The load completes',
          detail: 'A TLB miss costs tens of nanoseconds, not a fault. Only a <b>missing or read-only</b> entry makes the CPU trap into the kernel.' },
      ],
    },
    {
      id: 'cow', name: 'Minor fault: copy-on-write after fork()',
      summary: 'After <code>fork()</code>, parent and child share every physical page, all marked read-only. The first <b>write</b> to a shared page takes a <b>minor fault</b>: no disk, just a page copy (≈ microseconds).',
      steps: [
        { at: 'proc', badge: 'fork() → shares all pages', ms: 0, title: 'fork() copied the page table, not the memory',
          detail: 'The child\'s page table points at the same frames as the parent\'s, all read-only. That is why <code>fork()</code> is cheap even for a large process.' },
        { path: ['proc', 'tlb', 'pt'], label: 'write VA', ms: 0, title: 'The process writes to a shared page',
          detail: 'The translation exists, but the entry is marked read-only. A write through it is not allowed.' },
        { path: ['pt', 'fault'], label: 'PTE read-only → trap', tone: 'warn', ms: 0, title: 'Protection fault into the kernel',
          detail: 'The CPU stops the instruction and jumps to the kernel\'s page-fault handler with the faulting address and the reason (write to a read-only page).' },
        { at: 'fault', badge: 'COW: copy this one page', ms: .002, title: 'Kernel sees a copy-on-write page',
          detail: 'The page is shared, so the kernel copies only this one 4 KB page. Pages nobody writes stay shared forever, so <code>fork()</code> then <code>exec()</code> copies almost nothing.' },
        { path: ['fault', 'ram'], label: 'new frame + copy', ms: 0, title: 'Allocate a frame and copy into it',
          detail: 'The data is already in RAM, so this is a <b>minor</b> fault. The same kind of fault happens on the first touch of freshly allocated memory, where the kernel maps a zeroed page.' },
        { path: ['fault', 'pt'], label: 'PTE → new frame, writable', ms: 0, title: 'Point the writer at its private copy',
          detail: 'The writer\'s entry now maps the new frame with write permission; the stale TLB entry is flushed. The other process keeps the original page.' },
        { path: ['pt', 'tlb', 'proc'], label: 'retry the write', tone: 'ok', ms: 0, title: 'The instruction re-runs and succeeds',
          detail: 'The process never notices. The cost is the trap plus one page copy, which is why write-heavy children after <code>fork()</code> (e.g. Redis snapshots) can use far more memory than expected.' },
      ],
    },
    {
      id: 'major', name: 'Major fault: mmap\'d file not in RAM',
      summary: 'A <b>major fault</b> needs data that is not in memory at all (a memory-mapped file or swapped-out page), so the kernel must read from disk. That costs milliseconds, roughly 10,000× a RAM access.',
      steps: [
        { path: ['proc', 'tlb', 'pt'], label: 'read VA (mmap\'d file)', ms: 0, title: 'Read a byte of a memory-mapped file',
          detail: 'The file was <code>mmap</code>ed, so its bytes look like ordinary memory. TLB miss, then the walk finds the entry.' },
        { path: ['pt', 'fault'], label: 'PTE not present → trap', tone: 'warn', ms: 0, title: 'Page not present: fault',
          detail: 'The entry says no frame is mapped yet. The kernel must find the data before the instruction can finish.' },
        { path: ['fault', 'pcache'], label: 'file page cached?', tone: 'warn', badgeAt: 'pcache', badge: 'miss', ms: 0, title: 'Check the page cache first',
          detail: 'Linux caches file contents in free RAM. On a hit, the kernel just maps that page: a <b>minor</b> fault. Here it is a miss.' },
        { path: ['pcache', 'disk'], label: 'read 4 KB (+ readahead)', tone: 'err', ms: 5, title: 'Go to disk: a major fault',
          detail: 'Roughly milliseconds on a spinning disk (≈ 0.1 ms even on NVMe). The thread sleeps and the scheduler runs something else meanwhile. A swapped-out page takes the same path from swap.' },
        { path: ['disk', 'pcache'], label: 'page arrives', ms: 0, title: 'The page lands in the page cache',
          detail: 'It stays cached, so the next process to fault on this file page gets only a minor fault.' },
        { path: ['pcache', 'fault', 'pt'], label: 'map frame in PTE', ms: 0, title: 'Map the cached page into the process',
          detail: 'The kernel fills in the entry that pointed nowhere, then wakes the thread.' },
        { path: ['pt', 'tlb', 'proc'], label: 'retry the read', tone: 'ok', ms: 0, title: 'The instruction re-runs',
          detail: 'From the program\'s point of view one ordinary load took milliseconds. This is what makes swapping, or a cold <code>mmap</code>ed database file, feel like a stall.' },
      ],
    },
  ],
});

/* ========================================================= MVCC (CS/03) == */
const LosMV = lane([
  { label: 'TRANSACTIONS', nodes: [
    { id: 'w', label: 'Writer 100', sub: 'txn 100', kind: 'client', icon: 'user', row: 0 },
    { id: 'w2', label: 'Writer 101', sub: 'txn 101', kind: 'client', icon: 'user', row: 1 },
    { id: 'r', label: 'Reader', sub: 'txn 99 snapshot', kind: 'client', icon: 'user', row: 2 }] },
  { label: 'ENGINE', nodes: [
    { id: 'lock', label: 'Row lock', sub: 'held until commit', icon: 'lock', row: 0.5 }] },
  { label: 'HEAP', nodes: [
    { id: 'heap', label: 'Row versions', sub: 'v1 Alice · xmin 50', kind: 'db', icon: 'layers', row: 1 }] },
  { label: 'MAINTENANCE', nodes: [
    { id: 'vac', label: 'VACUUM', sub: 'reclaims dead rows', icon: 'worker', row: 1 }] },
]);
defineFlow('flow-mvcc', {
  title: 'Live flow: MVCC row versions and snapshots',
  hint: 'Watch an UPDATE create a new row version while a reader keeps seeing the old one, two writers collide on the same row, and a long transaction stop VACUUM.',
  zones: LosMV.zones, h: LosMV.h, nodes: LosMV.nodes,
  edges: [
    ['w', 'lock'], ['w2', 'lock'], ['w', 'heap'], ['w2', 'heap'], ['r', 'heap'], ['vac', 'heap'],
  ],
  scenarios: [
    {
      id: 'rw', name: 'Readers don\'t block writers',
      summary: 'PostgreSQL never overwrites a row in place. An UPDATE writes a <b>new version</b>, and each transaction\'s <b>snapshot</b> decides which version it can see. Times are illustrative (≈ 1 ms per statement).',
      steps: [
        { at: 'r', badge: 'snapshot: 100 not committed', ms: 0, title: 'The reader takes a snapshot',
          detail: 'A snapshot records which transactions had committed when it was taken. Transaction 100 is still running, so its writes will be invisible to this reader.' },
        { path: ['w', 'heap'], label: 'UPDATE name=\'Bob\'', badgeAt: 'heap', badge: 'v1 xmax 100 · v2 Bob xmin 100', ms: 1, title: 'The writer adds version 2',
          detail: 'The update writes v2 stamped <code>xmin = 100</code> and marks v1 with <code>xmax = 100</code>. Alice is still on disk; nothing was overwritten.' },
        { path: ['r', 'heap', 'r'], label: 'SELECT name', badgeAt: 'r', badge: '\'Alice\'', tone: 'ok', ms: 1, title: 'The reader gets Alice without waiting',
          detail: 'v2 was created by 100, which is not committed in the snapshot, so it is invisible. v1\'s deleter is also 100, so v1 still counts as live. No lock was needed.' },
        { at: 'w', badge: 'COMMIT 100', tone: 'ok', ms: 1, title: 'The writer commits',
          detail: 'Committing just records "100 committed" in the commit log (<code>pg_xact</code>), which visibility checks consult. No row is rewritten, which is why a commit is cheap regardless of how many rows changed.' },
        { path: ['r', 'heap', 'r'], label: 'SELECT again', badgeAt: 'r', badge: 'still \'Alice\' (RR / SI)', ms: 1, title: 'Same snapshot, same answer',
          detail: 'Under Repeatable Read (snapshot isolation) the whole transaction reuses its first snapshot, so it still sees Alice. Under <b>Read Committed</b> (the Postgres default) each statement takes a new snapshot and would now see Bob.' },
      ],
    },
    {
      id: 'ww', name: 'Writers do block writers',
      summary: 'MVCC removes reader/writer blocking, but two writers on the <b>same row</b> still queue on the row lock. What the second one does next depends on the isolation level.',
      steps: [
        { path: ['w', 'lock'], label: 'lock row', ms: 0, title: 'Writer 100 locks the row',
          detail: 'An UPDATE takes a row lock before writing and holds it until its transaction ends. Other rows are untouched.' },
        { path: ['w', 'heap'], label: 'write v2 (Bob)', ms: 1, title: 'Writer 100 writes its version',
          detail: 'Same as before: a new version with <code>xmin = 100</code>, the old one gets <code>xmax = 100</code>.' },
        { path: ['w2', 'lock'], label: 'UPDATE same row', tone: 'warn', badgeAt: 'lock', badge: 'txn 101 waits', ms: 1, title: 'Writer 101 has to wait',
          detail: 'Two versions can\'t both become the "next" version of one row, so 101 blocks on the lock. Readers are still unaffected.' },
        { at: 'w', badge: 'COMMIT 100', tone: 'ok', ms: 1, title: 'Writer 100 commits and releases the lock',
          detail: 'The lock is released at commit (or rollback), never earlier, so 101 can\'t act on a value that might still be undone.' },
        { path: ['lock', 'w2'], label: 'lock granted', tone: 'warn', badgeAt: 'w2', badge: 'RC: re-check · RR: abort', ms: 1, title: 'What 101 does depends on isolation',
          detail: 'Under Read Committed, Postgres re-reads the newly committed row and applies the update to it. Under Repeatable Read it aborts with a <b>serialization failure</b> and the application must retry, which is how Postgres RR prevents lost updates.' },
      ],
    },
    {
      id: 'bloat', name: 'Long transaction → bloat',
      summary: 'Old versions are only garbage once <b>no snapshot</b> can still see them. One transaction left open for hours keeps every version created since then alive.',
      steps: [
        { at: 'r', badge: 'txn open for hours', tone: 'warn', ms: 0, title: 'A transaction is left open',
          detail: 'A forgotten <code>BEGIN</code> in a console, or a long report query. Its snapshot is now the oldest one in the database.' },
        { path: ['w', 'heap'], label: 'many UPDATEs', badgeAt: 'heap', badge: '+ thousands of dead versions', ms: 1, title: 'Normal writes keep creating versions',
          detail: 'Every UPDATE leaves the previous version behind. Normally these become dead and are cleaned up shortly afterwards.' },
        { at: 'w', badge: 'COMMIT', tone: 'ok', ms: 1, title: 'The writers commit',
          detail: 'The old versions are now dead for every new snapshot, but not for the old reader\'s snapshot.' },
        { path: ['vac', 'heap'], label: 'reclaim dead versions?', async: true, title: 'VACUUM runs in the background',
          detail: 'VACUUM may only remove versions that are invisible to <b>every</b> active snapshot. The oldest snapshot sets that horizon.' },
        { at: 'vac', badge: 'kept: oldest snapshot needs them', tone: 'err', async: true, title: 'Nothing can be reclaimed',
          detail: 'The open transaction might still read those versions, so they stay. The table and its indexes grow (<b>bloat</b>) and scans read ever more dead rows.' },
        { at: 'r', badge: 'COMMIT / end', tone: 'ok', ms: 1, title: 'The old transaction finally ends',
          detail: 'The horizon moves forward. Monitoring long transactions (and <code>idle in transaction</code> sessions) prevents this.' },
        { path: ['vac', 'heap'], label: 'reclaim', tone: 'ok', badgeAt: 'heap', badge: 'space reusable', async: true, title: 'VACUUM can clean up',
          detail: 'The space is reused for new versions (the file rarely shrinks). InnoDB avoids heap bloat by keeping old versions in <b>undo logs</b> instead, which then grow in the same situation.' },
      ],
    },
  ],
});

/* ============================================ Spanner + TrueTime (CS/03) == */
const LosSP = lane([
  { label: 'CLIENT (NY)', nodes: [
    { id: 'c1', label: 'Client T1', sub: 'writes first', kind: 'client', icon: 'user', row: 0 }] },
  { label: 'NEW YORK', nodes: [
    { id: 'ny', label: 'NY leader', sub: 'Paxos leader', icon: 'server', row: 0 },
    { id: 'rep', label: 'NY replicas', sub: 'Paxos majority', kind: 'db', icon: 'replica', row: 2 }] },
  { label: 'TIME', nodes: [
    { id: 'tt', label: 'TrueTime', sub: 'GPS + atomic', icon: 'time', row: 0 }] },
  { label: 'TOKYO', nodes: [
    { id: 'tk', label: 'Tokyo leader', sub: 'Paxos leader', icon: 'server', row: 1 }] },
  { label: 'CLIENT (TOKYO)', nodes: [
    { id: 'c2', label: 'Client T2', sub: 'after T1 ack', kind: 'client', icon: 'user', row: 1 }] },
], { rowH: 96 });
defineFlow('flow-spanner-commit', {
  title: 'Live flow: Spanner commit wait and 2PC over Paxos',
  hint: 'See why Spanner waits out clock uncertainty before acknowledging a commit, and how two-phase commit across Paxos groups survives a coordinator crash.',
  zones: LosSP.zones, h: LosSP.h, nodes: LosSP.nodes,
  edges: [
    ['c1', 'ny'], ['ny', 'rep'], ['ny', 'tt'], ['c2', 'tk'], ['tk', 'tt'], ['ny', 'tk'], ['rep', 'tk'],
  ],
  scenarios: [
    {
      id: 'wait', name: 'Commit wait',
      summary: 'Spanner promises <b>external consistency</b>: if T1 commits before T2 starts in real time, T1 gets the smaller timestamp, even on another continent. The price is a short wait of about 2ε. Latencies are approximate.',
      steps: [
        { path: ['c1', 'ny'], label: 'COMMIT T1', ms: 10, title: 'T1 asks the New York leader to commit',
          detail: 'The rows live in a New York Paxos group. Its leader holds the locks and will pick the commit timestamp.' },
        { path: ['ny', 'tt', 'ny'], label: 'TT.now()', badgeAt: 'ny', badge: '[earliest, latest]', ms: 0, title: 'Ask TrueTime for the time',
          detail: 'TrueTime returns an interval guaranteed to contain true time, not a single instant. Its half-width ε is typically about 1 to 7 ms.' },
        { at: 'ny', badge: 's = latest', ms: 0, title: 'Pick the commit timestamp',
          detail: 'Choosing <code>s ≥ TT.now().latest</code> means s is not earlier than the true time at this moment, whatever any clock says.' },
        { path: ['ny', 'rep', 'ny'], label: 'Paxos accept', ms: 10, title: 'Replicate the commit to a majority',
          detail: 'The write is durable once a majority of the group has it (≈ 10 ms here). The commit wait below runs in parallel with this round.' },
        { at: 'ny', badge: 'wait until TT.after(s)', tone: 'warn', ms: 8, title: 'Commit wait: about 2ε',
          detail: 'The leader waits until <code>TT.now().earliest > s</code>. After that, every correct clock in the world reads past s, so no later transaction can get a smaller timestamp.' },
        { path: ['ny', 'c1'], label: 'ack T1 @ s', tone: 'ok', ms: 10, title: 'Only now is T1 visible and acknowledged',
          detail: 'Making the commit visible before the wait could let a transaction elsewhere start "after" T1 in real time yet read a timestamp below s.' },
        { path: ['c2', 'tk', 'tt', 'tk'], label: 'T2 → TT.now()', ms: 10, title: 'T2 starts in Tokyo',
          detail: 'Tokyo\'s leader gets <code>[earliest2, latest2]</code> from its own time masters, with no message to New York.' },
        { at: 'tk', badge: 'T2 timestamp > s', tone: 'ok', ms: 0, title: 'External consistency without talking to NY',
          detail: 'Because T1 waited, <code>earliest2 > s</code> is guaranteed, so T2\'s timestamp is larger. Snapshot reads at a timestamp are then lock-free and globally consistent.' },
      ],
    },
    {
      id: '2pc', name: 'Multi-shard: 2PC over Paxos groups',
      summary: 'T1 writes rows in both New York and Tokyo. Spanner runs <b>two-phase commit</b>, but every participant, including the coordinator, is a whole Paxos group rather than one machine. Cross-Pacific hops are roughly 80 ms one way.',
      steps: [
        { path: ['c1', 'ny'], label: 'COMMIT (NY coordinates)', ms: 10, title: 'One group leader becomes coordinator',
          detail: 'The New York leader coordinates; Tokyo\'s group is a participant.' },
        { path: ['ny', 'tk'], label: 'prepare', ms: 80, title: 'Phase 1: ask Tokyo to prepare',
          detail: 'Tokyo must promise it can commit whatever the coordinator decides.' },
        { at: 'tk', badge: 'log prepare via Paxos', ms: 10, title: 'The participant logs its vote through Paxos',
          detail: 'The prepare record, with a prepare timestamp, is replicated in Tokyo\'s group, so the promise survives the loss of the Tokyo leader too.' },
        { path: ['tk', 'ny'], label: 'prepared', ms: 80, title: 'Tokyo votes yes',
          detail: 'From here Tokyo holds its locks and cannot decide alone; it needs the coordinator\'s outcome.' },
        { path: ['ny', 'tt', 'ny'], label: 'TT.now()', badgeAt: 'ny', badge: 's ≥ latest, ≥ prepare ts', ms: 0, title: 'Pick one commit timestamp',
          detail: 's must be at least every participant\'s prepare timestamp and at least <code>TT.now().latest</code>.' },
        { path: ['ny', 'rep', 'ny'], label: 'log COMMIT via Paxos', ms: 10, title: 'The decision is replicated',
          detail: 'Once a majority of the New York group has the commit record, the outcome no longer depends on the leader machine surviving.' },
        { at: 'ny', badge: 'commit wait ≈ 2ε', tone: 'warn', ms: 8, title: 'Commit wait, as for a single group',
          detail: 'The same rule that orders single-group commits orders multi-shard ones.' },
        { path: ['ny', 'c1'], label: 'ack @ s', tone: 'ok', ms: 10, title: 'The client is acknowledged',
          detail: 'The transaction is committed everywhere at timestamp s.' },
        { path: ['ny', 'tk'], label: 'commit @ s', async: true, tone: 'ok', title: 'Tokyo applies and releases its locks',
          detail: 'Participants learn the outcome and release locks. Nothing here needs another wide-area round trip from the client.' },
      ],
    },
    {
      id: 'crash', name: 'Coordinator leader crashes',
      summary: 'Classic 2PC\'s weak spot: participants that voted yes block if the coordinator dies. Here the coordinator is a Paxos group, so its decision outlives any one machine.',
      down: ['ny'],
      steps: [
        { at: 'tk', badge: 'prepared · locks held', tone: 'warn', ms: 0, title: 'Tokyo has voted yes and is waiting',
          detail: 'In classic 2PC with one coordinator machine, Tokyo would be stuck holding locks until that machine came back.' },
        { at: 'ny', badge: 'leader crashed', tone: 'err', ms: 0, title: 'The New York leader dies after logging COMMIT',
          detail: 'The commit record had already reached a majority of the New York group before the crash.' },
        { at: 'rep', badge: 'new leader elected', tone: 'ok', ms: 10, title: 'A New York replica takes over',
          detail: 'Paxos elects a new leader from the surviving majority. It has the commit record in its log, so it knows the outcome.' },
        { path: ['rep', 'tk'], label: 'commit @ s', tone: 'ok', ms: 80, title: 'The new leader finishes the protocol',
          detail: 'Tokyo receives the decision and releases its locks. No participant blocks on a single failed machine.' },
      ],
    },
  ],
});

/* ================================================ OAuth + PKCE (API/03) == */
const LosOA = lane([
  { label: 'USER', nodes: [
    { id: 'user', label: 'Browser', sub: 'user logs in here', kind: 'client', icon: 'browser', row: 1 }] },
  { label: 'CLIENT APPS', nodes: [
    { id: 'app', label: 'Your app', sub: 'holds code_verifier', icon: 'app', row: 0 },
    { id: 'atk', label: 'Malicious app', sub: 'same redirect scheme', kind: 'client', icon: 'alert', row: 2 }] },
  { label: 'AUTH SERVER', nodes: [
    { id: 'as', label: 'Auth server', sub: '/authorize · /token', icon: 'auth', row: 1 }] },
  { label: 'RESOURCES', nodes: [
    { id: 'api', label: 'Resource API', sub: 'GET /orders', icon: 'api', row: 0 },
    { id: 'jwks', label: 'JWKS cache', sub: 'public keys by kid', kind: 'cache', icon: 'key', row: 1 }] },
]);
defineFlow('flow-oauth-pkce', {
  title: 'Live flow: OAuth 2.0 authorization code + PKCE',
  hint: 'Walk the login redirect dance, watch an API verify a JWT locally, and see PKCE stop a stolen authorization code.',
  zones: LosOA.zones, h: LosOA.h, nodes: LosOA.nodes,
  edges: [
    ['app', 'user'], ['user', 'as'], ['app', 'as'], ['app', 'api'], ['api', 'jwks'],
    ['user', 'atk'], ['atk', 'as'],
  ],
  scenarios: [
    {
      id: 'login', name: 'Authorization code + PKCE',
      summary: 'The app never sees the user\'s password. It gets a one-time <b>code</b> through the browser, then swaps it for tokens over a direct call, proving with <b>PKCE</b> that it is the app that started the login. Latencies are approximate.',
      steps: [
        { at: 'app', badge: 'challenge = SHA256(verifier)', ms: 0, title: 'The app makes a secret and its hash',
          detail: 'A fresh random <code>code_verifier</code> stays inside the app. Only its hash, the <code>code_challenge</code>, will travel through the browser.' },
        { path: ['app', 'user'], label: '302 → /authorize', ms: 50, title: 'Send the user to the auth server',
          detail: 'The redirect URL carries <code>client_id</code>, <code>scope</code>, the redirect URI and the <code>code_challenge</code>.' },
        { path: ['user', 'as'], label: '/authorize?…&code_challenge', ms: 50, title: 'The browser opens the login page',
          detail: 'The auth server stores the challenge with this pending login so it can check it later.' },
        { at: 'as', badge: 'log in + approve scopes', ms: 3000, title: 'The user signs in and consents',
          detail: 'Human time, ≈ seconds. The password goes only to the auth server; the app never handles it.' },
        { path: ['as', 'user', 'app'], label: '302 ?code=abc', ms: 50, title: 'The browser brings back a one-time code',
          detail: 'The code is short-lived and single-use, but it travelled through the browser (history, logs, redirect handlers), so assume it can leak.' },
        { path: ['app', 'as'], label: 'POST /token {code, code_verifier}', ms: 50, title: 'Swap the code on a direct channel',
          detail: 'Now the app reveals the verifier. The auth server hashes it and checks it matches the stored challenge.' },
        { path: ['as', 'app'], label: 'access_token + refresh_token', tone: 'ok', ms: 10, title: 'Tokens issued',
          detail: 'The access token is short-lived (typically 5-15 minutes) to limit damage if stolen; the refresh token gets new ones without another login.' },
        { path: ['app', 'api', 'app'], label: 'GET /orders · Bearer', tone: 'ok', ms: 60, title: 'Call the API with the access token',
          detail: 'The token goes in the <code>Authorization: Bearer</code> header on every request.' },
      ],
    },
    {
      id: 'jwt', name: 'API validates the JWT',
      summary: 'A JWT access token is verified <b>locally</b> by the API with the auth server\'s public key, so the hot path never calls the auth server.',
      steps: [
        { path: ['app', 'api'], label: 'Bearer eyJhbGci…', ms: 30, title: 'A request arrives with a JWT',
          detail: 'Header, claims and signature, base64url-encoded. It is signed, not encrypted: anyone can read the claims.' },
        { at: 'api', badge: 'alg allowlisted · kid', ms: .1, title: 'Read the header first',
          detail: 'Accept only the algorithms you expect and reject <code>alg: none</code>. The <code>kid</code> says which signing key was used.' },
        { path: ['api', 'jwks', 'api'], label: 'public key for kid', ms: 1, title: 'Fetch the key from the local cache',
          detail: 'The auth server publishes its public keys (JWKS). The API caches them and refetches only on an unknown <code>kid</code>, e.g. after key rotation.' },
        { at: 'api', badge: 'sig ✓ iss ✓ aud ✓ exp ✓', tone: 'ok', ms: .2, title: 'Verify signature and claims locally',
          detail: 'Checking locally is fast, but it is also why a JWT can\'t be revoked before <code>exp</code> without a denylist.' },
        { at: 'api', badge: 'scope ✓ owns order ✓', tone: 'ok', ms: .5, title: 'Authorize, not just authenticate',
          detail: 'Check the scope (<code>orders:read</code>) and that each order belongs to <code>sub</code>. Skipping the ownership check is BOLA, the top API vulnerability.' },
        { path: ['api', 'app'], label: '200 OK', tone: 'ok', ms: 30, title: 'Response returned',
          detail: 'A missing or invalid token would get <code>401</code>; a valid token without permission gets <code>403</code> (or <code>404</code>).' },
      ],
    },
    {
      id: 'stolen', name: 'Stolen authorization code',
      summary: 'An attacker grabs the code from the redirect. Without PKCE they could redeem it. With PKCE they are missing the verifier, which never left the app.',
      steps: [
        { path: ['as', 'user'], label: '302 ?code=abc', ms: 50, title: 'The auth server redirects with the code',
          detail: 'Same as a normal login so far.' },
        { path: ['user', 'atk'], label: 'code=abc leaks', tone: 'warn', ms: 0, title: 'A malicious app intercepts the code',
          detail: 'On a phone, another app can register the same custom URL scheme and receive the redirect. Codes can also leak through logs or proxies.' },
        { path: ['atk', 'as'], label: 'POST /token {code}', ms: 50, title: 'The attacker tries to redeem it',
          detail: 'They saw the <code>code_challenge</code> earlier, but it is a SHA-256 hash, so they can\'t work back to the verifier.' },
        { at: 'as', badge: 'SHA256(verifier) ≠ challenge', tone: 'err', ms: 0, title: 'PKCE check fails',
          detail: 'No verifier, or a wrong one, does not hash to the challenge stored at <code>/authorize</code>.' },
        { path: ['as', 'atk'], label: '400 invalid_grant', tone: 'err', ms: 10, title: 'No tokens for the attacker',
          detail: 'The stolen code is useless on its own. That is why public clients (SPAs, mobile apps), which can\'t keep a client secret, must use PKCE.' },
      ],
    },
  ],
});

/* ======================================================== CORS (API/02) == */
const LosCO = lane([
  { label: 'PAGE', nodes: [
    { id: 'js', label: 'JS on app.com', sub: 'fetch() cross-origin', kind: 'client', icon: 'code', row: 0 }] },
  { label: 'BROWSER', nodes: [
    { id: 'br', label: 'CORS check', sub: 'same-origin policy', icon: 'browser', row: 0 }] },
  { label: 'API', nodes: [
    { id: 'api', label: 'api.com', sub: 'sets CORS headers', icon: 'api', row: 0 }] },
  { label: 'OTHER CLIENTS', nodes: [
    { id: 'curl', label: 'curl / server', sub: 'no browser involved', kind: 'client', icon: 'cli', row: 0 }] },
]);
defineFlow('flow-cors', {
  title: 'Live flow: a CORS preflight in the browser',
  hint: 'Follow a cross-origin fetch through the browser\'s preflight, see what happens when the API forgets its headers, and why curl never sees CORS at all.',
  zones: LosCO.zones, h: LosCO.h, nodes: LosCO.nodes,
  edges: [['js', 'br'], ['br', 'api'], ['api', 'curl']],
  scenarios: [
    {
      id: 'ok', name: 'Preflight OK',
      summary: 'JavaScript on <code>https://app.com</code> calls <code>https://api.com</code>. Different origin, so the browser only lets the page read the response if the API <b>opts in</b>. Latencies are approximate.',
      steps: [
        { path: ['js', 'br'], label: 'fetch POST /orders', ms: 0, title: 'The page calls a different origin',
          detail: 'Origin is scheme + host + port. <code>app.com</code> and <code>api.com</code> differ, so the same-origin policy applies.' },
        { at: 'br', badge: 'not simple → preflight', ms: 0, title: 'The browser decides to ask first',
          detail: 'A POST with an <code>Authorization</code> header or a JSON body is not a "simple" request, so the browser checks with the server before sending it.' },
        { path: ['br', 'api'], label: 'OPTIONS /orders · Origin', ms: 30, title: 'Preflight request',
          detail: 'Sent automatically with <code>Origin: https://app.com</code>, <code>Access-Control-Request-Method: POST</code> and the headers it wants to use.' },
        { path: ['api', 'br'], label: '204 + Allow-Origin: app.com', tone: 'ok', ms: 30, title: 'The API says yes',
          detail: 'It lists the exact origin plus <code>Allow-Methods: POST</code> and <code>Allow-Headers: Authorization, Content-Type</code>.' },
        { path: ['br', 'api'], label: 'POST /orders', ms: 30, title: 'Now the real request goes out',
          detail: 'The preflight cost an extra round trip; <code>Access-Control-Max-Age</code> lets the browser cache the answer.' },
        { path: ['api', 'br'], label: '201 + Allow-Origin', ms: 30, title: 'The response also carries CORS headers',
          detail: 'The actual response must repeat <code>Access-Control-Allow-Origin</code> too, or the page still can\'t read it.' },
        { path: ['br', 'js'], label: 'response readable', tone: 'ok', ms: 0, title: 'The page gets the data',
          detail: 'The browser hands the body to JavaScript only because every check passed.' },
      ],
    },
    {
      id: 'missing', name: 'Missing CORS headers',
      summary: 'The API works in curl but the browser shows a "CORS error". The fix is on the <b>server</b>, not in the front-end code.',
      steps: [
        { path: ['js', 'br'], label: 'fetch POST /orders', ms: 0, title: 'Same cross-origin call',
          detail: 'Same request as before, so a preflight is needed.' },
        { path: ['br', 'api'], label: 'OPTIONS /orders', ms: 30, title: 'Preflight goes out',
          detail: 'The server receives it, but its CORS config doesn\'t cover this origin, or doesn\'t answer <code>OPTIONS</code> at all.' },
        { path: ['api', 'br'], label: '204 (no Allow-Origin)', tone: 'warn', ms: 30, title: 'No permission in the answer',
          detail: 'Without <code>Access-Control-Allow-Origin</code> matching <code>https://app.com</code>, the browser treats the answer as "no".' },
        { at: 'br', badge: 'blocked · POST never sent', tone: 'err', ms: 0, title: 'The browser stops here',
          detail: 'The console shows a CORS error and JavaScript gets an opaque network error, not the status. The fix is adding the right headers on the API.' },
        { path: ['br', 'js'], label: 'TypeError: failed to fetch', tone: 'err', ms: 0, title: 'The page sees only a failure',
          detail: 'For a <b>simple</b> request (e.g. a plain GET) there is no preflight: the request does reach the server and runs, and the browser just hides the response. CORS protects reading, not the server.' },
      ],
    },
    {
      id: 'curl', name: 'curl ignores CORS',
      summary: 'CORS is enforced <b>by browsers only</b>. It protects users from other sites reading data with their browser, and is not an authentication mechanism.',
      steps: [
        { at: 'curl', badge: 'Origin: anything it likes', tone: 'warn', ms: 0, title: 'A non-browser client can say anything',
          detail: 'curl, mobile apps and server-to-server calls can send any <code>Origin</code> header, or none, so the server can\'t trust it for security.' },
        { path: ['curl', 'api'], label: 'POST /orders + token', ms: 30, title: 'Straight to the API, no preflight',
          detail: 'Nothing sends an <code>OPTIONS</code> preflight and nothing checks the response headers.' },
        { at: 'api', badge: 'auth checked, not CORS', ms: 1, title: 'The server\'s real defence is authentication',
          detail: 'Tokens, scopes and ownership checks protect the API. CORS headers are only instructions to browsers.' },
        { path: ['api', 'curl'], label: '201 Created', tone: 'ok', ms: 30, title: 'curl reads the response',
          detail: 'No browser, no same-origin policy. That is why "it works in curl" tells you nothing about CORS.' },
      ],
    },
  ],
});

/* ================================================= sql transaction (SQL/09) == */
const LosTx = lane([
  { label: 'TRANSACTION A', nodes: [
    { id: 't1_b', label: 'BEGIN', kind: 'client', icon: 'start', row: 0 },
    { id: 't1_w', label: 'UPDATE account', kind: 'client', icon: 'edit', row: 1 },
    { id: 't1_c', label: 'COMMIT', kind: 'client', icon: 'check', row: 4 }] },
  { label: 'DATABASE (Postgres)', nodes: [
    { id: 'db_row', label: 'Row Data', sub: 'balance=100', kind: 'db', icon: 'db', row: 2 },
    { id: 'db_lock', label: 'Row Lock', sub: 'exclusive', kind: 'cache', icon: 'lock', row: 1 }] },
  { label: 'TRANSACTION B', nodes: [
    { id: 't2_b', label: 'BEGIN', kind: 'client', icon: 'start', row: 0 },
    { id: 't2_r', label: 'SELECT balance', sub: 'Read Committed', kind: 'client', icon: 'search', row: 2 },
    { id: 't2_w', label: 'UPDATE account', sub: 'Blocked', kind: 'client', icon: 'edit', row: 3 }] }
]);

defineFlow('flow-sql-isolation', {
  title: 'Live flow: ACID Isolation Levels',
  hint: 'Watch how Transaction B is blocked from writing, but under Read Committed can still read the old value.',
  zones: LosTx.zones, h: LosTx.h, nodes: LosTx.nodes,
  edges: [
    ['t1_b', 't1_w'], ['t1_w', 'db_lock'], ['t1_w', 'db_row'],
    ['t2_b', 't2_r'], ['t2_r', 'db_row'], ['t2_r', 't2_w'], ['t2_w', 'db_lock'],
    ['db_lock', 't1_c', { dashed: true }]
  ],
  scenarios: [
    {
      id: 'rc', name: 'Read Committed (Postgres Default)',
      summary: 'Tx A updates the row (taking the exclusive lock). Tx B tries to read it: under Read Committed, it reads the <b>old</b> committed value (no lock needed). Tx B then tries to update it and <b>blocks</b> waiting for Tx A to commit.',
      steps: [
        { node: 't1_b', note: 'Tx A starts' },
        { node: 't1_w', edge: ['t1_b', 't1_w'] },
        { node: 'db_lock', edge: ['t1_w', 'db_lock'], note: 'Tx A acquires the exclusive row lock.' },
        { node: 'db_row', edge: ['t1_w', 'db_row'], note: 'Tx A writes the new value, but it is uncommitted.' },
        { node: 't2_b', note: 'Tx B starts' },
        { node: 't2_r', edge: ['t2_b', 't2_r'] },
        { node: 'db_row', edge: ['t2_r', 'db_row'], note: 'Tx B reads the old snapshot value (100).' },
        { node: 't2_w', edge: ['t2_r', 't2_w'] },
        { node: 'db_lock', edge: ['t2_w', 'db_lock'], error: true, note: 'Tx B tries to update and blocks!' },
        { node: 't1_c', edge: ['db_lock', 't1_c'], note: 'Tx A commits, releasing the lock. Tx B can now proceed.' }
      ]
    }
  ]
});

}
