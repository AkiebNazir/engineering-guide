# 04 Routing Direct (Python)

**Goal:** Route messages selectively to different queues based on a routing key.

**Deep Concept Explanation:**
The `direct` exchange routes messages to queues whose binding key exactly matches the routing key of the message. This allows us to subscribe to only a subset of messages (e.g. only 'error' logs).\n