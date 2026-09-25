# 01 Basic Go Cli

**Goal:** Demonstrate 01 basic go cli
**Key Concepts:** [Docker & Containerization Guide](../../Docker_Container.md)
**Prerequisites:** Docker installed
**Step-by-Step Execution:**
1. Navigate to this directory.
2. Build the image:
   ```bash
   docker build -t 01_basic_go_cli .
   ```
3. Run the container:
   ```bash
   docker run -p 8080:8080 01_basic_go_cli
   ```
   *(Modify port if application uses a different port)*

**Try it yourself:** Modify the application code and rebuild the image to see the changes.

**Teardown:**
```bash
docker ps -a
docker rm -f <container_id>
```
