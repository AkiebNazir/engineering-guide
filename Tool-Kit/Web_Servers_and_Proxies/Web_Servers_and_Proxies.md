# Web Servers & Proxies

## Interactive Examples
We provide several interactive Docker-based examples in the `examples/` directory to help you practice these concepts:
* [Basic NGINX Static Server](./examples/01_basic_nginx_static)
* [Basic NGINX Reverse Proxy](./examples/02_basic_nginx_reverse_proxy)
* [Intermediate HAProxy Load Balancer](./examples/03_intermediate_haproxy_load_balancer)
* [Advanced NGINX Rate Limiting](./examples/04_advanced_nginx_rate_limiting)
* [Advanced NGINX SSL and HTTP/2](./examples/05_advanced_nginx_ssl_http2)

## 1. Introduction to Web Servers and Proxies

Web servers (like Apache, NGINX) serve static content and pass dynamic requests to application servers.
Proxies act as intermediaries for requests from clients seeking resources from other servers.

### Forward Proxy vs Reverse Proxy vs API Gateway

*   **Forward Proxy**: Sits in front of a group of client machines. When those clients make requests to sites on the internet, the proxy intercepts those requests and, acting on behalf of the clients, communicates with web servers. Used for anonymity, bypassing geographical restrictions, and caching.
*   **Reverse Proxy**: Sits in front of one or more web servers, intercepting requests from clients. This ensures that no client ever communicates directly with a backend server. Used for load balancing, security (hiding backend servers), and SSL/TLS termination.
> [!TIP] Check out the [Basic NGINX Reverse Proxy](./examples/02_basic_nginx_reverse_proxy) example to see this in action.
*   **API Gateway**: An API gateway is a specific type of reverse proxy designed for managing, routing, and securing API requests. It often includes features like rate limiting, authentication, billing, and request/response transformation.
> [!TIP] See rate limiting in action with the [Advanced NGINX Rate Limiting](./examples/04_advanced_nginx_rate_limiting) example.

## 2. Deep Dive: NGINX, HAProxy, and Envoy

*   **NGINX**: Highly performant, event-driven architecture. Excellent as a web server for static files and as a reverse proxy/load balancer.
> [!TIP] Check out the [Basic NGINX Static Server](./examples/01_basic_nginx_static) example.
*   **HAProxy**: High Availability Proxy. Specializes in load balancing and proxying for TCP and HTTP-based applications. Known for its incredible speed, reliability, and detailed metrics. Often preferred for complex routing and pure load balancing scenarios.
> [!TIP] Check out the [Intermediate HAProxy Load Balancer](./examples/03_intermediate_haproxy_load_balancer) example.
*   **Envoy**: Developed by Lyft, it's an L7 proxy and communication bus designed for large modern service oriented architectures. Excellent for cloud-native environments (like Kubernetes), offering advanced traffic management, observability, and extensibility. Often used as a sidecar proxy in service meshes.

## 3. Load Balancing Algorithms

Load balancers distribute incoming network traffic across a group of backend servers.

*   **Round Robin**: Requests are distributed sequentially across the pool of servers. Simple and effective when servers have similar capacities.
*   **Least Connections**: Directs traffic to the server with the fewest active connections. Best for long-lived connections (e.g., WebSockets) or when servers have varying loads.
*   **IP Hash**: The client's IP address is used to determine which server receives the request. Ensures a specific client consistently connects to the same server (session persistence/sticky sessions).

> [!TIP] Experiment with load balancing algorithms in the [Intermediate HAProxy Load Balancer](./examples/03_intermediate_haproxy_load_balancer) example.

## 4. SSL/TLS Termination

SSL/TLS termination (or offloading) is the process of decrypting encrypted traffic at the reverse proxy or load balancer before passing it unencrypted to the backend servers.
*   **Benefits**: Reduces CPU load on backend servers (since cryptography is computationally expensive), simplifies certificate management (managed in one place instead of on every backend), and allows the load balancer to inspect L7 traffic for routing decisions.

> [!TIP] Try configuring SSL termination yourself in the [Advanced NGINX SSL and HTTP/2](./examples/05_advanced_nginx_ssl_http2) example.

## 5. HTTP/2 vs HTTP/3

*   **HTTP/2**: Based on SPDY. Introduces multiplexing (multiple requests/responses over a single TCP connection), header compression (HPACK), and server push. Still uses TCP as the transport layer.
*   **HTTP/3**: Based on QUIC (Quick UDP Internet Connections). Uses UDP instead of TCP, eliminating head-of-line blocking at the transport layer, enabling faster connection establishment, and improving performance on lossy networks.

## 6. Architecture Diagram

```arch
node client "Client" at 0,0 icon=client
node proxy "Reverse Proxy" at 1,0 icon=proxy sub="SSL Termination"
node app1 "Backend App 1" at 2,0 icon=app
node app2 "Backend App 2" at 2,1 icon=app
client -> proxy
proxy -> app1
proxy -> app2
```

## 7. NGINX Production-Grade Configuration Example

Below is an example of setting up NGINX as a reverse proxy with SSL termination and basic load balancing.

