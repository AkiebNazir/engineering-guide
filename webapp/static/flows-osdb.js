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

/* ====================================== CAP: one partition, CP vs AP (CS/03 §7) == */
const LcsCAP = lane([
  { label: 'CLIENT 1', nodes: [
    { id: 'c1', label: 'Client 1', sub: 'talks to A', kind: 'client', icon: 'user', row: 0 }] },
  { label: 'MAJORITY SIDE', nodes: [
    { id: 'ra', label: 'Replica A', sub: 'leader', kind: 'db', icon: 'db', row: 0 },
    { id: 'rb', label: 'Replica B', sub: 'follower', kind: 'db', icon: 'db', row: 2 }] },
  { label: 'NETWORK', nodes: [
    { id: 'net', label: 'Link to C', sub: 'switch / zone link', icon: 'network', row: 1 }] },
  { label: 'MINORITY SIDE', nodes: [
    { id: 'rc', label: 'Replica C', sub: 'follower', kind: 'db', icon: 'db', row: 1 }] },
  { label: 'CLIENT 2', nodes: [
    { id: 'c2', label: 'Client 2', sub: 'talks to C', kind: 'client', icon: 'user', row: 1 }] },
]);
defineFlow('flow-cap-partition', {
  title: 'Live flow: a network partition, CP vs. AP',
  hint: 'Three replicas, one cut link. Compare a healthy quorum write with what a consistent (CP) and an available (AP) system do when a client reaches only the minority side.',
  zones: LcsCAP.zones, h: LcsCAP.h, nodes: LcsCAP.nodes,
  edges: [['c1', 'ra'], ['ra', 'rb'], ['ra', 'net'], ['net', 'rc'], ['rc', 'c2']],
  scenarios: [
    {
      id: 'ok', name: 'Healthy: quorum write',
      summary: 'No partition. A write is acknowledged once a <b>majority</b> (2 of 3) has it, and any read that goes through the leader sees it. Latencies are approximate, for replicas in nearby zones.',
      steps: [
        { path: ['c1', 'ra'], label: 'PUT x = 1', ms: 1, title: 'Client 1 writes through the leader',
          detail: 'A single leader orders writes for this key range, the Raft/Paxos pattern from §6.' },
        { path: ['ra', 'rb'], label: 'append x = 1', ms: 1, title: 'Replicate to B',
          detail: 'The leader appends the entry to its log and sends it to the followers in parallel.' },
        { path: ['ra', 'net', 'rc'], label: 'append x = 1', ms: 1, title: 'Replicate to C',
          detail: 'C also gets the entry. The leader does not need C: two of three is already a majority.' },
        { path: ['rb', 'ra'], label: 'ack', tone: 'ok', badgeAt: 'ra', badge: '2 of 3 → committed', ms: 1, title: 'Majority reached: committed',
          detail: 'Once A and B have the entry it survives the loss of any one replica.' },
        { path: ['ra', 'c1'], label: '200 OK', tone: 'ok', ms: 1, title: 'Client 1 is acknowledged',
          detail: 'Normal operation still has a PACELC choice: this write waited for a replica round trip (EC). Acknowledging before replication would be faster (EL) but could lose the write.' },
        { path: ['c2', 'rc', 'net', 'ra'], label: 'GET x (linearizable)', ms: 2, title: 'Client 2 reads via C',
          detail: 'For a linearizable read, C confirms with the leader (Raft ReadIndex or a leader lease) that it is up to date. Reading C\'s local copy directly would be faster but possibly stale.' },
        { path: ['ra', 'net', 'rc', 'c2'], label: 'x = 1', tone: 'ok', ms: 2, title: 'Client 2 sees the latest write',
          detail: 'Every read reflects every acknowledged write: the system behaves like a single copy.' },
      ],
    },
    {
      id: 'cp', name: 'Partition: CP refuses',
      summary: 'The link to C fails. A consistent (CP) system keeps serving on the majority side and <b>refuses</b> on the minority side, because C cannot know what it missed.',
      down: ['net'],
      steps: [
        { at: 'net', badge: 'link down', tone: 'err', ms: 0, title: 'The network partitions',
          detail: 'A and B can talk; C can talk to nobody. Each side keeps running, and neither can tell a dead peer from a slow one.' },
        { path: ['c2', 'rc'], label: 'PUT x = 2', ms: 1, title: 'Client 2 writes via C',
          detail: 'C would have to forward to the leader or collect a majority itself. It can do neither.' },
        { at: 'rc', badge: '1 of 3 · no quorum', tone: 'warn', ms: 3000, title: 'C waits for a quorum that never answers',
          detail: 'After a timeout it gives up. Accepting the write locally would let the two sides diverge.' },
        { path: ['rc', 'c2'], label: '503 / timeout', tone: 'err', ms: 1, title: 'Unavailable on the minority side',
          detail: 'This is the "lose A" half of CAP. Only requests that reach C fail; clients that can reach A or B are fine.' },
        { path: ['c1', 'ra'], label: 'PUT x = 3', ms: 1, title: 'Client 1 writes on the majority side',
          detail: 'A still has B, which is 2 of 3.' },
        { path: ['ra', 'rb', 'ra'], label: 'append · ack', tone: 'ok', badgeAt: 'ra', badge: 'committed', ms: 2, title: 'The majority keeps committing',
          detail: 'Spanner, etcd, CockroachDB and MongoDB (w: majority) all behave like this: the majority side is fully available and linearizable.' },
        { at: 'rc', badge: 'heal → catch up to x = 3', tone: 'ok', ms: 5, title: 'When the link heals, C catches up',
          detail: 'C receives the log entries it missed. No acknowledged write was lost and no two clients ever saw conflicting values.' },
      ],
    },
    {
      id: 'ap', name: 'Partition: AP diverges',
      summary: 'Same partition. An available (AP) system lets <b>every</b> replica keep answering. Nobody gets an error, but the two sides now disagree, and something has to reconcile them later.',
      down: ['net'],
      steps: [
        { at: 'net', badge: 'link down', tone: 'err', ms: 0, title: 'The network partitions',
          detail: 'Same failure as the CP scenario.' },
        { path: ['c2', 'rc'], label: 'PUT x = 2', ms: 1, title: 'Client 2 writes via C',
          detail: 'A leaderless (Dynamo-style) store with write consistency ONE, or a multi-leader setup, accepts writes on any live replica.' },
        { path: ['rc', 'c2'], label: '200 OK', tone: 'ok', badgeAt: 'rc', badge: 'x = 2 (local)', ms: 1, title: 'Accepted locally',
          detail: 'Available, and fast. A hinted handoff will try to deliver the write to A and B later.' },
        { path: ['c1', 'ra', 'rb'], label: 'PUT x = 3', ms: 2, badgeAt: 'rb', badge: 'x = 3', title: 'Client 1 writes on the other side',
          detail: 'A concurrent write to the same key. Neither side knows about the other.' },
        { path: ['c2', 'rc', 'c2'], label: 'GET x → 2', tone: 'warn', ms: 1, title: 'Two clients, two answers',
          detail: 'Client 2 reads 2 while Client 1 would read 3. Not linearizable: the "lose C" half of CAP.' },
        { at: 'net', badge: 'healed', tone: 'ok', ms: 0, title: 'The partition heals',
          detail: 'Anti-entropy (read repair, Merkle-tree sync) finds that the replicas disagree about x.' },
        { path: ['rc', 'net', 'ra'], label: 'x = 2 vs x = 3', tone: 'err', badgeAt: 'ra', badge: 'LWW keeps 3, drops 2', ms: 5, title: 'Last-writer-wins silently drops a write',
          detail: 'Client 2 was told its write succeeded, and it is gone. Production AP systems avoid this with version vectors that surface conflicts, CRDTs, or application merge logic.' },
      ],
    },
  ],
});

