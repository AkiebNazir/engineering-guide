# Exercise 4: Artifact Promotion in Docker 🟡

## 🎯 Objective
Simulate a CI/CD pipeline promotion strategy. You will build an image for "dev", test it, and then promote that *exact same image* to "prod" without rebuilding it.

## 📋 Prerequisites
* Docker installed and running
* Local Docker registry running (from Exercise 1: `docker run -d -p 5000:5000 registry:2`)

## 📝 Instructions

### Step 1: Create the Application
Create a simple Python web server.
File: `app.py`
```python
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        env = os.environ.get("ENV_NAME", "unknown")
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes(f"Running in {env} environment.\n", "utf-8"))

if __name__ == "__main__":
    webServer = HTTPServer(("0.0.0.0", 8080), MyServer)
    print("Server started http://0.0.0.0:8080")
    webServer.serve_forever()
```

### Step 2: Create the Dockerfile
File: `Dockerfile`
```dockerfile
FROM python:3.9-alpine
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
```

### Step 3: CI Phase - Build and Push with Git SHA
Assume the current Git commit is `abc1234`. We build and push this unique SHA.

```bash
# Build the artifact
docker build -t localhost:5000/webapp:abc1234 .

# Push to artifact registry
docker push localhost:5000/webapp:abc1234
```

### Step 4: Staging Deployment & Testing
Pull the artifact, deploy it, and test it as if we were in the Staging environment.

```bash
# Pull exact SHA
docker pull localhost:5000/webapp:abc1234

# Run in staging
docker run -d --name staging-app -p 8081:8080 -e ENV_NAME=STAGING localhost:5000/webapp:abc1234

# Run integration tests (curl)
curl http://localhost:8081
```

### Step 5: Promotion to Production
The tests passed! Now, we promote. **Crucially, we do not run `docker build` again.** We retag the existing image.

```bash
# Tag the tested image for production release
docker tag localhost:5000/webapp:abc1234 localhost:5000/webapp:v1.0.0
docker tag localhost:5000/webapp:abc1234 localhost:5000/webapp:production

# Push the new tags
docker push localhost:5000/webapp:v1.0.0
docker push localhost:5000/webapp:production
```

### Step 6: Production Deployment
Deploy using the production tag.

```bash
docker pull localhost:5000/webapp:v1.0.0
docker run -d --name prod-app -p 8082:8080 -e ENV_NAME=PRODUCTION localhost:5000/webapp:v1.0.0

curl http://localhost:8082
```

### Step 7: Verify Image Digests match
Prove to yourself that the image in staging and production are byte-for-byte identical.
```bash
docker inspect --format='{{index .Id}}' localhost:5000/webapp:abc1234
docker inspect --format='{{index .Id}}' localhost:5000/webapp:v1.0.0
```
*(Both commands will output the exact same sha256 hash).*

## 💡 Hints
* Tagging an image doesn't duplicate the data on your disk or in the registry. It simply creates a new pointer to the existing image layers (SHA digest).

## ✅ Expected Output
```text
$ curl http://localhost:8081
Running in STAGING environment.

$ curl http://localhost:8082
Running in PRODUCTION environment.

$ docker inspect ...
sha256:7f8a9b2...
sha256:7f8a9b2...
```

## 🧠 Key Takeaway
Artifact promotion ensures that the code you tested in lower environments is mathematically guaranteed to be the exact same code deployed to production. Build once, tag multiple times.
