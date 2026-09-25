# Intermediate HAProxy Load Balancer
**Goal:** Demonstrates HAProxy round-robin load balancing across 3 backend containers.
**Key Concepts:** [Load Balancing Algorithms](../../Web_Servers_and_Proxies.md#3-load-balancing-algorithms), [Deep Dive: HAProxy](../../Web_Servers_and_Proxies.md#2-deep-dive-nginx-haproxy-and-envoy)
**Prerequisites:** Docker and Docker Compose installed.
**Step-by-Step Execution:**
1. Run `docker-compose up -d`
2. Open your browser and navigate to `http://localhost:8083`, or curl it multiple times: `curl http://localhost:8083`
3. The response will show different Hostnames as HAProxy cycles through `web1`, `web2`, and `web3`.
**Try it yourself:** Modify the HAProxy configuration to use a different load balancing algorithm like `leastconn` instead of `roundrobin` and observe the behavior.
**Teardown:** Run `docker-compose down` to stop the containers.
