Everything to master for the Google Senior SWE loop
Work through each section, open a topic to see exactly what to learn and which problems to practice, and tick it only when you pass its mastery check. Your ticks are saved in this browser.

No syllabus can promise a 100% result. Interviewer fit, a bad day, or team-matching headcount all add variance. The goal here is to make you consistently above the bar in every round, so one off moment doesn't decide the outcome.

Google doesn't publish its internal rubric. This plan is based on Google's public hiring guidance and widely reported candidate and interviewer accounts.

How you're actually scored
Understand what interviewers write down about you, because that's what the hiring committee reads.

Each interviewer submits written feedback and a hire rating. A hiring committee of senior engineers who never met you reads the whole packet together. You're commonly assessed on four attributes:

General cognitive ability: how you break down an unfamiliar problem, reason about options, and use hints.
Role-related knowledge: your coding, data structures and algorithms, and system design skill.
Leadership: ownership, influencing without authority, mentoring, and driving ambiguous work to an outcome.
Googleyness: collaboration, comfort with ambiguity, humility, openness to feedback, and doing the right thing for users.
In coding rounds, interviewers typically judge four things: communication, problem solving, code quality, and verification (testing your own code). Reaching an optimal answer silently, with sloppy code and no testing, can still get a weak rating.

For L5 specifically, every round is also a leveling signal. A good solution that needed heavy guidance reads as L4. The same solution that you scoped, drove, and verified yourself reads as L5.

Mindset checks

I can explain the four attributes and what evidence each round produces
›
Before each practice session, name which attribute you're producing evidence for.


I understand why downleveling happens
›
It usually comes from needing hints in design, vague behavioral stories with small scope, or coding that works but wasn't driven independently. Map each of these to a section below.

Foundations before any problem solving
These make everything else faster. Skipping them is why people plateau at 300 problems.

Language mastery

Pick one interview language and know its standard library cold
›
Python: list slicing costs, dict/set operations, collections (deque, Counter, defaultdict), heapq (min-heap only, negate for max, tuples for priority), bisect, itertools, functools.cache, sorting with key, recursion depth limit.

Java: ArrayList, HashMap/HashSet, ArrayDeque as stack and queue, PriorityQueue with comparators, TreeMap/TreeSet (floorKey, ceilingKey, subMap), StringBuilder, integer overflow and long, equals/hashCode for custom keys.

C++: vector, unordered_map, map/set with lower_bound and upper_bound, priority_queue (max-heap by default, greater<> for min), deque, lambdas in sort, pair/tuple, references vs copies.

Mastery check: Write a Dijkstra, an LRU cache, and a trie in plain text with zero syntax lookups.


Write code without an IDE
›
Practice in a plain doc or on a whiteboard: no autocomplete, no running code. Build habits for helper functions, meaningful names, and consistent indentation. You'll have at least one in-person round, so also practice on paper or a whiteboard.

Mastery check: Three problems written in a plain doc compile on first run.

Complexity analysis

Big-O, and the reasoning behind it
›
Time and space for loops, nested loops, recursion (draw the recursion tree), and the master theorem for divide and conquer. Include recursion stack space, the hidden cost of string concatenation and slicing, and average vs worst case for hash maps.

Mastery check: State the complexity of any solution before being asked, including space.


Amortized analysis
›
Dynamic array resizing, monotonic stacks (each element pushed and popped once), union-find with path compression (inverse Ackermann), and sliding windows (each pointer moves at most n times).


Constraints to target complexity
›
Use input size to guess the expected algorithm: n up to about 20 suggests 2^n or bitmask; about 500 allows n³; about 10⁴ allows n²; 10⁵ to 10⁶ needs n log n or n; beyond that, log n or O(1) math.

Mastery check: Given only the constraints, predict the intended technique for 10 random problems.

Data structures and algorithms, topic by topic
Learn by pattern, not by problem. For each topic, study the ideas, solve the practice set without hints, then redo any failures after 3, 7, and 21 days.

Linear structures

Arrays and strings
›
Prefix sums (1D and 2D), difference arrays for range updates, Kadane's algorithm, in-place techniques (reverse, swap, Dutch national flag partition), matrix traversal (spiral, rotation, diagonals), frequency counting, expand-around-center for palindromes.