/* ====================================== circuit breaker (CS/04 §6) == */
const LcsCB = lane([
  { label: 'CALLER', nodes: [
    { id: 'h', label: 'Checkout', sub: 'deadline 300 ms', icon: 'service', row: 0 }] },
  { label: 'CLIENT LIBRARY', nodes: [
    { id: 'br', label: 'Breaker', sub: 'closed/open/half-open', icon: 'gauge', row: 0 },
    { id: 'fb', label: 'Fallback', sub: 'last known prices', kind: 'cache', icon: 'cache', row: 1 }] },
  { label: 'DEPENDENCY', nodes: [
    { id: 'dep', label: 'Pricing', sub: 'remote service', icon: 'server', row: 0 }] },
]);
defineFlow('flow-circuit-breaker', {
  title: 'Live flow: a circuit breaker opening and closing',
  hint: 'Follow calls from a checkout service to a pricing dependency: normal traffic, an outage that trips the breaker so callers fail fast, and the half-open probe that closes it again.',
  zones: LcsCB.zones, h: LcsCB.h, nodes: LcsCB.nodes,
  edges: [['h', 'br'], ['br', 'dep'], ['br', 'fb']],
  scenarios: [
    {
      id: 'closed', name: 'Closed: normal traffic',
      summary: 'While the breaker is <b>closed</b>, every call goes through, bounded by a timeout that fits inside the caller\'s own deadline. Latencies are illustrative.',
      steps: [
        { path: ['h', 'br'], label: 'GET /price', ms: 0, title: 'Checkout needs a price',
          detail: 'The call goes through a client library (or a service-mesh sidecar) that owns the timeout, retry and breaker policy for this dependency.' },
        { at: 'br', badge: 'CLOSED → pass', tone: 'ok', ms: 0, title: 'Breaker closed: let it through',
          detail: 'The breaker tracks recent failures. Below the threshold it adds nothing but a counter update.' },
        { path: ['br', 'dep'], label: 'call · timeout 100 ms', ms: 20, title: 'Call the dependency with a timeout',
          detail: 'The timeout is shorter than the caller\'s remaining deadline, so a slow answer can\'t eat the whole budget.' },
        { path: ['dep', 'br', 'h'], label: '200 · price', tone: 'ok', ms: 20, title: 'Success resets the failure count',
          detail: 'A success keeps the breaker closed. Real libraries track a failure rate over a sliding window rather than a simple count.' },
      ],
    },
    {
      id: 'open', name: 'Outage: breaker opens',
      summary: 'Pricing starts timing out. Without a breaker, every checkout would wait the full timeout and hold a thread, and the slowness would climb the call graph. The breaker turns that into <b>fast failure plus a fallback</b>.',
      down: ['dep'],
      steps: [
        { path: ['h', 'br', 'dep'], label: 'call', ms: 0, title: 'A call goes out while Pricing is unhealthy',
          detail: 'Pricing is overloaded and not answering.' },
        { at: 'br', badge: 'timeout · fails 1 → 3', tone: 'warn', ms: 100, title: 'Three calls time out in a row',
          detail: 'Each one cost the full 100 ms timeout and a pooled connection while it waited.' },
        { at: 'br', badge: 'OPEN for 5 s', tone: 'err', ms: 0, title: 'Threshold reached: the breaker opens',
          detail: 'For the cooldown period no request is sent to Pricing at all, which also gives the overloaded service room to recover.' },
        { path: ['h', 'br'], label: 'GET /price', ms: 0, title: 'The next checkout arrives',
          detail: 'Same request as before.' },
        { at: 'br', badge: 'OPEN → fail fast', tone: 'warn', ms: 0, title: 'Rejected in microseconds, no network call',
          detail: 'The caller gets an immediate error instead of waiting 100 ms. Retrying into an open breaker would defeat it, so the retry policy must not.' },
        { path: ['br', 'fb', 'br'], label: 'last known price', badgeAt: 'fb', badge: 'degraded', ms: 1, title: 'Use the fallback',
          detail: 'A cached price (with a staleness limit) keeps checkout working. Where no safe fallback exists, return a clear error quickly.' },
        { path: ['br', 'h'], label: '200 · cached price', tone: 'ok', ms: 0, title: 'Checkout stays up, degraded',
          detail: 'The failure stayed contained: checkout\'s threads and connections are not tied up waiting on Pricing.' },
      ],
    },
    {
      id: 'half', name: 'Recovery: half-open probe',
      summary: 'After the cooldown the breaker goes <b>half-open</b> and lets a single trial request through. Its result decides whether the circuit closes or opens for another cooldown.',
      steps: [
        { at: 'br', badge: 'cooldown over → HALF-OPEN', tone: 'warn', ms: 0, title: 'Cooldown elapsed',
          detail: 'The breaker doesn\'t know whether Pricing recovered. Sending all traffic at once could knock it over again.' },
        { path: ['h', 'br', 'dep'], label: 'trial call', ms: 20, title: 'One probe request goes through',
          detail: 'Other concurrent calls keep using the fallback until the probe answers.' },
        { path: ['dep', 'br'], label: '200', tone: 'ok', ms: 20, title: 'The probe succeeds',
          detail: 'If it had failed, the breaker would reopen for another cooldown, often with a growing interval.' },
        { at: 'br', badge: 'CLOSED', tone: 'ok', ms: 0, title: 'The circuit closes',
          detail: 'Traffic returns. Pairing this with jittered retries and a retry budget keeps recovering clients from stampeding the dependency together.' },
        { path: ['br', 'h'], label: 'live price', tone: 'ok', ms: 0, title: 'Back to normal',
          detail: 'Fresh prices again, and the fallback cache is refreshed as calls succeed.' },
      ],
    },
  ],
});

