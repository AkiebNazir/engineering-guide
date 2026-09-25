# Basic NGINX Reverse Proxy
**Goal:** Demonstrates NGINX acting as a reverse proxy forwarding requests to a Node.js backend.
**Key Concepts:** [Forward Proxy vs Reverse Proxy](../../Web_Servers_and_Proxies.md#forward-proxy-vs-reverse-proxy-vs-api-gateway)
**Prerequisites:** Docker and Docker Compose installed.
**Step-by-Step Execution:**
1. Run `docker-compose up -d`
2. Open your browser and navigate to `http://localhost:8082`
3. You should see "Hello from the Node.js Backend Container!"
**Try it yourself:** Try modifying the Node.js backend to return a different message and restart the backend container.
**Teardown:** Run `docker-compose down` to stop the containers.
