# Advanced k6 Spike Test

**Goal:** Demonstrates how to configure stages in k6 to simulate sudden, extreme increases in load (a spike test).

**Key Concepts:** [Spike Testing](../../Performance_and_Load_Testing.md#spike-testing), Staged Load Profiles

**Prerequisites:** 
- [k6 installed](https://k6.io/docs/get-started/installation/)

**Step-by-Step Execution:** 
1. Run the k6 script:
   ```bash
   k6 run script.js
   ```
2. **Expected Output:** The script will automatically scale the number of Virtual Users (VUs) up and down over several minutes according to the defined `stages` array, simulating a sudden burst in traffic and a subsequent recovery period.

**Try it yourself:** Modify the stages to simulate a "step" load test, where traffic increases by 50 VUs every minute for 5 minutes, then abruptly stops.

**Teardown:** No cleanup required.
