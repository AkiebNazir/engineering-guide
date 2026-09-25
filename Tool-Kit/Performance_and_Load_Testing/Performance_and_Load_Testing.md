# Performance & Load Testing

## 1. Introduction to Performance Engineering
Performance engineering is the discipline of ensuring software applications meet non-functional requirements related to speed, stability, and scalability under varying workloads. It involves designing, implementing, and validating system behavior under expected and peak loads.

## 2. Tools of the Trade: k6, JMeter, and Locust

### k6 (by Grafana)
Modern, developer-centric load testing tool built in Go, utilizing JavaScript/TypeScript for test authoring.
- **Pros**: Outstanding performance, "as-code" approach, CI/CD friendly, integrates with Grafana/Prometheus.
- **Cons**: JS execution is not full Node.js (uses Goja), so some npm packages aren't compatible.

### Apache JMeter
The veteran open-source Java-based tool with a GUI for test creation.
- **Pros**: Huge ecosystem, protocol support (HTTP, JDBC, FTP, JMS, etc.), no coding required for basic tests.
- **Cons**: XML-based test plans are hard to version control, high resource consumption compared to k6.

### Locust
Python-based, distributed user load testing tool.
- **Pros**: Tests are written in pure Python, highly customizable, distributed execution is easy to set up.
- **Cons**: Python's GIL can bottleneck single-node performance compared to Go-based tools like k6.

## 3. Interactive Examples

This guide is accompanied by practical examples in the `examples/` directory. You can run these locally to see the concepts in action:

- **[01_basic_k6_load](./examples/01_basic_k6_load)**: A simple k6 load test generating steady traffic.
- **[02_basic_jmeter](./examples/02_basic_jmeter)**: A basic JMeter test plan to demonstrate non-GUI execution.
- **[03_intermediate_k6_thresholds](./examples/03_intermediate_k6_thresholds)**: Defines custom metrics and SLA thresholds.
- **[04_advanced_k6_spike_test](./examples/04_advanced_k6_spike_test)**: Simulates sudden traffic spikes using staged load profiles.
- **[05_advanced_local_saturation](./examples/05_advanced_local_saturation)**: Finds a system's breaking point by testing a CPU-limited Docker container.

## 4. Types of Testing

### Load Testing
> [!TIP]
> Try out our [Basic k6 Load Test](./examples/01_basic_k6_load) or [Basic JMeter Test](./examples/02_basic_jmeter) to see load testing in action.

Validates system performance under **expected** (normal and peak) load conditions.
- **Goal**: Ensure the system meets SLAs (Service Level Agreements) for response times and throughput under anticipated usage.

### Stress Testing
Pushes the system **beyond** expected peak loads until it breaks.
- **Goal**: Identify the breaking point (saturation point), observe how the system fails (does it degrade gracefully?), and determine bottleneck components.

### Spike Testing
> [!TIP]
> See the [Advanced k6 Spike Test](./examples/04_advanced_k6_spike_test) example to learn how to configure staged load profiles.

Subjecting the system to sudden, extreme increases in load over a very short duration.
- **Goal**: Evaluate how the system handles sudden bursts of traffic (e.g., ticket sales, Black Friday) and if autoscaling triggers fast enough.

### Soak Testing (Endurance Testing)
Applying a continuous, moderate load over an extended period (hours to days).
- **Goal**: Uncover memory leaks, database connection pool exhaustion, and long-term degradation.

## 5. Key Metrics and Concepts

### Latency vs Throughput
- **Latency**: The time it takes for a single request to be processed and returned to the client (measured in ms).
- **Throughput**: The number of requests the system can handle over a given time period (e.g., Requests Per Second - RPS).

### Percentiles (p50, p90, p99)
> [!TIP]
> Check out the [Intermediate k6 Thresholds](./examples/03_intermediate_k6_thresholds) example to learn how to define custom metrics and pass/fail thresholds for percentiles.

Averages lie. Percentiles tell the true story of user experience.
- **p50 (Median)**: 50% of requests are faster than this value.
- **p90**: 90% of requests are faster. 10% of users experience worse performance.
- **p99**: The "tail latency". Critical for large-scale systems where a user request fans out to dozens of microservices.

### Little's Law
`L = λW`
Where:
- **L**: Number of concurrent requests in the system.
- **λ (Lambda)**: Arrival rate (Throughput/RPS).
- **W**: Average time a request spends in the system (Latency).
Useful for calculating required concurrent users to hit a target RPS.

### Saturation Point
> [!TIP]
> Run the [Advanced Local Saturation Test](./examples/05_advanced_local_saturation) to learn how to intentionally induce CPU bottlenecks and find a system's saturation point.

