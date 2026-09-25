# Intermediate k6 Thresholds

**Goal:** Demonstrates how to define custom metrics and pass/fail thresholds in k6 to enforce SLAs (Service Level Agreements).

**Key Concepts:** [Percentiles](../../Performance_and_Load_Testing.md#percentiles-p50-p90-p99), Thresholds, Custom Metrics

**Prerequisites:** 
- [k6 installed](https://k6.io/docs/get-started/installation/)

**Step-by-Step Execution:** 
1. Run the k6 script:
   ```bash
   k6 run script.js
   ```
2. **Expected Output:** The script will run for 1 minute. At the end, k6 will evaluate the thresholds (`p(95)<200` for duration and `rate<0.01` for errors). The console output will color-code these thresholds green (pass) or red (fail).

**Try it yourself:** Intentionally fail the test by changing the `http_req_duration` threshold in `script.js` to `p(95)<10` (10ms) and observe k6 exit with a non-zero status code.

**Teardown:** No cleanup required.
