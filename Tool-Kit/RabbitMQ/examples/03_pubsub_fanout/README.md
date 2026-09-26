# 03 PubSub Fanout (Python)

**Goal:** Deliver a message to multiple consumers at once.

**Deep Concept Explanation:**
The `fanout` exchange broadcasts all the messages it receives to all the queues it knows. Here, we create temporary, exclusive queues for our consumers and bind them to the fanout exchange.\n