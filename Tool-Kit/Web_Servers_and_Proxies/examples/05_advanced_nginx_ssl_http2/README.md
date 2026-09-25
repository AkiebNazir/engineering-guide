# Advanced NGINX SSL and HTTP/2
**Goal:** Demonstrates NGINX configured for SSL termination and HTTP/2.
**Key Concepts:** [SSL/TLS Termination](../../Web_Servers_and_Proxies.md#4-ssltls-termination), [HTTP/2 vs HTTP/3](../../Web_Servers_and_Proxies.md#5-http2-vs-http3)
**Prerequisites:** Docker and Docker Compose installed. OpenSSL for generating certificates.
**Step-by-Step Execution:**
1. Run `./generate_certs.sh` to generate self-signed certificates.
2. Run `docker-compose up -d`
3. Try accessing `http://localhost:8085` (it will redirect to HTTPS).
4. Access `https://localhost:8443` in your browser. (You will need to accept the self-signed certificate warning).
5. Open your browser's Developer Tools -> Network tab, and observe that the Protocol used for the request is `h2` (HTTP/2).
**Try it yourself:** Try disabling HTTP/2 in the NGINX configuration by removing `http2` from the listen directive and see how it falls back to HTTP/1.1 in your browser's dev tools.
**Teardown:** Run `docker-compose down` to stop the containers.