The point at which increasing load no longer increases throughput, but instead causes latency to spike exponentially. The system's capacity is fully utilized.

## 6. Load Testing Architecture

```arch
node gen "Generator" at 0,0 icon=client sub="Client"
node lb "Load Balancer" at 1,0 icon=lb
node cluster "Cluster" at 2,0 icon=server sub="Server"
gen -> lb
lb -> cluster
```

## 7. Production-Grade Code Example (k6)

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const apiLatency = new Trend('api_latency');

export const options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp up to 50 users
    { duration: '3m', target: 50 },  // Stay at 50 users for 3 mins
    { duration: '1m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    // 99% of requests must finish within 200ms
    http_req_duration: ['p(99)<200'],
    // Error rate must be less than 1%
    error_rate: ['rate<0.01'],
    // Custom trend threshold
    api_latency: ['p(95)<150'],
  },
};

export default function () {
  const url = 'https://api.example.com/v1/resource';
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_TOKEN_HERE',
    },
  };

  const res = http.get(url, params);

  // Track metrics
  apiLatency.add(res.timings.duration);
  errorRate.add(res.status >= 400);

  // Validate response
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response has data': (r) => r.json().hasOwnProperty('data'),
  });

  // Think time
  sleep(1);
}
```

## 8. MAANG-Level Interview Questions

**Q1: How do you identify a memory leak during performance testing?**
A: Run a Soak Test over several hours. Monitor application memory usage via APM tools (e.g., Datadog, Prometheus). A steady, continuous upward trend in memory usage that does not drop after Garbage Collection (GC) sweeps indicates a leak. You would then capture a heap dump and analyze it (e.g., with Eclipse MAT or VisualVM) to find the objects keeping references alive.

**Q2: What is "Coordinated Omission" and why is it dangerous?**
A: It occurs when a load testing tool fails to accurately record the response times of delayed requests because it waits for previous slow requests to complete before sending new ones. This masks the severity of tail latencies. Tools like wrk2 or specialized k6 configurations mitigate this by maintaining a constant arrival rate regardless of response times.

**Q3: Explain Little's Law and how you'd use it to design a load test.**
A: Little's Law (`L = λ * W`) relates concurrency (L), throughput (λ), and latency (W). If your target is 1000 RPS (λ) and your expected latency is 50ms (0.05s) (W), you need `1000 * 0.05 = 50` concurrent users (L) to generate that load. This helps configure the `vus` (Virtual Users) parameter accurately.

**Q4: Your system crashes at 500 RPS during a stress test. How do you find the bottleneck?**
A: I'd use the USE method (Utilization, Saturation, Errors) across the stack. First, check the load balancer/proxy. Then check application nodes: CPU, Memory, Network I/O. If CPU is 100%, profile the code (flame graphs). If CPU is low, check DB metrics (active connections, slow queries, deadlocks). Often, the bottleneck is external APIs or DB locks.

**Q5: Why should you care about p99 latency instead of average latency?**
A: Averages mask outliers. In microservice architectures, a single user request might fan out to 50 downstream services. If any of those 50 services hits a p99 latency spike, the entire user request is delayed. This is called the "tail at scale" problem.

**Q6: What is the difference between open and closed workload models?**
A: Closed models maintain a fixed number of concurrent users (e.g., standard JMeter). A new request is only sent when an old one completes. Open models send requests at a constant rate regardless of system response time, accurately simulating real-world internet traffic where users arrive independently.

**Q7: How do you load test a system that relies heavily on 3rd-party APIs?**
A: You cannot load test third-party APIs without permission, and it's expensive/unpredictable. Instead, build a stub/mock service (using WireMock or Mountebank) that replicates the latency and response payload of the 3rd-party API.

**Q8: Explain the difference between Thread Pools and Connection Pools. How do they affect load testing?**
A: Thread pools limit concurrent application-level executions (e.g., Tomcat threads). Connection pools limit concurrent connections to a database (e.g., HikariCP). Misconfiguring either can lead to queuing. If your thread pool is 200 but connection pool is 20, 180 threads will block waiting for a DB connection, showing up as high latency in the test.

**Q9: What happens if your load generator itself becomes the bottleneck?**
A: The results will show high latency and low throughput, falsely blaming the system under test. To fix this, monitor the load generator's CPU/Network. Use distributed load testing (e.g., k6 cloud, JMeter distributed mode, Locust workers) to spread the generation across multiple machines.

**Q10: How do you ensure your load test data doesn't skew your results (e.g., cache hits)?**
A: Real-world traffic has high cardinality. If a load test requests the same user ID repeatedly, the database or application cache will serve it from memory (unrealistic 1ms latency). You must parameterize tests with large, randomized datasets (e.g., CSV files) to simulate realistic cache miss rates.
