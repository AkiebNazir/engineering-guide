# Basic JMeter Test

**Goal:** Demonstrates a simple load test using Apache JMeter, executing HTTP GET requests against a test endpoint.

**Key Concepts:** [Apache JMeter](../../Performance_and_Load_Testing.md#apache-jmeter), Thread Groups, HTTP Request Sampler

**Prerequisites:** 
- [Java 8+](https://adoptium.net/) installed
- [Apache JMeter](https://jmeter.apache.org/download_jmeter.cgi) installed

**Step-by-Step Execution:** 
1. Run the test plan in non-GUI mode:
   ```bash
   jmeter -n -t test_plan.jmx -l results.jtl
   ```
2. **Expected Output:** JMeter will run the 5 threads for 10 loops each and output summary statistics to the console, while logging raw results to `results.jtl`.

**Try it yourself:** Open `test_plan.jmx` in the JMeter GUI (using the `jmeter` command without arguments) and add a "View Results Tree" listener to inspect individual requests and responses.

**Teardown:** 
```bash
rm results.jtl
```
