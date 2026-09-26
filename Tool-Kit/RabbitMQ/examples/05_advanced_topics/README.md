# 05 Advanced Topics (Python)

**Goal:** Route messages to queues based on multiple criteria using wildcard patterns.

**Deep Concept Explanation:**
The `topic` exchange routes messages to queues based on a wildcard match between the routing key and the routing pattern specified in the queue binding.
- `*` (star) can substitute for exactly one word.
- `#` (hash) can substitute for zero or more words.\n