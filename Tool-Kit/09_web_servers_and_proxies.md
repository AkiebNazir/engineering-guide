# Web Servers and Proxies

Application servers (like a Node.js Express app, a Python Gunicorn worker, or a Java Tomcat server) are designed to run business logic. They are generally *terrible* at handling slow clients, terminating SSL, serving static files efficiently, or buffering large uploads.

That is why we place a dedicated Web Server / Reverse Proxy in front of them.

## 1. Nginx: The Industry Standard

Nginx uses an asynchronous, event-driven architecture, allowing a single worker process to handle tens of thousands of concurrent connections with very little memory.

### Reverse Proxy and Load Balancing
Instead of exposing your Node app on port 3000 to the internet, expose Nginx on port 80/443, and have it proxy traffic.

```nginx
upstream backend_servers {
    server 10.0.1.5:3000;
    server 10.0.1.6:3000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL Termination
Nginx handles the heavy cryptographic math of establishing a TLS connection, then forwards plain HTTP traffic to your backend over the secure internal network.

### Rate Limiting
Nginx can easily limit traffic to protect backends from brute force or DDoS attacks.
```nginx
# Limit to 10 requests per second per IP
limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

server {
    location /login {
        limit_req zone=mylimit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

## 2. Envoy: The Modern Cloud-Native Proxy

While Nginx was built for static files and simple reverse proxying, **Envoy** (built by Lyft) was designed from the ground up for microservices and dynamic cloud environments.

### The Problem Envoy Solves
In Nginx, if you add a new backend server to the `upstream` block, you have to reload the Nginx process. In Kubernetes, pods spin up and die every second. Reloading Nginx every second drops connections.

Envoy uses **xDS APIs** (Discovery Services). A control plane (like Istio) dynamically pushes new routing rules and backend IPs to Envoy over gRPC, and Envoy applies them instantly without dropping a single connection.

### Features Nginx Lacks (or paywalls)
- **Circuit Breaking**: "If this backend fails 5 times in a row, stop sending it traffic for 30 seconds."
- **Automatic Retries**: "If the backend returns a 503, retry the request exactly once before returning an error to the user."
- **Advanced Load Balancing**: Consistent hashing, zone-aware routing.
- **Deep Observability**: Envoy natively emits rich Prometheus metrics and OpenTelemetry traces for every hop.

## 3. HAProxy: The Pure TCP/HTTP Load Balancer

HAProxy is similar to Nginx but is entirely focused on being the fastest, most reliable load balancer on earth. It is often used at the edge to load-balance traffic *into* the Nginx/Envoy tier, or to load-balance raw TCP traffic (like database connections to a Postgres read-replica cluster).

## 4. Where Do They Belong in the Architecture?

```arch
%% caption: HAProxy at the edge for raw TCP load balancing, Nginx for static assets and SSL, Envoy as a sidecar for microservice routing.
route straight
node int "Internet" at 2,0 icon=internet color=blue
node edge "HAProxy\\n(L4 Load Balancer)" at 2,1 icon=lb color=amber
node ng "Nginx\\n(API Gateway & SSL)" at 2,2 icon=network color=green

group mesh "Service Mesh (K8s)" color=slate style=dashed
node e1 "Envoy Proxy" at 0,3 in mesh icon=proxy color=amber
node app1 "Microservice A" at 0,4 in mesh icon=app color=blue
node e2 "Envoy Proxy" at 4,3 in mesh icon=proxy color=amber
node app2 "Microservice B" at 4,4 in mesh icon=app color=blue

int -> edge
edge -> ng : "TCP/80"
ng -> e1 : "HTTP"
ng -> e2 : "HTTP"
e1 -> app1 : "localhost"
e2 -> app2 : "localhost"
e1 <-> e2 : "mTLS cross-talk"
```
