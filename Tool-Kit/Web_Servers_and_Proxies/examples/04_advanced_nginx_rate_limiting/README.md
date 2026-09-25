# Advanced NGINX Rate Limiting
**Goal:** Demonstrates NGINX configured with rate limiting to prevent API abuse.
**Key Concepts:** [API Gateway](../../Web_Servers_and_Proxies.md#forward-proxy-vs-reverse-proxy-vs-api-gateway)
**Prerequisites:** Docker and Docker Compose installed.
**Step-by-Step Execution:**
1. Run `docker-compose up -d`
2. Run a loop to send multiple requests quickly:
   `for i in {1..10}; do curl -i http://localhost:8084; done`
3. Notice that after a few successful requests (due to the `burst` config), you will start receiving `503 Service Temporarily Unavailable` responses from NGINX.
4. Wait a few seconds and try again, the rate limit will have recovered.
**Try it yourself:** Adjust the rate limit parameters in the NGINX configuration (e.g., change the rate or burst values) and test how it impacts the allowed requests.
**Teardown:** Run `docker-compose down` to stop the containers.
