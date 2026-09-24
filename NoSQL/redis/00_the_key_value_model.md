# The Key-Value Model

Redis (**RE**mote **DI**ctionary **S**erver) is an in-memory data structure store. Strip
away every command and data type and what's left is one idea: **a giant dictionary that
lives in RAM, that many processes can share over the network.** Everything else in this
module — sorted sets, pub/sub, transactions, locks — is built on top of that one idea, so
it is worth understanding precisely before touching a single command.

## Mental model: RAM + one thread + a event loop

Three properties explain almost everything about how Redis behaves:

1. **The dataset lives in RAM.** Every `GET`, `HSET`, `ZADD` is a memory access, not a disk
   seek. That is *why* Redis is fast — not because the code is exceptionally clever, but
   because RAM is roughly 100,000x faster than a disk seek and 100x faster than an SSD
   read. Persistence (level 10) exists to survive restarts, but the read/write path never
   waits on disk.

2. **Commands run on a single thread.** A classic misconception is "single-threaded means
   slow." It's the opposite, for this workload. Redis's command execution is single-threaded
   (newer versions offload I/O and some background work to helper threads, but the part
   that mutates your data structures is one thread), which means:
   - **No lock contention.** A `HSET` never blocks waiting for another thread's lock on the
     same hash. There is no such lock, because there is no such other thread.
   - **Every command is atomic by construction.** `INCR` can never race with another
     `INCR` on the same key, because only one command executes at any instant. You get
     atomicity for free on single commands — this is the foundation levels 02, 04, and 07
     all lean on.
   - The cost: one very slow command (a `KEYS *` over 10 million keys, an unbounded
     `SMEMBERS`) blocks *every other client* for its whole duration. There is no other
     thread to pick up slack. Watching out for O(n) commands on large collections is a
     running theme in this module.

3. **It's event-driven, not blocking-per-connection.** Redis uses an event loop (built on
   epoll/kqueue) to multiplex thousands of client sockets on that one thread, similar in
   shape to Node.js's event loop. It never dedicates an OS thread per connection, which is
   how a single Redis instance handles tens of thousands of concurrent clients on modest
   hardware.

```arch
%% caption: Redis serves every client from one event-loop thread over in-memory structures, and persists to disk in the background.
group cl "Clients" color=slate icon=users
node c1 "client A" at 0,0 in cl icon=client
node c2 "client B" at 1,0 in cl icon=client
node c3 "client C" at 2,0 in cl icon=client
node el "Event loop" at 1,1 icon=thread sub="single thread"
node ds "In-memory data structures" at 0,2 icon=memory
node disk "Disk: RDB / AOF" at 2,2 icon=disk
c1 -> el
c2 -> el : "socket"
c3 -> el
el -> ds : "reads/writes memory"
el ..> disk : "snapshot / append"
```

## What this buys you, and what it costs

| Property | Consequence |
|---|---|
| RAM-resident | Sub-millisecond latency for simple ops; dataset size is bounded by RAM, not disk |
| Single-threaded execution | Every individual command is atomic; no data-structure locking; but one slow command stalls all clients |
| Event loop | Cheap to hold many idle connections open (good for pub/sub, session stores) |
| Optional persistence | You choose the durability/performance tradeoff (level 10) rather than getting it for free |

This is a different bet from a disk-backed database like Postgres or MongoDB, which trade
some raw speed for datasets far larger than RAM and stronger default durability. Redis is
usually not your system of record — it's the fast layer in front of, or beside, one.

## Where Redis actually gets used

Because it's a fast, atomic, shared in-memory dictionary reachable over the network, the
same primitive shows up in very different roles:

- **Cache** — store the expensive result of a DB query or API call, keyed by its inputs
  (level 05).
- **Session store** — a web app's load balancer can route a user to any of N app servers;
  none of them can hold session state in local memory, so it goes in Redis instead
  (level 11).
- **Queue / job buffer** — `LPUSH`/`BRPOP` turn a Redis list into a simple work queue
  (level 03).
- **Rate limiter** — atomic counters with expiry, shared across every app server instance,
  not just one process (level 09).
- **Leaderboard** — sorted sets keep a score-ordered ranking updated in real time
  (level 04).
- **Pub/sub** — fan out an event to every subscriber currently connected, with no
  persistence (level 06).

Every one of those is really the same trick: cheap atomic reads/writes on shared state,
visible to every process in your fleet at once. The rest of this module builds up from
`SET`/`GET` to each of these in turn.

## What's next

Level 01 connects to a real Redis instance from both `redis-cli` and Python and runs the
first commands. Everything after that adds one data type or one pattern at a time.