/* ================================== deadlock and lock ordering (CS/05 §3) == */
const LcsDL = lane([
  { label: 'THREAD 1', nodes: [
    { id: 't1', label: 'Thread 1', sub: 'transfer(A → B)', icon: 'thread', row: 0.5 }] },
  { label: 'LOCKS', nodes: [
    { id: 'la', label: 'Lock A', sub: 'account 1', icon: 'lock', row: 0 },
    { id: 'lb', label: 'Lock B', sub: 'account 2', icon: 'lock', row: 1 },
    { id: 'wf', label: 'Lock manager', sub: 'waits-for graph', icon: 'graph', row: 2 }] },
  { label: 'THREAD 2', nodes: [
    { id: 't2', label: 'Thread 2', sub: 'transfer(B → A)', icon: 'thread', row: 0.5 }] },
]);
defineFlow('flow-deadlock', {
  title: 'Live flow: a deadlock, and the two ways out',
  hint: 'Two transfers in opposite directions each grab one lock and wait for the other. Then see lock ordering prevent the cycle, and a database lock manager detect it and abort a victim.',
  zones: LcsDL.zones, h: LcsDL.h, nodes: LcsDL.nodes,
  edges: [['t1', 'la'], ['t1', 'lb'], ['t2', 'la'], ['t2', 'lb'], ['wf', 't1'], ['wf', 't2']],
  scenarios: [
    {
      id: 'dead', name: 'Deadlock: circular wait',
      summary: 'Each thread locks its <b>source</b> account first. With opposite directions, that is opposite orders, and all four Coffman conditions hold at once.',
      steps: [
        { path: ['t1', 'la'], label: 'lock A', tone: 'ok', badgeAt: 'la', badge: 'held by T1', ms: 0, title: 'Thread 1 locks account 1',
          detail: 'Mutual exclusion: only one holder at a time.' },
        { path: ['t2', 'lb'], label: 'lock B', tone: 'ok', badgeAt: 'lb', badge: 'held by T2', ms: 0, title: 'Thread 2 locks account 2',
          detail: 'Both threads are running in parallel on different cores; so far nothing is wrong.' },
        { path: ['t1', 'lb'], label: 'lock B?', tone: 'warn', badgeAt: 't1', badge: 'waiting for T2', ms: 0, title: 'Thread 1 now needs account 2',
          detail: 'Hold and wait: T1 keeps lock A while it blocks on lock B.' },
        { path: ['t2', 'la'], label: 'lock A?', tone: 'warn', badgeAt: 't2', badge: 'waiting for T1', ms: 0, title: 'Thread 2 now needs account 1',
          detail: 'Circular wait: T1 waits for T2, T2 waits for T1. No preemption: nobody can take a lock away.' },
        { at: 't1', badge: 'blocked forever', tone: 'err', ms: 0, title: 'Nobody can ever progress',
          detail: 'CPU usage drops to zero; requests pile up behind these threads. A thread dump shows the cycle: each is "waiting for a lock held by" the other.' },
      ],
    },
    {
      id: 'order', name: 'Fix: global lock order',
      summary: 'Both threads lock the <b>lower account ID first</b>, whatever the transfer direction. A cycle needs someone to take the locks in the opposite order, so it can\'t form.',
      steps: [
        { path: ['t1', 'la'], label: 'lock A (lower id)', tone: 'ok', badgeAt: 'la', badge: 'held by T1', ms: 0, title: 'Thread 1 locks the lower ID first',
          detail: 'For transfer(A → B), that is A.' },
        { path: ['t2', 'la'], label: 'lock A (lower id)', tone: 'warn', badgeAt: 't2', badge: 'waits, holds nothing', ms: 0, title: 'Thread 2 also starts with A',
          detail: 'For transfer(B → A), the lower ID is still A, so T2 waits without holding B. Hold-and-wait with a cycle is impossible.' },
        { path: ['t1', 'lb'], label: 'lock B', tone: 'ok', badgeAt: 'lb', badge: 'held by T1', ms: 0, title: 'Thread 1 takes B and does the transfer',
          detail: 'Nobody else can hold B while waiting for A, so this never blocks for long.' },
        { at: 't1', badge: 'transfer done · unlock B, A', tone: 'ok', ms: 0, title: 'Thread 1 finishes and releases both',
          detail: 'The critical section was short: no I/O or callbacks while holding the locks.' },
        { path: ['t2', 'la'], label: 'acquire A', tone: 'ok', badgeAt: 'la', badge: 'held by T2', ms: 0, title: 'Thread 2 gets A',
          detail: 'It was simply queued behind T1.' },
        { path: ['t2', 'lb'], label: 'acquire B', tone: 'ok', badgeAt: 't2', badge: 'transfer done', ms: 0, title: 'Thread 2 completes',
          detail: 'Both transfers succeed and the total balance is conserved. This is the fix for LeetCode 1226 (dining philosophers) too.' },
      ],
    },
    {
      id: 'detect', name: 'Database: detect and abort',
      summary: 'A database can\'t impose an order on arbitrary SQL, so it lets the cycle happen, <b>detects</b> it in a waits-for graph, and aborts one transaction.',
      steps: [
        { path: ['t1', 'la'], label: 'UPDATE row 1', tone: 'ok', badgeAt: 'la', badge: 'row lock T1', ms: 0, title: 'Transaction 1 locks row 1',
          detail: 'Row locks are taken implicitly by <code>UPDATE</code> and held until commit.' },
        { path: ['t2', 'lb'], label: 'UPDATE row 2', tone: 'ok', badgeAt: 'lb', badge: 'row lock T2', ms: 0, title: 'Transaction 2 locks row 2',
          detail: 'Opposite order, exactly as in the first scenario.' },
        { path: ['t1', 'lb'], label: 'UPDATE row 2', tone: 'warn', ms: 0, title: 'T1 blocks on row 2',
          detail: 'Waiting is normal; the lock manager records the edge T1 → T2.' },
        { path: ['t2', 'la'], label: 'UPDATE row 1', tone: 'warn', ms: 0, title: 'T2 blocks on row 1',
          detail: 'The edge T2 → T1 closes a cycle.' },
        { at: 'wf', badge: 'cycle T1 → T2 → T1', tone: 'err', ms: 1000, title: 'The deadlock detector finds the cycle',
          detail: 'Postgres checks after <code>deadlock_timeout</code> (1 s by default); InnoDB detects immediately by default. Finding a cycle is a graph search, like course-schedule cycle detection.' },
        { path: ['wf', 't2'], label: 'abort victim', tone: 'err', badgeAt: 't2', badge: 'ERROR: deadlock detected', ms: 0, title: 'One transaction is rolled back',
          detail: 'Its locks are released and the client gets an error it must <b>retry</b>. Application code that never retries turns this into a user-visible failure.' },
        { path: ['wf', 't1'], label: 'proceed', tone: 'ok', badgeAt: 't1', badge: 'COMMIT', ms: 0, title: 'The survivor commits',
          detail: 'Consistently ordering updates (e.g. by primary key) in your transactions makes these aborts rare.' },
      ],
    },
  ],
});

