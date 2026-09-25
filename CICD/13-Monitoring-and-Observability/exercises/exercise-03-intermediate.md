# Exercise 3: Instrumenting Custom Metrics 📊

## 🎯 Objective
Expose custom Prometheus metrics (a counter and a gauge) from an application.

## 📋 Prerequisites
- Python 3.9+
- Prometheus client library: `pip install prometheus_client`

## 📝 Instructions

We will create a simple web server that tracks the total number of requests (Counter) and the current number of active requests being processed (Gauge).

### Step 1: Create the Server Script
Create a file named `server.py`.

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import start_http_server, Counter, Gauge
import time
import random
import threading

# Define metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total app HTTP requests')
ACTIVE_REQUESTS = Gauge('app_requests_active', 'Number of active requests being processed')

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Increment total request counter
        REQUEST_COUNT.inc()
        
        # Increase active request gauge
        ACTIVE_REQUESTS.inc()
        
        try:
            # Simulate work
            time.sleep(random.uniform(0.1, 0.5))
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Hello, world!\n")
        finally:
            # Decrease active request gauge when done
            ACTIVE_REQUESTS.dec()

def run_app_server():
    server = HTTPServer(('localhost', 8080), MetricsHandler)
    print("App server running on port 8080...")
    server.serve_forever()

if __name__ == '__main__':
    # Start up the server to expose the metrics to Prometheus on port 8000
    start_http_server(8000)
    print("Prometheus metrics available on port 8000 (/metrics)...")
    
    # Run the main app
    run_app_server()
```

### Step 2: Test the Metrics
1. Run the script: `python server.py`
2. Open a new terminal. Send some traffic to the app:
   `for i in {1..10}; do curl http://localhost:8080 & done`
3. View the exposed metrics:
   `curl http://localhost:8000`

## 💡 Hints
- The Counter `app_requests_total` will only ever increase.
- The Gauge `app_requests_active` will fluctuate up and down depending on concurrent traffic.
- Look for `app_requests_total_total` in the metrics output.

## ✅ Expected Output / Solution
The `/metrics` endpoint on port 8000 will output something like:
```text
# HELP app_requests_total Total app HTTP requests
# TYPE app_requests_total counter
app_requests_total_total 10.0
# HELP app_requests_total_created Total app HTTP requests
# TYPE app_requests_total_created gauge
app_requests_total_created 1698240000.0
# HELP app_requests_active Number of active requests being processed
# TYPE app_requests_active gauge
app_requests_active 0.0
```

## 🧠 Key Takeaway
Instrumentation allows developers to expose internal application state. Prometheus scrapes these `/metrics` endpoints periodically to aggregate the data over time.
