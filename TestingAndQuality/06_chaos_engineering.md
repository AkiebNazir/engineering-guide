# Resilience: Chaos Engineering

"What happens if the database goes down?"
You can write unit tests that mock database exceptions, but you don't actually know what will happen in production until it happens in production.

**Chaos Engineering** is the discipline of experimenting on a distributed system in order to build confidence in its capability to withstand turbulent conditions.

## 1. Principles of Chaos Engineering

Popularized by Netflix's "Chaos Monkey" (a script that randomly killed production servers during business hours), the goal is not to cause chaos, but to verify that the system handles chaos gracefully.

1. **Define the Steady State**: The system must be healthy. (e.g., Error rate < 1%).
2. **Hypothesize**: "If the Redis cache is unreachable, the system will fall back to the Database. Latency will increase, but the error rate will stay < 1%."
3. **Introduce Chaos**: Use tools (like Gremlin or Chaos Mesh) to inject failure.
   - Kill a random Kubernetes Pod.
   - Inject 500ms of network latency between the Web and API tiers.
   - Block traffic to the AWS S3 IP range.
   - Max out CPU on the database server.
4. **Observe**: Did the steady state remain? Did the fallback mechanisms (circuit breakers, retries) actually work?
5. **Fix**: If the system crashed, fix it, and run the experiment again.

## 2. Game Days

You do not run Chaos Monkey in production on Day 1.

You start with **Game Days**:
1. Gather the engineering team in a room (or a Zoom call).
2. Manually trigger a failure in a Staging environment.
3. Observe how the dashboards react. Are the alerts firing correctly? Does the team know which runbook to follow?
4. Once Staging is bulletproof, move the experiments to Production, carefully, during business hours when all engineers are awake and ready to hit the "Abort Experiment" button.

## 3. The Ultimate Goal

When a real AWS zone goes down at 3 AM on a Sunday, your pager should not ring. The system should gracefully fail over to another zone, because it has practiced doing exactly that every day via automated chaos experiments.
