# Persistence: RDB and AOF

Level 00 was clear that Redis's dataset lives in RAM. RAM is volatile — a process
restart, a container recreate, a host reboot, and everything in memory is gone unless
Redis wrote it to disk first. Redis has two independent, combinable persistence
mechanisms, and picking between (or combining) them is a genuine durability/performance
tradeoff, not a "just turn on the safe one" choice.

## RDB: point-in-time snapshots

RDB (**R**edis **D**ata**B**ase) writes the *entire dataset* to a single compact binary
file (`dump.rdb`) at a point in time — either on a schedule (`save 3600 1 300 100 60
10000` — save if 1+ keys changed in 3600s, or 100+ changed in 300s, or 10000+ changed in
60s) or on demand.

```bash
CONFIG GET save
# "3600 1 300 100 60 10000"   -- the default schedule

BGSAVE     # fork a child process, snapshot the dataset to dump.rdb, don't block clients
```

Run against the live lab instance:

```
$ docker exec dsa-redis redis-cli CONFIG GET save
save
3600 1 300 100 60 10000
$ docker exec dsa-redis redis-cli SET lab10:probe hello
OK
$ docker exec dsa-redis redis-cli BGSAVE
Background saving started
$ docker exec dsa-redis redis-cli INFO persistence | grep rdb_last_save_time
rdb_last_save_time:1790161232
```

**Go (`go-redis/v9`):** the shell commands above are what you'd run by hand; a real
service that needs to trigger or check persistence programmatically (an admin
endpoint, a pre-shutdown hook) does it through the client instead:

```go
save, _ := r.ConfigGet(ctx, "save").Result()
status, _ := r.BgSave(ctx).Result()
```

Real output:

```text
CONFIG GET save -> map[save:3600 1 300 100 60 10000]
BGSAVE -> Background saving started
```

**How `BGSAVE` avoids blocking**: Redis `fork()`s a child process. The child inherits a
copy-on-write view of the parent's memory and writes it out while the parent keeps
serving requests normally. This is why RDB snapshotting barely dents throughput — the
tradeoff is instead about the fork itself needing enough free memory headroom for the
OS's copy-on-write pages to diverge during a busy write workload.

**RDB's durability gap**: everything written *since* the last snapshot is lost on a crash.
With the default schedule, a crash 10 minutes after the last save can lose up to 10
minutes of writes. That's the whole tradeoff: fast, compact, cheap to restore from — and
lossy for anything written after the last snapshot.

## AOF: append-only file

AOF instead logs every write command as it happens, appended to a file, and replays that
log on startup to rebuild state. Turning it on:

```bash
CONFIG SET appendonly yes
```

Run against the live instance:

```
$ docker exec dsa-redis redis-cli CONFIG SET appendonly yes
OK
$ docker exec dsa-redis redis-cli INFO persistence | grep -E "aof_enabled|aof_last_write_status"
aof_enabled:1
aof_last_write_status:ok
$ docker exec dsa-redis ls -la /data
drwx------ 2 redis redis 4096 Sep 23 11:00 appendonlydir
-rw------- 1 redis redis  518 Sep 23 11:00 dump.rdb
```

**Go:** `r.ConfigSet(ctx, "appendonly", "yes")`, then read `INFO persistence`'s reply
(a single newline-delimited string in both `redis-py` and `go-redis` — Redis's `INFO`
command has always returned a flat text blob, not a structured reply) and pick out the
same two lines:

```text
aof_enabled:1
aof_last_write_status:ok
```

Both an `appendonlydir` (AOF, modern multi-file format) and a `dump.rdb` (RDB) can coexist
on disk — enabling one doesn't remove the other, and Redis can be configured to use both.

AOF's durability knob is `appendfsync`, which controls how often the log is actually
flushed to disk (as opposed to just handed to the OS's page cache):

| `appendfsync` | Durability | Performance |
|---|---|---|
| `always` | Every write is fsynced before acknowledging — near-zero data loss on crash | Slowest — one disk fsync per write |
| `everysec` (default) | Fsync once per second in a background thread | Good default — at most ~1 second of writes lost on a crash |
| `no` | Let the OS decide when to flush | Fastest, but a crash can lose whatever the OS hadn't flushed yet |

## The actual tradeoff

| | RDB | AOF |
|---|---|---|
| What's on disk | Full snapshot at a point in time | Every write command, replayed on startup |
| Data loss window on crash | Up to the whole gap since last snapshot | At most ~1 second with `everysec` (or none with `always`) |
| File size | Compact (just current state) | Grows continuously — needs periodic rewrite/compaction |
| Restart speed | Fast (load one binary snapshot) | Slower (replay the whole log, though the modern AOF format also embeds a base RDB to speed this up) |
| Restore/backup use | Trivial to copy and ship elsewhere | Less convenient as a portable backup format |

There's no universally "correct" choice — it depends on what you're using Redis for. If
it's a pure cache (level 05) and everything can be rebuilt from the real source of truth
on a cold start, you might reasonably disable persistence entirely (`save ""`,
`appendonly no`) and accept a cold, empty cache after a restart — durability doesn't
matter for disposable data. If Redis is holding data with no other copy (a queue whose
jobs would be lost, a session store where losing sessions logs everyone out), AOF with
`everysec` (or `always` for the most critical data) is the safer default. Many production
setups run both: RDB for fast, portable full backups, AOF for tighter recovery-point
objectives between snapshots.

## Common mistakes

- **Assuming persistence is "on" by default in a way that matches your durability needs.**
  RDB's default schedule can lose a meaningful window of writes; check `CONFIG GET save`
  and `CONFIG GET appendonly` rather than assuming.
- **Running `BGSAVE` (or letting the scheduled snapshot fire) on a host with too little
  free memory headroom** for the copy-on-write fork under a heavy write load — this can
  cause memory pressure or even OOM at exactly the wrong moment.
- **Treating a cache-only Redis instance's persistence config the same as a system-of-
  record instance's.** They have opposite right answers — decide deliberately, not by
  leaving the default.

## What's next

Level 11 ties everything in this module together into one small capstone service: a
connection-pooled, retrying, timeout-aware client combining a session store, a cache, and
a rate limiter.
