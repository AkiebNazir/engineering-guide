import re

with open("SystemDesign/solutions/040_distributed_lock_service_solution.md", "r") as f:
    content = f.read()

mermaid_1 = """```mermaid
%% caption: A master failover shorter than the grace period costs clients a jeopardy pause but not their sessions or locks.
sequenceDiagram
    participant C as Client library
    participant M1 as Old master
    participant M2 as New master
    C->>M1: KeepAlive
    M1-->>C: lease extended 12 s
    Note over M1: master crashes
    Note over C: local lease runs out, state JEOPARDY, cache flushed, calls block
    Note over M2: elected, new epoch, assumes every lease runs 12 s from now
    C->>M2: KeepAlive within 45 s grace
    M2-->>C: session kept plus fail-over event
    Note over C: state SAFE, cache cold, locks intact
```"""

arch_1 = """```arch
%% caption: A master failover shorter than the grace period costs clients a jeopardy pause but not their sessions or locks.
grid 100x100
node C "Client library" at 0,0
node M1 "Old master" at 1,0
node M2 "New master" at 2,0
C -> M1 : "1. KeepAlive"
M1 -> C : "2. lease extended 12 s"
C -> M2 : "3. KeepAlive within 45 s grace"
M2 -> C : "4. session kept plus fail-over event"
```"""

mermaid_2 = """```mermaid
%% caption: The paused holder wakes up and writes with token 812 but the resource has already seen 907 and rejects it.
sequenceDiagram
    participant A as Holder A
    participant S as Lock cell
    participant B as Holder B
    participant R as Resource
    A->>S: Acquire lock
    S-->>A: token 812
    Note over A: 15 s pause, lease lapses
    B->>S: Acquire lock
    S-->>B: token 907
    B->>R: write with 907
    R-->>B: ok, max token now 907
    A->>R: write with 812
    R-->>A: rejected 812 below 907
```"""

arch_2 = """```arch
%% caption: The paused holder wakes up and writes with token 812 but the resource has already seen 907 and rejects it.
grid 100x100
node A "Holder A" at 0,0 sub="15 s pause, lease lapses"
node S "Lock cell" at 1,0
node B "Holder B" at 2,0
node R "Resource" at 3,0

A -> S : "1. Acquire lock"
S -> A : "2. token 812"
B -> S : "3. Acquire lock"
S -> B : "4. token 907"
B -> R : "5. write with 907"
R -> B : "6. ok, max token now 907"
A -> R : "7. write with 812"
R -> A : "8. rejected 812 below 907"
```"""

content = content.replace(mermaid_1, arch_1)
content = content.replace(mermaid_2, arch_2)

with open("SystemDesign/solutions/040_distributed_lock_service_solution.md", "w") as f:
    f.write(content)

