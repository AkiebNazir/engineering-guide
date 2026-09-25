```arch
%% caption: A purge is one small ordered message committed to a durable log and fanned down a relay tree, and sequence numbers let a slow or partitioned POP catch up exactly.
node C "Customer" at 0,0 icon=client
node A "Purge API & log" at 0,1 icon=api sub="appends seq, quorum commit"
node R "Regional relay" at 0,2 icon=cache
node P "POP agent" at 0,3 icon=server
node S "POP servers" at 0,4 icon=server

C -> A : "purge tag product-42"
A -> C : "202 purge_id and seq"
A -> R : "batch every 50 ms"
R -> P : "batch up to seq 918273"
P -> S : "broadcast, apply on every server"
S -> P : "applied_seq 918273"
P -> R : "ack, feeds GET purges"
```
