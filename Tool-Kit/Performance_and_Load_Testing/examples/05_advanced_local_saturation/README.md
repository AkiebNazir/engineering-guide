# Advanced Local Saturation Test

**Goal:** Demonstrates how to find a system's saturation point by load testing a containerized Node.js API with strict resource limits, intentionally inducing CPU bottlenecks.

**Key Concepts:** [Saturation Point](../../Performance_and_Load_Testing.md#saturation-point), CPU Profiling, Little's Law

**Prerequisites:** 
- Docker and Docker Compose installed
- [k6 installed](https://k6.io/docs/get-started/installation/)

**Step-by-Step Execution:** 
1. Start the target API using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
2. Verify the API is running:
   ```bash
   curl http://localhost:3000/health
   ```
3. Run the saturation test script:
   ```bash
   k6 run script.js
   ```
4. **Expected Output:** The script will ramp up load against the `/process` endpoint. Because the container is limited to 0.5 CPUs and calculates Fibonacci sequences recursively, you will observe latencies spike exponentially as the system reaches its saturation point.

**Try it yourself:** Open `docker-compose.yml`, increase the CPU limit from `0.5` to `2.0`, restart the container (`docker-compose up -d`), and run the test again. Observe how the saturation point moves.

**Teardown:** 
```bash
docker-compose down
```