```nginx
# Define the backend upstream pool
upstream backend_servers {
    least_conn; # Use Least Connections algorithm
    server 10.0.0.11:8080 weight=3;
    server 10.0.0.12:8080 max_fails=3 fail_timeout=30s;
}

# Redirect all HTTP traffic to HTTPS
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS Server configuration
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # SSL Settings (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;

    # Proxy settings
    location / {
        proxy_pass http://backend_servers;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_addrs;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Websocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 8. MAANG-Level Interview Questions

1.  **Q: Explain the difference between a forward proxy and a reverse proxy. When would you use each?**
    **A:** A forward proxy sits in front of clients, mediating their outbound requests to the internet (used for caching, content filtering, IP masking). A reverse proxy sits in front of backend servers, intercepting inbound requests from the internet (used for load balancing, SSL termination, caching, hiding backend topology).

2.  **Q: Why might you choose HAProxy over NGINX, or vice versa?**
    **A:** NGINX is a versatile web server and reverse proxy, excellent for serving static files, caching, and standard HTTP load balancing. HAProxy is purely a load balancer and proxy (no static file serving), known for extreme performance, complex routing rules, detailed metrics, and deep TCP-level proxying capabilities.

3.  **Q: What is SSL termination, and why is it beneficial? What are its security implications?**
    **A:** SSL termination involves decrypting SSL traffic at the proxy/load balancer and sending it unencrypted to the backend. It offloads CPU-intensive decryption from backends and centralizes certificate management. The security implication is that traffic on the internal network is unencrypted; if the internal network is breached, traffic can be snooped (End-to-End Encryption can mitigate this if needed).

4.  **Q: How does the Least Connections load balancing algorithm work, and when is it superior to Round Robin?**
    **A:** Least Connections routes new requests to the server with the fewest active connections. It is superior to Round Robin when requests have highly variable processing times or when using long-lived connections (like WebSockets), preventing servers from being overwhelmed by a few heavy requests.

5.  **Q: Explain Head-of-Line (HOL) blocking in the context of HTTP/1.1, HTTP/2, and HTTP/3.**
    **A:** In HTTP/1.1, pipelining suffers from HOL blocking at the application layer; a delayed response blocks subsequent responses. HTTP/2 solves application-layer HOL blocking via multiplexing, but suffers from transport-layer HOL blocking because it uses TCP (a single dropped packet stalls all multiplexed streams). HTTP/3 solves this by using QUIC (over UDP), where streams are independent at the transport layer; a lost packet only affects its specific stream.

6.  **Q: What is an API Gateway, and how does it differ from a standard reverse proxy?**
    **A:** An API Gateway is a specialized reverse proxy tailored for APIs. While a standard reverse proxy primarily handles routing and load balancing, an API gateway adds features like authentication/authorization, rate limiting, quota management, request/response transformation, and API analytics.

7.  **Q: How do you handle session persistence (sticky sessions) in a load-balanced environment, and what are the drawbacks?**
    **A:** Session persistence can be achieved using IP Hash, where a client's IP is hashed to select a server, or by the load balancer injecting a cookie. Drawbacks include uneven load distribution (one server might handle many heavy clients) and state loss if a server fails. Storing session state in a centralized store (like Redis) is generally preferred over sticky sessions.

8.  **Q: Explain how NGINX handles concurrent connections efficiently compared to thread-per-connection web servers like traditional Apache.**
    **A:** Traditional Apache spawns a new thread/process per connection, leading to high memory and context-switching overhead under heavy load. NGINX uses an asynchronous, event-driven, non-blocking architecture. A single worker process handles thousands of concurrent connections within an event loop, drastically reducing resource consumption.

9.  **Q: What are the key differences between Envoy and NGINX?**
    **A:** NGINX is a robust, general-purpose web server and proxy. Envoy is heavily focused on dynamic configuration, extensive observability, and L7 routing, making it the preferred choice for service mesh data planes (like Istio) in cloud-native, microservices architectures. Envoy is configured almost entirely via APIs rather than static files.

10. **Q: How would you design a highly available reverse proxy tier?**
    **A:** Deploy multiple reverse proxy instances across different availability zones. Place them behind a cloud provider's network load balancer or use a floating IP (Virtual IP) managed by Keepalived/VRRP. Ensure health checks are configured so traffic is only routed to healthy proxies.

11. **Q: Describe the X-Forwarded-For header and why it's necessary.**
    **A:** When a reverse proxy intercepts a request, the backend server sees the proxy's IP address, not the client's. The proxy adds the original client's IP to the `X-Forwarded-For` header so the backend can log the true client IP or make IP-based decisions.

12. **Q: What is SNI (Server Name Indication), and why is it important for HTTPS?**
    **A:** SNI is an extension to the TLS protocol that allows a client to specify the hostname it is trying to connect to during the TLS handshake. This enables a single IP address (e.g., on a load balancer) to host multiple HTTPS websites with different SSL certificates.

13. **Q: In an architecture with a Reverse Proxy and multiple Microservices, how would you implement rate limiting?**
    **A:** Implement rate limiting at the Reverse Proxy or API Gateway layer (e.g., using NGINX `limit_req` module or Envoy's rate limiting service). This protects the backend microservices from being overwhelmed and centralizes the configuration. A distributed store like Redis might be needed if there are multiple proxy instances.

14. **Q: How do you gracefully restart NGINX or HAProxy to apply configuration changes without dropping connections?**
    **A:** Both proxies support graceful reloads (e.g., `nginx -s reload`). The master process starts new worker processes with the updated configuration. Old worker processes stop accepting new connections but continue serving existing ones until they complete, after which the old workers exit.

15. **Q: When might you choose to NOT terminate SSL at the load balancer (Pass-through)?**
    **A:** You might choose SSL pass-through (End-to-End Encryption) for strict compliance requirements (e.g., HIPAA, PCI-DSS) where traffic must remain encrypted on the internal network. The load balancer routes TCP traffic blindly without decrypting it, which prevents L7 inspection or routing based on HTTP headers.