/* ================================= CPython dict: lookup, probe, resize (CS/06 §1) == */
const LdsDict = lane([
  { label: 'YOUR CODE', nodes: [
    { id: 'code', label: 'd[key]', sub: 'lookup or insert', kind: 'client', icon: 'code', row: 1 }] },
  { label: 'HASHING', nodes: [
    { id: 'hash', label: 'hash(key)', sub: '64-bit integer', icon: 'number', row: 1 }] },
  { label: 'INDEX TABLE', nodes: [
    { id: 'idx', label: 'Index table', sub: 'sparse, small ints', kind: 'cache', icon: 'grid', row: 1 },
    { id: 'grow', label: 'Resize', sub: 'bigger table', icon: 'layers', row: 2 }] },
  { label: 'ENTRIES', nodes: [
    { id: 'ent', label: 'Entries array', sub: 'hash, key, value', kind: 'db', icon: 'table', row: 1 }] },
]);
defineFlow('flow-dict-lookup', {
  title: 'Live flow: inside a CPython dict lookup',
  hint: 'A dict is two arrays: a sparse index table that open addressing probes, and a dense entries array in insertion order. Follow a hit, a collision, and an insert that forces a resize.',
  zones: LdsDict.zones, h: LdsDict.h, nodes: LdsDict.nodes,
  edges: [['code', 'hash'], ['hash', 'idx'], ['idx', 'ent'], ['idx', 'grow'], ['grow', 'ent']],
  scenarios: [
    {
      id: 'hit', name: 'Hit on the first probe',
      summary: 'The common case: one hash, one slot in the index table, one entry. Every step is a few nanoseconds, which is why dict lookups are "O(1)".',
      steps: [
        { path: ['code', 'hash'], label: "d['apple']", ms: 0, title: 'Hash the key',
          detail: 'For a <code>str</code> the hash is computed once and cached inside the string object, so repeat lookups skip this work. Hashing a long key the first time is O(length).' },
        { path: ['hash', 'idx'], label: 'i = h & 7', ms: 0, badgeAt: 'idx', badge: 'slot 5', title: 'Pick the home slot',
          detail: 'The table has 8 slots (a power of two), so the low 3 bits of the hash choose the slot: a mask, not a division.' },
        { path: ['idx', 'ent'], label: 'entry #2', ms: 0, title: 'The slot holds an index, not the entry',
          detail: 'Index-table slots are tiny integers (1 byte each for small dicts) pointing into the dense entries array. That split, the "compact dict" (3.6+), saves memory and keeps insertion order.' },
        { at: 'ent', badge: 'hash equal → key equal', tone: 'ok', ms: 0, title: 'Compare, cheapest check first',
          detail: 'First identity (<code>is</code>), then the full hash, and only if those match, <code>==</code>. A different hash rules the entry out without calling <code>__eq__</code>.' },
        { at: 'code', badge: 'value returned', tone: 'ok', ms: 0, title: 'Return the value',
          detail: 'One hash, one index read, one entry read: constant work no matter how many keys the dict holds.' },
      ],
    },
    {
      id: 'collide', name: 'Collision, then a miss',
      summary: 'Two keys can share a home slot. CPython then follows a <b>perturbed</b> probe sequence that mixes in higher hash bits, so colliding keys spread out instead of clustering.',
      steps: [
        { path: ['code', 'hash'], label: "d['pear']", ms: 0, title: 'Hash the key', detail: 'Same first step as always.' },
        { path: ['hash', 'idx'], label: 'slot 5', ms: 0, title: 'Home slot is taken',
          detail: 'Slot 5 already points at the entry for <code>\'apple\'</code>.' },
        { path: ['idx', 'ent'], label: 'entry #2', tone: 'warn', ms: 0, badgeAt: 'ent', badge: 'hash differs: skip', title: 'Not our key',
          detail: 'The stored hash differs, so the entry is rejected without comparing strings.' },
        { at: 'idx', badge: 'i = (5i + 1 + perturb) & 7', ms: 0, title: 'Probe the next slot',
          detail: 'The recurrence visits every slot eventually; <code>perturb</code> starts as the full hash and is shifted right by 5 bits each step, so higher bits influence the path.' },
        { path: ['idx', 'ent'], label: 'entry #4', tone: 'ok', ms: 0, title: 'Found on the second probe',
          detail: 'With the table kept at most 2/3 full, the expected number of probes stays small (see §11 for measured probe lengths).' },
        { at: 'idx', badge: 'empty slot → KeyError', tone: 'err', ms: 0, title: 'A missing key stops at an empty slot',
          detail: 'Looking up a key that was never inserted probes until it reaches an empty slot, which proves absence. Deleted entries leave a <b>dummy</b> (tombstone) so this stop rule stays correct.' },
      ],
    },
    {
      id: 'resize', name: 'Insert that forces a resize',
      summary: 'An 8-slot table accepts only 5 entries (2/3 full). The 6th insert rebuilds everything: the one O(n) insert that keeps all the others O(1).',
      steps: [
        { path: ['code', 'hash'], label: "d['fig'] = 6", ms: 0, title: 'Insert a sixth key', detail: 'The table already holds 5 entries in 8 slots.' },
        { path: ['hash', 'idx'], label: 'usable = 0', tone: 'warn', ms: 0, title: 'No usable slots left',
          detail: 'CPython tracks how many more inserts fit before the 2/3 limit. It is now zero.' },
        { path: ['idx', 'grow'], label: 'resize', tone: 'warn', ms: 0, badgeAt: 'grow', badge: '8 → 16 slots', title: 'Allocate a bigger table',
          detail: 'The new size is the smallest power of two that fits about 3 × the live entries, so the table roughly doubles here and each resize is followed by many cheap inserts (amortized O(1)).' },
        { path: ['grow', 'ent'], label: 'copy live entries', ms: 0, title: 'Compact the entries array',
          detail: 'Live entries are copied in order and deleted ones are dropped. No <code>__hash__</code> call is needed: the hash is stored in each entry (or cached in the <code>str</code> key).' },
        { at: 'grow', badge: 're-probe each entry', ms: 0, title: 'Rebuild the index table',
          detail: 'Every entry is placed again with the new mask. This is the O(n) step, and why latency-sensitive code pre-sizes big maps.' },
        { path: ['grow', 'ent'], label: 'append fig', tone: 'ok', ms: 0, title: 'The new entry goes at the end',
          detail: 'Appending to the dense array is what makes iteration follow insertion order, a language guarantee since Python 3.7.' },
        { at: 'code', badge: 'insert done', tone: 'ok', ms: 0, title: 'Insert complete',
          detail: 'The next 4 inserts fit without any resize (16 slots × 2/3 ≈ 10 entries).' },
      ],
    },
  ],
});
}
