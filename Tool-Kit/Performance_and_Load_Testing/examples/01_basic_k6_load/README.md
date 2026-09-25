# Basic k6 Load Test

**Goal:** Demonstrates a simple load test using k6, generating steady traffic to a test endpoint and verifying responses.

**Key Concepts:** [Load Testing](../../Performance_and_Load_Testing.md#load-testing), Virtual Users (VUs), Basic Assertions (Checks)

**Prerequisites:** 
- [k6 installed](https://k6.io/docs/get-started/installation/)

**Step-by-Step Execution:** 
1. Run the k6 script:
   ```bash
   k6 run script.js
   ```
2. **Expected Output:** k6 will output a summary of metrics, including `http_req_duration`, `vus`, and `checks` (verifying 100% of requests returned a 200 status and contained the expected text).

**Try it yourself:** Change the `vus` from 10 to 50 and the `duration` to `1m` in `script.js`, then run the test again to see how the metrics change.

**Teardown:** No cleanup required for this example.
