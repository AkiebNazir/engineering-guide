# Performance and Load Testing

You cannot know if your system will scale to 10,000 requests per second by running a single `curl` command. You must load test it.

## 1. The Methodology

1. **Establish a Baseline**: Run a test against the current system. Record the P95 latency and the max RPS (Requests Per Second) before the error rate exceeds 1%.
2. **Identify the Bottleneck**: Are you maxing out CPU? RAM? DB Connections? Network bandwidth? Use observability tools (Prometheus, Grafana) *while* the load test is running.
3. **Change ONE Thing**: Add an index, increase the DB connection pool, or add a caching layer.
4. **Re-test**: Did the P95 latency drop? Did the max RPS go up?

## 2. `wrk`: The Blunt Instrument

`wrk` is a C program that uses operating system threads to blast an endpoint with as much HTTP traffic as physically possible. It is great for finding the absolute upper limit of a single endpoint.

```bash
# Run for 30 seconds, using 12 threads, keeping 400 open connections
wrk -t12 -c400 -d30s http://127.0.0.1:8080/api/users
```

**Output**:
```text
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    45.12ms   12.34ms 105.40ms   80.12%
    Req/Sec     750.12    105.45     1.1k    75.00%
  270043 requests in 30.10s, 85.12MB read
Requests/sec:   8971.52
Transfer/sec:      2.83MB
```

## 3. `k6`: The Precision Scalpel

`wrk` just hits a single URL blindly. Real users log in, fetch a profile, wait 2 seconds, and then submit a form. **k6** (written in Go, scripted in JavaScript) simulates complex user journeys.

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

// Define the shape of the test
export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp up to 20 users
    { duration: '1m', target: 20 },  // Stay at 20 users
    { duration: '30s', target: 0 },  // Ramp down to 0
  ],
  thresholds: {
    // The test fails if P95 latency is > 500ms, or if error rate is > 1%
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

// The actual user journey
export default function () {
  // 1. Log in
  const loginRes = http.post('https://api.example.com/login', { user: 'test', pass: '123' });
  check(loginRes, { 'logged in successfully': (r) => r.status === 200 });
  const token = loginRes.json('token');

  // 2. Think time
  sleep(1);

  // 3. Fetch data using the token
  const dataRes = http.get('https://api.example.com/profile', {
    headers: { Authorization: `Bearer ${token}` },
  });
  check(dataRes, { 'fetched profile': (r) => r.status === 200 });
}
```

Run it:
```bash
k6 run script.js
```

## 4. Types of Load Tests

- **Smoke Test**: Minimal load (1 user) to verify the script works and the system is up.
- **Load Test**: Assess performance under *expected* peak production load. (e.g., 500 concurrent users).
- **Stress Test**: Push the system beyond its limits until it breaks, to see *how* it fails (does it gracefully degrade, or does the database crash and corrupt data?) and how it recovers when the load subsides.
- **Spike Test**: Extremely rapid ramp-up to simulate a viral event or a marketing push. Evaluates if autoscaling triggers fast enough.
- **Soak Test**: Run a moderate load for 24 hours to find memory leaks and database connection pool exhaustion.
