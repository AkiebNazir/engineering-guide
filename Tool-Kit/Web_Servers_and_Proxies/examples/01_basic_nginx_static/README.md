# Basic NGINX Static Server
**Goal:** Demonstrates how to run a basic NGINX server serving a simple static HTML file.
**Key Concepts:** [Introduction to Web Servers and Proxies](../../Web_Servers_and_Proxies.md#1-introduction-to-web-servers-and-proxies), [Deep Dive: NGINX](../../Web_Servers_and_Proxies.md#2-deep-dive-nginx-haproxy-and-envoy)
**Prerequisites:** Docker and Docker Compose installed.
**Step-by-Step Execution:**
1. Run `docker-compose up -d`
2. Open your browser and navigate to `http://localhost:8081`
3. You should see the static HTML page.
**Try it yourself:** Modify the static HTML file and observe the changes in your browser after refreshing.
**Teardown:** Run `docker-compose down` to stop the server.