Practice: Product of Array Except Self, Subarray Sum Equals K, Maximum Subarray, Rotate Image, Spiral Matrix, Range Sum Query 2D, Sort Colors, Next Permutation, Longest Palindromic Substring

Mastery check: Recognize a prefix-sum-plus-hashmap problem within 2 minutes.


Hashing
›
O(1) lookup trade-offs, counting, grouping by canonical keys (sorted string, tuple of counts), hashing composite keys, rolling hash idea, worst-case behavior.

Practice: Two Sum, Group Anagrams, Longest Consecutive Sequence, Contiguous Array, Isomorphic Strings, Insert Delete GetRandom O(1)


Two pointers
›
Opposite ends on sorted data, same-direction read/write pointers, fast and slow pointers, merging two sorted sequences, and knowing when sorting first makes two pointers possible.

Practice: 3Sum, Container With Most Water, Trapping Rain Water, Remove Duplicates from Sorted Array, Boats to Save People


Sliding window
›
Fixed-size windows, variable windows that expand and shrink on a condition, a count map inside the window, the trick of exactly(K) = atMost(K) − atMost(K−1), and a monotonic deque for window max or min.

Practice: Longest Substring Without Repeating Characters, Minimum Window Substring, Longest Repeating Character Replacement, Permutation in String, Subarrays with K Different Integers, Sliding Window Maximum

Mastery check: Write the variable-window template from memory and explain its O(n) bound.


Linked lists
›
Dummy head nodes, reversal (iterative and recursive), reversing in groups, cycle detection and cycle start (Floyd), finding the middle, merging, reordering, deep copy with random pointers.

Practice: Reverse Linked List, Reverse Nodes in k-Group, Linked List Cycle II, Reorder List, Copy List with Random Pointer, Merge k Sorted Lists


Stacks, queues, and monotonic structures
›
Matching brackets, expression evaluation, decoding nested strings, monotonic stacks for next greater or smaller element, histogram areas, contribution technique (how many subarrays each element is the min of), min stack.

Practice: Daily Temperatures, Largest Rectangle in Histogram, Basic Calculator II, Decode String, Asteroid Collision, Remove K Digits, Sum of Subarray Minimums

Mastery check: Explain why each element is pushed and popped at most once.

Searching and sorting

Binary search
›
One template you trust, with a clear invariant (for example, find the first index where a condition becomes true). Apply it to rotated arrays, searching on the answer space (minimum capacity, speed, or maximum of minimums), 2D matrices, and floating-point precision loops.

Practice: Search in Rotated Sorted Array, Find Minimum in Rotated Sorted Array, Koko Eating Bananas, Capacity To Ship Packages Within D Days, Split Array Largest Sum, Time Based Key-Value Store, Median of Two Sorted Arrays

Mastery check: No off-by-one bugs across 10 binary search problems in a row.


Sorting and selection
›
Implement merge sort (and use it to count inversions), quicksort partitioning, quickselect with its average O(n) and worst-case behavior, counting and bucket sort, custom comparators, and stability.

Practice: Sort an Array (implement merge sort), Kth Largest Element in an Array (quickselect), Top K Frequent Elements (bucket sort), Largest Number, Count of Smaller Numbers After Self

Trees, heaps, and tries

Binary trees and BSTs
›
Recursive and iterative traversals (in, pre, post, level order), height and diameter, path sums, lowest common ancestor, BST validation, insert, delete, and successor, building a tree from traversals, serialization, and tree DP where a function returns multiple values from each child.

Practice: Binary Tree Maximum Path Sum, Lowest Common Ancestor of a Binary Tree, Validate Binary Search Tree, Serialize and Deserialize Binary Tree, Construct Binary Tree from Preorder and Inorder Traversal, Binary Tree Right Side View, All Nodes Distance K in Binary Tree, House Robber III, Kth Smallest Element in a BST

Mastery check: Write iterative inorder traversal from memory, and solve a tree DP problem by defining what each call returns.


Heaps and priority queues
›
Top-K, merging K sorted streams, two heaps for a running median, greedy scheduling with a heap, and lazy deletion.

Practice: Find Median from Data Stream, K Closest Points to Origin, Task Scheduler, Meeting Rooms II, IPO, Sliding Window Median


Tries
›
Insert, search, and prefix lookup, wildcard search with DFS, a trie combined with grid backtracking, and storing counts or top suggestions at nodes.

Practice: Implement Trie (Prefix Tree), Design Add and Search Words Data Structure, Word Search II, Search Suggestions System, Maximum XOR of Two Numbers in an Array

Graphs (Google asks these often)

Graph traversal
›
Adjacency lists vs matrices, BFS for unweighted shortest paths, DFS (recursive and iterative), grids as graphs, multi-source BFS, connected components, cycle detection (undirected with a parent, directed with three colors), bipartite checks, implicit graphs where states are nodes, bidirectional BFS.

Practice: Number of Islands, Rotting Oranges, Clone Graph, Pacific Atlantic Water Flow, Is Graph Bipartite?, Word Ladder, Open the Lock, Shortest Path in Binary Matrix, Surrounded Regions

Mastery check: Model a problem that doesn't look like a graph (such as a lock combination) as one within 5 minutes.


Ordering and connectivity
›
Topological sort (Kahn's algorithm and DFS), detecting impossible orderings, union-find with path compression and union by rank, minimum spanning trees (Kruskal and Prim).

Practice: Course Schedule II, Alien Dictionary, Number of Provinces, Redundant Connection, Accounts Merge, Min Cost to Connect All Points, Satisfiability of Equality Equations

Mastery check: Write union-find and Kahn's algorithm from memory in under 5 minutes each.


Bridges and strongly connected components
stretch
›
Tarjan's algorithm for bridges and articulation points, and Kosaraju or Tarjan for strongly connected components. These are less common, but they do appear at Google.

Practice: Critical Connections in a Network


Shortest paths
›
Dijkstra with a heap (and why it fails with negative edges), 0-1 BFS, Bellman-Ford and the limited-edges variant, Floyd-Warshall for small all-pairs graphs, and Dijkstra over augmented states (node plus extra information such as stops or keys). Know that A* exists.

Practice: Network Delay Time, Cheapest Flights Within K Stops, Path With Minimum Effort, Swim in Rising Water, Minimum Cost to Make at Least One Valid Path in a Grid, Evaluate Division

Mastery check: Explain the difference between marking nodes visited on push vs on pop in Dijkstra.

Recursion, backtracking, and dynamic programming

Backtracking
›
The choose, explore, unchoose template, subsets, permutations, and combinations (including with duplicates), pruning, and constraint satisfaction.

Practice: Subsets II, Permutations II, Combination Sum, Generate Parentheses, Word Search, Palindrome Partitioning, N-Queens, Sudoku Solver


Dynamic programming foundations
›
Define the state, transition, and base case in words before writing code. Go from recursion to memoization, then to bottom-up tables, then to space optimization. Cover 1D problems, grid paths, and 0/1 vs unbounded knapsack.

Practice: Climbing Stairs, House Robber II, Decode Ways, Word Break, Unique Paths II, Minimum Path Sum, Coin Change, Coin Change II, Partition Equal Subset Sum, Target Sum

Mastery check: For any DP problem, write the state definition in one sentence before coding.


DP on sequences and strings
›
Longest increasing subsequence in O(n²) and O(n log n), longest common subsequence, edit distance, palindromic subsequences, counting distinct subsequences, and regex or wildcard matching.

Practice: Longest Increasing Subsequence, Russian Doll Envelopes, Longest Common Subsequence, Edit Distance, Longest Palindromic Subsequence, Distinct Subsequences, Interleaving String, Regular Expression Matching


Advanced DP patterns
›
Interval DP, state-machine DP (stock problems with cooldowns, fees, or transaction limits), bitmask DP for n up to about 20, DP on DAGs and grids with memoized DFS, and counting modulo 10⁹+7.

Practice: Burst Balloons, Best Time to Buy and Sell Stock with Cooldown, Best Time to Buy and Sell Stock IV, Partition to K Equal Sum Subsets, Shortest Path Visiting All Nodes, Longest Increasing Path in a Matrix, Minimum Cost Tree From Leaf Values


Digit DP
stretch
›
Counting numbers in a range with digit constraints, using a tight flag. Rare, but useful to recognize.

Practice: Numbers At Most N Given Digit Set, Count Special Integers

Greedy, intervals, math, and advanced structures

Greedy algorithms and intervals
›
Justifying a greedy choice with an exchange argument, sorting by start vs end time, merging and inserting intervals, sweep line with start and end events, and jump-game reachability.

Practice: Merge Intervals, Insert Interval, Non-overlapping Intervals, Minimum Number of Arrows to Burst Balloons, Jump Game II, Gas Station, Car Pooling, My Calendar II, Employee Free Time, The Skyline Problem

Mastery check: Explain why your greedy approach is correct, not only that it passes the tests.


Bit manipulation and math
›
XOR properties, clearing the lowest set bit with x & (x−1), bitmasks for subsets, GCD and LCM, modular arithmetic and fast exponentiation, sieve of Eratosthenes, combinations, overflow handling, and randomness (Fisher-Yates shuffle, reservoir sampling, weighted random choice with prefix sums and binary search).

Practice: Single Number II, Counting Bits, Pow(x, n), Count Primes, Random Pick with Weight, Linked List Random Node, Shuffle an Array


Range query structures
stretch
›
Fenwick (binary indexed) trees, segment trees with point updates and range queries (know what lazy propagation does), and ordered maps for interval bookkeeping.

Practice: Range Sum Query - Mutable, My Calendar I, Count of Range Sum, Falling Squares

Mastery check: Implement a Fenwick tree from memory.


Design-style coding problems
›
Implement a class with several methods and clear complexity guarantees for each. These are common at Google and reward clean API design, well-chosen invariants, and edge-case handling.

Practice: LRU Cache, LFU Cache, Design Hit Counter, Logger Rate Limiter, Snapshot Array, Time Based Key-Value Store, Design Browser History, Flatten Nested List Iterator, Stock Price Fluctuation, Design Twitter

Mastery check: Write LRU cache with a hashmap and doubly linked list, bug-free, in under 15 minutes.

Google-style follow-ups to practice on every problem
After solving a problem, ask yourself the follow-ups Google interviewers like to add, and sketch an answer for each:

What if the input is a stream and you can't store it all?
What if the data doesn't fit in memory, or is spread across many machines?
What if there are millions of queries? What would you precompute?
What if multiple threads call this at once? What needs locking?
What if a constraint changes, such as negative numbers, duplicates, or a graph with cycles?
How to run a 45-minute coding round
Knowing algorithms is necessary but not sufficient. This is the execution layer interviewers actually score.

Minutes 0–5: clarify
Restate the problem. Ask about input size, value ranges, negatives, duplicates, empty input, whether it's sorted, the output format, and whether you can modify the input. Work through one small example by hand.
Minutes 5–12: design the approach
State a brute-force solution with its complexity, then improve it. Explain the optimal idea and its time and space complexity, and get the interviewer's agreement before coding.
Minutes 12–30: code
Write clean code with helper functions and clear names. Narrate key decisions briefly rather than every line.
Minutes 30–38: verify
Trace through your example line by line, then edge cases. Find and fix your own bugs before the interviewer points them out.
Minutes 38–45: follow-ups
Discuss optimizations, scaling, or variations. Usually a second, harder part arrives here.
Execution skills

Clarifying questions become automatic
›
Keep a personal list and use it on every practice problem until you no longer need it.


Edge case checklist
›
Empty input, a single element, all elements the same, negative numbers and zero, integer overflow, very large inputs, duplicates, disconnected graphs, cycles, and invalid input.


Thinking out loud without rambling
›
Record yourself solving a problem. Silence longer than about 30 seconds without a status update is a problem, and so is narrating every keystroke.

Mastery check: Watch a recording of yourself and note each stretch of unexplained silence.


Using hints well
›
When you get a hint, acknowledge it, connect it to your approach, and move on quickly. Arguing with a hint, or ignoring it, costs more than taking it.


Recovering when stuck
›
Go back to small examples, try a simpler version of the problem, or list techniques that match the constraints. Say what you're trying so the interviewer can see how you think.

System design concepts
This is the round that decides L5 vs L4. You need enough depth in each area to defend trade-offs when pushed, not just name the technology.

Basics

Back-of-envelope estimation
›
Latency orders of magnitude (memory in nanoseconds, SSD reads in microseconds, a cross-continent round trip around 150 ms), powers of two, about 86,400 seconds (roughly 10⁵) in a day. QPS = daily users × actions per user ÷ 86,400, then multiply by 2 to 3 for peak. Storage = record size × record count × replication factor × retention period. Also estimate bandwidth.

Mastery check: Estimate QPS, storage, and servers for a photo-sharing app in under 4 minutes.


Networking and APIs
›
DNS, TCP vs UDP, HTTP/1.1 vs HTTP/2 vs HTTP/3 (QUIC), TLS basics, REST vs gRPC vs GraphQL, WebSockets vs server-sent events vs long polling, CDNs, and API design: cursor vs offset pagination, idempotency keys, versioning, and error semantics.


Load balancing and service architecture
›
Layer 4 vs layer 7 load balancers, balancing algorithms (round robin, least connections, consistent hashing), stateless services, autoscaling, service discovery, API gateways, and monolith vs microservices trade-offs.

Data

Databases
›
Relational modeling and normalization, B-tree indexes (composite and covering), transactions, isolation levels and their anomalies (dirty reads, non-repeatable reads, phantoms, write skew), MVCC. The NoSQL families: key-value, wide-column, document, and graph. When to choose each.

Mastery check: Choose a database for 5 different systems and defend each choice against an alternative.


Storage engines
›
B-trees vs LSM-trees: write and read amplification, compaction, bloom filters, and why write-heavy systems like Bigtable use LSM designs.


Replication
›
Single leader (synchronous vs asynchronous), problems caused by replication lag (read-your-writes and monotonic reads), multi-leader conflicts, leaderless quorums (R + W > N), failover, and split brain.


Partitioning and sharding
›
Range vs hash partitioning, consistent hashing with virtual nodes, hot keys and key salting, local vs global secondary indexes, rebalancing, and choosing a shard key.


Caching
›
Where to cache (client, CDN, application, distributed cache), patterns (cache-aside, read-through, write-through, write-behind), eviction (LRU, LFU, TTL), invalidation strategies, preventing stampedes (request coalescing, jittered TTLs), and hot-key mitigation.


Specialized data structures and indexes
›
Blob storage with a separate metadata store, chunking and deduplication, inverted indexes and ranking basics (TF-IDF, BM25), geospatial indexes (geohash, quadtree, and S2 cells, which Google uses), time-series databases, and probabilistic structures (bloom filter, HyperLogLog, count-min sketch).

Distributed systems

Asynchronous processing and messaging
›
Queues vs logs, Kafka-style partitions, consumer groups, offsets, and per-partition ordering. Delivery guarantees (at most once, at least once, effectively once), idempotent consumers, the outbox pattern, dead-letter queues, and backpressure.

Mastery check: Explain how you'd avoid charging a customer twice when a message is redelivered.


Consistency and consensus
›
CAP and PACELC, linearizable vs causal vs eventual consistency, Raft basics (leader election, log replication, majorities), where Paxos fits, lock and coordination services (Chubby, ZooKeeper, etcd), leases and fencing tokens, clock issues (NTP drift, Lamport and vector clocks, Spanner's TrueTime), two-phase commit vs sagas.


Resilience patterns
›
Timeouts, retries with exponential backoff and jitter, circuit breakers, bulkheads, load shedding, graceful degradation, and rate limiting algorithms (token bucket, leaky bucket, fixed window, sliding log, sliding window counter).


Real-time collaboration
›
Operational transformation vs CRDTs, conflict resolution, presence, and offline edits syncing later.


Batch and stream processing
›
MapReduce and Spark for batch, Dataflow/Beam and Flink for streaming. Event time vs processing time, tumbling, sliding, and session windows, watermarks and late data, lambda vs kappa architectures, OLTP vs analytical warehouses like BigQuery.

Production concerns (these signal seniority)

Reliability and operations
›
SLIs, SLOs, SLAs, and error budgets. The four golden signals (latency, traffic, errors, saturation), alerting, logging, distributed tracing, canary and blue-green deployments, feature flags, rollbacks, multi-region disaster recovery (RPO and RTO), and capacity planning. Google's free SRE book covers most of this.

Mastery check: For any design, say how you'd monitor it and what happens when a region goes down.


Security and privacy
›
Authentication vs authorization, OAuth 2.0 and OpenID Connect, JWT trade-offs, encryption in transit and at rest, key management, least privilege, abuse and spam prevention, and handling personal data, including deletion requirements.


ML and AI systems
›
Offline training vs online serving, feature stores, model serving (batching, GPU utilization, latency budgets), embeddings and approximate nearest-neighbor search (HNSW, Google's ScaNN), recommendation pipelines (candidate generation, then ranking, then re-ranking), LLM serving concerns (token streaming, caching, rate limiting, cost), A/B testing, and monitoring model drift.

Google papers worth reading

Storage and compute: GFS, MapReduce, Bigtable
›
Read these for design reasoning. Focus on why they made each choice, not on memorizing details.


Coordination and databases: Chubby, Spanner
›
Locks and leases, global consistency, and TrueTime.


Analytics and infrastructure: Dremel, Borg, Zanzibar
›
Columnar querying at scale, cluster scheduling, and authorization at global scale.


Also useful: Amazon's Dynamo paper and the Dataflow model paper
›
Dynamo is the classic leaderless key-value design. The Dataflow paper explains windows and watermarks.

System design problems to practice
For each problem, do a full 45-minute design out loud, then check what you missed. The key challenges listed are where interviewers usually push.

Core set

URL shortener
›
ID generation (base62, counters vs hashing, collisions), read-heavy caching, 301 vs 302 redirects, custom aliases, expiration, click analytics.


Distributed rate limiter
›
Choosing an algorithm, atomic counters in a shared store, per-user and per-IP limits, synchronizing across regions, fail-open vs fail-closed behavior.


Unique ID generator
›
Snowflake-style bit layouts, clock skew, ordering guarantees, and running without a single point of failure.


Distributed key-value store
›
Consistent hashing, quorum replication, conflict resolution with vector clocks, gossip membership, hinted handoff, and anti-entropy with Merkle trees.


Distributed cache
›
Eviction, partitioning, replication, hot keys, cache warm-up, and consistency with the source of truth.


Search autocomplete
›
Tries with top-K suggestions at each node vs precomputed prefix tables, an offline aggregation pipeline, latency under 100 ms, sharding by prefix, personalization, and filtering offensive terms.


Web crawler
›
URL frontier with politeness and priority, deduplication of URLs and near-duplicate content, robots.txt, DNS caching, distributed workers, and crawler traps.


Notification system
›
Push, SMS, and email channels, templates, priorities, deduplication, retries, user preferences, and rate limits.

Social and communication

News feed
›
Fan-out on write vs on read, the hybrid approach for accounts with huge follower counts, ranking, pagination, and feed caching.


Chat application
›
WebSocket connection servers, message IDs and ordering, delivery and read receipts, offline sync, presence, group fan-out, and awareness of end-to-end encryption.


Google Docs
›
Operational transformation or CRDTs, session servers, snapshots plus operation logs, cursors and presence, permissions, and offline editing.

Google-scale products

Google Drive or Dropbox
›
File chunking, deduplication, metadata database, resumable uploads, delta sync, conflict handling, and notifying clients of changes.


YouTube
›
Upload pipeline, transcoding as a DAG of tasks, adaptive bitrate streaming (HLS or DASH), CDN strategy, view counting at scale, and thumbnails.


Web search
›
The crawl, index, and serve pipeline, sharding the inverted index, fanning queries out and merging results, ranking, freshness, and caching popular queries.


Google Maps or nearby places
›
Geospatial indexing with geohash, quadtrees, or S2, read-heavy traffic patterns, map tile serving, routing on a partitioned road graph, and ETA estimation.


Ride sharing
›
High-volume location updates, driver matching, geospatial sharding, a trip state machine, and making sure one driver isn't assigned to two riders.

Infrastructure and data

Distributed job scheduler
›
Job storage, time-based partitioning, leader election and leases, at-least-once execution with idempotency, retries, priorities, and cron-style schedules.


Metrics monitoring and alerting
›
Time-series ingestion, downsampling and retention tiers, the query layer, and evaluating alert rules at scale.


Ad click aggregation
›
Stream processing with windows, exactly-once counting, late events, and reconciling streaming results with batch recomputation.


Top-K trending items
›
Count-min sketch, windowed aggregation, approximate vs exact results, and combining counts from many servers.


Payment system
›
Idempotency, a double-entry ledger, reconciliation, integrating an external payment provider, and handling partial failures.


Ticket booking with flash sales
›
Seat holds with expiration, preventing overselling, heavy contention, and virtual waiting queues.


Real-time leaderboard
›
Sorted sets, sharding scores, tie-breaking, and real-time vs periodic ranking.


LLM-powered assistant feature
›
Request routing, token streaming, caching responses, rate limiting and quotas, cost control, safety filtering, and observability.

How to run a 45-minute design round
At L5 you should drive the whole conversation. The interviewer should mostly be reacting to you.

Minutes 0–5: requirements
List the core functional features and agree on what's out of scope. Then list non-functional requirements: scale, latency, availability vs consistency, durability, and read/write ratio.
Minutes 5–10: estimates and API
Estimate QPS, storage, and bandwidth, and say which numbers will shape the design. Define the main API endpoints.
Minutes 10–15: data model
Define entities, access patterns, database choice, and a first view of partitioning.
Minutes 15–25: high-level design
Draw clients, load balancers, services, storage, caches, and queues. Walk through a request end to end.
Minutes 25–38: deep dives
Pick the two hardest parts, such as fan-out, consistency, or hot keys. Compare alternatives and make an explicit decision.
Minutes 38–45: failure and evolution
Cover bottlenecks, failure modes, monitoring, multi-region, and what you would change at 10 times the scale.
Signals that read as L5

I state trade-offs explicitly and commit to a decision
›
For example: "I'll use asynchronous replication here. We accept a few seconds of stale reads in exchange for lower write latency, which fits this product."


I quantify instead of hand-waving
›
Use your estimates to justify caching, sharding, and replica counts.


I start simple and scale when the numbers require it
›
Over-engineering from the first minute is as much a red flag as under-designing.


I raise failure modes before being asked
›
What happens when the cache, a shard, or a whole region fails?


I adapt smoothly when the interviewer changes a requirement
›
Practice by having a mock partner add a surprise constraint halfway through.

Googleyness and leadership
This round heavily influences your level. Prepare it as seriously as coding.

Interviewers look for comfort with ambiguity, openness to feedback, willingness to challenge the status quo, putting users first, doing the right thing, caring about the team, bias to action, and humility. Expect both past-behavior questions ("Tell me about a time…") and hypothetical ones ("What would you do if…").

Answer structure
Use STAR plus a lesson: Situation and Task (about 20%), Action (about 60%, told with "I" and specific decisions), Result (with numbers), and what you learned. Keep each story to 2 to 3 minutes and prepare for follow-ups like "What would you do differently?" and "What did your manager think?"

Your story bank (write each one out)

Leading an ambiguous project end to end
›
How you defined the scope, aligned stakeholders, and delivered.


A technical decision with significant trade-offs
›
The alternatives, how you decided, and how you persuaded others.


Influencing without authority
›
Getting another team or a senior person to change direction.


Disagreeing with your manager or a peer
›
Show respect, data, a resolution, and disagreeing then committing where appropriate.


A failure or mistake you owned
›
Choose a real failure, not a disguised strength, and explain what changed afterward.


Mentoring someone to greater ownership
›
What they could do before and after, and your specific role.


Receiving hard feedback and acting on it
›
Show how your behavior actually changed.


Pushing back for users or quality
›
Stopping a risky launch or raising an uncomfortable concern.


Resolving team conflict or working with a difficult colleague
›
Focus on understanding their perspective and the outcome.


Prioritizing under a tight deadline
›
What you cut, why, and how you communicated it.


Handling a production incident
›
Calm response, communication, root cause, and prevention.


Improving a process or the team's productivity
›
Before-and-after impact.


Making sure quieter or different perspectives were heard
›
Inclusion within a team or a meeting.

Hypothetical questions to rehearse

Your team strongly disagrees with a product decision from leadership
›
Show how you gather data, escalate respectfully, and commit once decided.


A teammate consistently misses commitments
›
Show empathy and a private conversation first, then support, then escalation if needed.


You find a serious bug in a colleague's code the day before launch
›
Weigh user impact, communicate transparently, and propose options rather than blame.

Your own projects and resume
Interviewers will dig into what you've built. Vague answers here quietly damage your level.

For your top 2 to 3 projects

I can draw the architecture from memory
›
Include components, data flow, and storage choices.


I know the real numbers
›
Traffic, data size, latency, team size, timeline, and business impact.


I can separate my contribution from the team's
›
Name what you personally designed, decided, and led.


I can explain the alternatives we rejected and why
›
This is strong evidence of senior judgment.


I know what broke and what I'd do differently today
›
Shows reflection and growth.


Every line on my resume holds up to 5 minutes of follow-up
›
Remove or reword anything you can't defend in depth.


I have a crisp 2-minute career summary and a real answer for why Google
›
Used in the recruiter screen and often at the start of rounds.

A 12-week plan
Assumes about 2 to 3 hours on weekdays and 5 to 6 hours on weekend days. If you have less time, stretch it to 16 to 20 weeks rather than skipping topics.

Week	Coding	System design and behavioral
1	Language library, complexity, arrays, hashing, two pointers, sliding window	Start a mistakes log. List candidate stories.
2	Linked lists, stacks and monotonic structures, binary search, sorting	Estimation and networking basics
3	Trees, heaps, tries	APIs, load balancing, databases
4	Graph traversal, ordering, union-find	Storage engines, replication, partitioning
5	Shortest paths, backtracking	Caching, messaging. Write your first 5 stories.
6	DP foundations and DP on strings. First coding mock.	Consistency, consensus, resilience patterns
7	Advanced DP, greedy and intervals	Stream processing, search and geo indexes, SRE concepts. Finish all stories.
8	Bits and math, range query structures, design-style coding	Design: URL shortener, rate limiter, key-value store, autocomplete
9	Mixed Google-tagged sets. Second coding mock.	Design: news feed, chat, notifications, Docs, Drive. First design mock.
10	Timed sessions: 2 problems in 45 minutes	Design: YouTube, search, Maps, job scheduler, ad aggregation. Behavioral mock.
11	Full mock loops (4 rounds in one day), then fix the weakest area	Read the Google papers. Rehearse your projects deep dive.
12	Redo failed problems from your log. Light practice only.	Rest, logistics, and review your notes. Don't cram.
Daily habits
Log every problem you couldn't solve or got wrong, with the missing insight in one sentence. Redo those problems after 3, 7, and 21 days.
Give each problem 25 to 30 minutes before looking at a solution. If you look, re-solve it from scratch the next day.
Prioritize depth over count. 250 to 350 well-understood problems beat 800 memorized ones.
You're ready when you can tick all of these
Use these as honest checks, not rough impressions. If one is missing, that's where your next week goes.

Coding

I solve unseen medium problems in 25 minutes or less, 8 times out of 10, bug-free after my own testing

I solve unseen hard problems in about 40 minutes at least half the time, and reach a solid approach on the rest

I can write Dijkstra, union-find, topological sort, a trie, binary search, quickselect, an LRU cache, and a Fenwick tree from memory

My last 3 coding mocks, with strangers, came back as hire or strong hire
System design

I can design at least 15 of the listed systems in 45 minutes, with 2 real deep dives each

I've done at least 3 design mocks with experienced engineers, and the latest feedback was at the senior level

I can explain every trade-off I make and name at least one alternative
Behavioral and experience

I have 10 or more stories written out and rehearsed aloud, each under 3 minutes

I can map any common behavioral question to a story within 10 seconds

I can defend every project on my resume with numbers and trade-offs
Resources
Use a small number of resources deeply rather than many at the surface.

Coding practice: LeetCode (Google-tagged problems with premium), and the NeetCode roadmap for pattern-organized lists.
Algorithm implementations: cp-algorithms.com for trustworthy explanations of graphs, trees, and range queries.
Fundamentals book: Cracking the Coding Interview by Gayle Laakmann McDowell.
System design books: Designing Data-Intensive Applications by Martin Kleppmann (the most important one), and System Design Interview volumes 1 and 2 by Alex Xu.
Reliability: Google's SRE books, free online.
Mock interviews: interviewing.io for anonymous mocks with engineers from large tech companies, plus peers who are also preparing.
Google papers: search the titles listed in the system design section on Google Research.