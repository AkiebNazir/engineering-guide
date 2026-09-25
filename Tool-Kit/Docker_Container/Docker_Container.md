# Docker & Containerization

Welcome to the ultimate guide on Docker! Whether you're a complete beginner or looking to solidify your foundational knowledge, this guide covers everything from ground zero to advanced concepts.

## Introduction to Docker & Containerization

## Interactive Examples

To help you bridge theory and practice, this guide includes interactive examples. 
There are two sets of examples:
- `examples/`: Focuses on interpreted languages (Python, Node.js) where containerization is straightforward.
- `examples_go/`: Focuses on compiled languages (Go), which introduces concepts like multi-stage builds to keep final images small and secure.

> [!TIP] Check out the [examples folder](examples) and [examples_go folder](examples_go) for hands-on applications of these concepts!



### 1. The Problem: "It works on my machine!"
Imagine this scenario: A developer writes an application on their laptop (using specific versions of Python, Node.js, libraries, and OS settings). They send it to testing, and it crashes. Why? Because the testing environment has a different OS, missing dependencies, or conflicting library versions.

This is the classic **"It works on my machine!"** problem.

Historically, the solution was **Virtual Machines (VMs)**.

#### The Virtual Machine (VM) Approach
A VM is a complete operating system running on top of your host operating system. It uses a **Hypervisor** (like VMware, VirtualBox, or Hyper-V) to allocate physical resources (CPU, RAM) to guest operating systems.
*   **Pros:** Complete isolation.
*   **Cons:** Heavy, slow to start, wastes resources (each VM needs its own full OS, taking up GBs of disk space and RAM).

### 2. The Solution: Containerization
Containers offer a lightweight alternative to VMs. Instead of virtualizing the hardware to run a whole new OS, containers virtualize the **Operating System itself**.

*   **Containers** share the host system's kernel (the core of the OS) but keep the application and its dependencies isolated in their own little bubble.
*   Because they don't need a full OS, containers are tiny (often just megabytes), start in milliseconds, and use fewer resources.

#### VM vs. Container Architecture

#### VM vs. Container Architecture

```arch
group vm "Virtual Machine Approach" color=slate style=dashed
node hw1 "Server Hardware" at 0.5,0 in vm icon=server
node hyp "Hypervisor" at 0.5,1 in vm icon=process
node vm1_os "Guest OS Ubuntu" at 0,2 in vm icon=server
node vm1_app "App 1 + Libs" at 0,3 in vm icon=app
node vm2_os "Guest OS Windows" at 1,2 in vm icon=server
node vm2_app "App 2 + Libs" at 1,3 in vm icon=app

hw1 -> hyp
hyp -> vm1_os
vm1_os -> vm1_app
hyp -> vm2_os
vm2_os -> vm2_app

group cont "Container Approach" color=slate style=dashed
node hw2 "Server Hardware" at 3,0 in cont icon=server
node hos "Host OS" at 3,1 in cont icon=process
node de "Docker Engine" at 3,2 in cont icon=docker-icon
node c1 "Container 1 App 1" at 2.5,3 in cont icon=app
node c2 "Container 2 App 2" at 3.5,3 in cont icon=app

hw2 -> hos
hos -> de
de -> c1
de -> c2
```

| Feature | Virtual Machine | Container (Docker) |
| :--- | :--- | :--- |
| **Architecture** | App + Dependencies + Guest OS | App + Dependencies |
| **Isolation** | Hardware-level (Hypervisor) | OS-level (Namespaces & cgroups) |
| **Size** | Gigabytes | Megabytes |
| **Boot Time** | Minutes | Milliseconds |
| **Resource Usage**| High | Low |

### 3. What is Docker?
Docker is a platform and tool that allows developers to easily create, deploy, and run applications in containers. It standardized containerization. While Linux containers (LXC) existed before Docker, Docker made them incredibly easy to use.

#### Core Concepts (The Docker Glossary)

1.  **Image:** The blueprint. It's a read-only template that contains everything needed to run an application (code, libraries, environment variables, config files). Think of it as a class in Object-Oriented Programming (OOP) or a snapshot of an environment.
2.  **Container:** The running instance of an Image. Think of it as an object instantiated from a class. You can start, stop, move, and delete containers.
3.  **Dockerfile:** A text document containing all the commands/instructions a user could call on the command line to assemble a Docker Image.
4.  **Docker Daemon (`dockerd`):** The background service running on the host machine that manages building, running, and distributing Docker containers.
5.  **Docker Client (`docker`):** The command-line interface (CLI) that allows you to interact with the daemon (e.g., when you type `docker run`).
6.  **Docker Registry/Hub:** A centralized repository for storing Docker images. Docker Hub is the default public registry, like GitHub is for code.

### 4. Docker Architecture (How it works under the hood)
Docker uses a **Client-Server architecture**.

1.  **Client:** You run a command like `docker pull ubuntu`.
2.  **Docker Host (Daemon):** The daemon receives the command. It checks if the `ubuntu` image is stored locally.
3.  **Registry:** If not local, the daemon reaches out to Docker Hub, downloads the image, and stores it locally.
4.  **Container Execution:** When you run `docker run ubuntu`, the daemon creates a container from that image using Linux kernel features:
    *   **Namespaces:** Provide isolation (Process ID, Network, Mounts). This ensures a container can't see or affect other containers.
    *   **cgroups (Control Groups):** Limit and monitor resources (CPU, Memory). This prevents one container from hogging all system resources.

### 5. Summary and Next Steps
You now understand *why* Docker exists and the high-level architecture. We've moved from the heavy, sluggish world of Virtual Machines to the agile, lightweight world of Containers.


## Basic Commands and the Container Lifecycle

Now that we know the theory, it's time to use Docker. In this chapter, we will pull images, run containers, and understand the core lifecycle commands.

### 1. Checking Your Setup
Before running commands, verify Docker is installed and running:
```bash
docker version
docker info
```
*   `docker version` shows both the Client and Server (Daemon) versions. If you get an error about the daemon not running, ensure Docker Desktop/Service is started.

### 2. Your First Container: Hello World
Let's run the canonical test:
```bash
docker run hello-world
```
**What happens behind the scenes?**
1.  Docker CLI tells the Daemon to run the `hello-world` image.
2.  The Daemon looks for `hello-world` locally.
3.  Not finding it, the Daemon pulls it from Docker Hub.
4.  The Daemon creates a container from the image.
5.  The container runs an executable that prints "Hello from Docker!" and then exits.

### 3. Working with Images
Images are the building blocks.

*   **Pull an image (download without running):**
    ```bash
    docker pull nginx:latest
    ```
    *Note: `nginx` is the repository name, `latest` is the tag. If you omit the tag, it defaults to `latest`.*
*   **List local images:**
    ```bash
    docker images
    # or
    docker image ls
    ```
*   **Remove an image:**
    ```bash
    docker rmi nginx
    ```
    *(You cannot remove an image if a container—even a stopped one—is currently using it).*

> [!TIP] Explore basic python app deployment in [examples/01_basic_python_app](examples/01_basic_python_app)

### 4. Container Lifecycle Commands
Let's run an interactive Ubuntu container.

*   **Run and interact:**
    ```bash
    docker run -it ubuntu bash
    ```
    *   `-i` (interactive): Keeps STDIN open.
    *   `-t` (tty): Allocates a pseudo-TTY (terminal).
    *   `bash`: The command to run inside the container.
    *(Type `exit` to leave and STOP the container).*

*   **Run in the background (Detached mode):**
    ```bash
    docker run -d --name my-web-server -p 8080:80 nginx
    ```
    *   `-d`: Detached mode (runs in background).
    *   `--name`: Assign a custom name (instead of a random one).
    *   `-p 8080:80`: Port mapping. Maps port 8080 on your host (laptop) to port 80 inside the container. If you go to `http://localhost:8080` in your browser, you'll see Nginx!

*   **List containers:**
    ```bash
    # List ONLY running containers
    docker ps

    # List ALL containers (running and stopped)
    docker ps -a
    ```

*   **Start, Stop, and Restart:**
    ```bash
    docker stop my-web-server
    docker start my-web-server
    docker restart my-web-server
    ```

*   **Execute a command in an ALREADY RUNNING container:**
    ```bash
    # Open a shell in our background Nginx container
    docker exec -it my-web-server bash
    ```
    *(This is incredibly useful for debugging. Unlike `docker run` which creates a new container, `exec` enters an existing one).*

*   **View Logs:**
    ```bash
    # View all logs
    docker logs my-web-server
    
    # Tail logs (stream them live)
    docker logs -f my-web-server
    ```

*   **Remove a container:**
    ```bash
    # Container must be stopped first
    docker stop my-web-server
    docker rm my-web-server

    # Or force remove a running container
    docker rm -f my-web-server
    ```

### 5. Cleaning Up (Pruning)
Over time, you will accumulate unused images, stopped containers, and dangling resources.
```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune

# The nuclear option: Remove all unused containers, networks, images (both dangling and unreferenced)
docker system prune -a
```

### Summary Exercise
1. Run an `alpine` container in interactive mode.
2. Inside it, create a file `echo "hello" > test.txt`.
3. Exit the container.
4. Run `docker ps -a` to find its ID.
5. Start it again: `docker start <ID>`.
6. Execute a command to read the file: `docker exec <ID> cat test.txt`.
7. Stop and remove the container.


## Dockerfiles and Building Custom Images

Using pre-built images like `ubuntu` or `nginx` is great, but eventually, you need to containerize your *own* applications. We do this using a `Dockerfile`.

### 1. What is a Dockerfile?
A `Dockerfile` is a plain text file containing a list of instructions. The Docker daemon reads these instructions top-to-bottom to build a Docker Image. 

Think of it as a recipe. Every instruction in the recipe creates a new "layer" in the image.

### 2. Basic Dockerfile Instructions

| Instruction | Description | Example |
| :--- | :--- | :--- |
| `FROM` | Sets the Base Image. Must be the first instruction. | `FROM node:18-alpine` |
| `WORKDIR` | Sets the working directory inside the container. | `WORKDIR /app` |
| `COPY` | Copies files/directories from host to container. | `COPY package.json .` |
| `RUN` | Executes a command *during the build process*. | `RUN npm install` |
| `EXPOSE` | Documents the port the container listens on (doesn't actually publish it). | `EXPOSE 8080` |
| `ENV` | Sets environment variables. | `ENV NODE_ENV=production` |
| `CMD` | Default command to run *when the container starts*. | `CMD ["node", "app.js"]` |
| `ENTRYPOINT`| Configures a container that will run as an executable. | `ENTRYPOINT ["python", "main.py"]` |

*Note: `RUN` executes during `docker build`. `CMD` executes during `docker run`.*

> [!TIP] View a working Node.js example in [examples/02_basic_node_app](examples/02_basic_node_app)

### 3. Example: Containerizing a Node.js App

Let's say we have a simple Node.js app with two files:
*   `package.json`
*   `server.js`

Here is how we write the `Dockerfile`:

```dockerfile
# 1. Start with a lightweight Node.js base image
FROM node:18-alpine

# 2. Set the working directory inside the container
WORKDIR /usr/src/app

# 3. Copy package.json first (Optimization: leverages layer caching)
COPY package.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of the application code
COPY . .

# 6. Expose the port the app runs on
EXPOSE 3000

# 7. Start the application
CMD ["node", "server.js"]
```

### 4. Building the Image
Once the `Dockerfile` is created, we use the `docker build` command.
Navigate to the directory containing the Dockerfile and run:

```bash
docker build -t my-node-app:1.0 .
```
*   `-t`: Tags the image with a name and optional version (`name:tag`).
*   `.`: The build context (the current directory). Docker sends all files in this directory to the daemon.

### 5. Layer Caching (The Secret to Fast Builds)
Docker caches each layer (instruction). If an instruction and the files it uses haven't changed, Docker reuses the cached layer instead of rebuilding it.

**Why did we copy `package.json` separately from the rest of the code in the example above?**
If we did `COPY . .` first, followed by `RUN npm install`, *any* change to *any* file (like tweaking a CSS file) would invalidate the cache for the `COPY` layer. This would force Docker to run `npm install` again, which is slow!
By copying `package.json` first, the `npm install` layer is only rebuilt if the dependencies actually change.

### 6. .dockerignore
Just like `.gitignore`, you should create a `.dockerignore` file. It prevents unnecessary files (like `node_modules`, `.git`, or local secrets) from being sent to the Docker daemon.

Example `.dockerignore`:
```text
node_modules
npm-debug.log
.git
.env
```

> [!TIP] View multi-stage build examples in [examples/03_intermediate_multi_stage](examples/03_intermediate_multi_stage) and [examples_go/03_intermediate_go_multistage](examples_go/03_intermediate_go_multistage)

### 7. Multi-Stage Builds (Advanced but Essential)
Compiled languages (Go, Java, C++) need heavy build tools (compilers, SDKs). If you include these in your final image, the image becomes massive and less secure.

Multi-stage builds solve this. You use one image to compile the code, and a second, much smaller image to just run it.

```dockerfile
# --- Stage 1: Build Stage ---
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
# Compile the Go binary
RUN go build -o myapp main.go

# --- Stage 2: Production Stage ---
FROM alpine:latest  
WORKDIR /app
# Copy ONLY the compiled binary from the 'builder' stage
COPY --from=builder /app/myapp .
# Run the binary
CMD ["./myapp"]
```
*Result:* Your final image is tiny (just Alpine + the binary), free of Go compilers!

### Summary Exercise
1. Create a simple Python script `print("Hello from custom image!")`.
2. Write a Dockerfile using `FROM python:3.9-slim`.
3. Build the image: `docker build -t my-python-script .`
4. Run it: `docker run my-python-script`.

## Volumes and Bind Mounts

By default, data created inside a container is ephemeral. If the container is deleted, the data is lost forever. 
Databases and stateful applications require data persistence. Docker provides three main ways to mount data into a container.

### 1. The Ephemeral Layer (Writable Container Layer)
When a container runs, Docker adds a thin "read-write" layer on top of the read-only image. 
*   **Problem:** Data here is tightly coupled to the container's lifecycle. It's hard to extract, move, or back up. Writing to this layer also requires a storage driver (like overlay2), which is slower than writing directly to the host filesystem.

### 2. Bind Mounts
Bind mounts allow you to map a specific file or directory on your **Host OS** to a directory inside the container.
*   *Use Case:* Local development. You can mount your source code directory into the container. When you save a file in your IDE, the container sees the change immediately.

**Command:**
```bash
docker run -v /path/on/host:/path/in/container nginx
# or using the newer --mount syntax (recommended for clarity)
docker run --mount type=bind,source=/path/on/host,target=/path/in/container nginx
```

**Pros & Cons:**
*   ✅ Great for live-reloading code.
*   ❌ Ties the container to a specific host file structure.
*   ❌ Security risk (containers can modify host system files if misconfigured).

### 3. Docker Volumes (The Recommended Way)
Volumes are completely managed by Docker. They are stored in a part of the host filesystem that *only Docker* controls (e.g., `/var/lib/docker/volumes/` on Linux). Non-Docker processes should not modify this part of the filesystem.

*   *Use Case:* Databases (Postgres, MySQL, Mongo), persistent application data.

#### Volume Commands
*   **Create a volume:**
    ```bash
    docker volume create my-db-data
    ```
*   **List volumes:**
    ```bash
    docker volume ls
    ```
*   **Inspect a volume (find exactly where it lives on the host):**
    ```bash
    docker volume inspect my-db-data
    ```
*   **Use the volume in a container:**
    ```bash
    docker run -v my-db-data:/var/lib/postgresql/data postgres
    # or
    docker run --mount type=volume,source=my-db-data,target=/var/lib/postgresql/data postgres
    ```

**Why Volumes are better than Bind Mounts for Persistence:**
1.  **Portability:** Volumes are easier to back up, migrate, or share among multiple containers.
2.  **Safety:** Isolated from the host's core filesystem.
3.  **Performance:** Often perform better on Docker Desktop (Mac/Windows) than bind mounts.
4.  **Remote Storage:** Volume drivers allow storing data on remote hosts or cloud providers (AWS EBS, Azure Files).

### 4. tmpfs Mounts
A `tmpfs` mount is temporary and only stored in the host's memory (RAM). It is never written to the host's disk.
*   *Use Case:* Security-sensitive data (passwords, encryption keys) or high-performance temporary state that shouldn't persist.

```bash
docker run --mount type=tmpfs,target=/app/secrets my-secure-app
```

### Summary Table and Architecture Diagram

```arch
group host "Host Machine OS" color=slate style=dashed
node fs1 "/path/to/my/project" at 0,0 in host icon=folder sub="Bind Mount"
node fs2 "/var/lib/docker/..." at 1,0 in host icon=database sub="Docker Volume"
node ram "Host RAM" at 2,0 in host icon=memory sub="tmpfs"

group cont "Docker Container" color=blue
node m1 "/app/code" at 0,1 in cont icon=folder
node m2 "/var/lib/postgresql/data" at 1,1 in cont icon=folder
node m3 "/app/secrets" at 2,1 in cont icon=folder
node app "Running Application" at 1,2 in cont icon=app

fs1 <..> m1
fs2 <..> m2
ram <..> m3
m1 <..> app
m2 <..> app
m3 <..> app
```

| Type | Managed By | Where it lives | Best For |
| :--- | :--- | :--- | :--- |
| **Bind Mount** | User | Anywhere on Host OS | Local development, sharing configs |
| **Volume** | Docker | Docker-managed area (e.g., `/var/lib/docker/volumes`) | Databases, persistent app data |
| **tmpfs** | Host RAM | Memory (RAM) | Secrets, non-persistent fast caching |

### Summary Exercise
1. Create a volume named `html_data`.
2. Run an Nginx container and mount `html_data` to `/usr/share/nginx/html`.
3. Exec into the container and create an `index.html` file in that directory.
4. Delete the container (`docker rm -f`).
5. Run a *new* Nginx container and mount the *same* `html_data` volume.
6. Verify your `index.html` file is still there!

## Docker Networking

Containers need to talk to each other, to the host machine, and to the outside world. Docker networking manages this communication through different network drivers.

```arch
group host "Host OS Network" color=slate style=dashed
node eth0 "Physical Interface eth0" at 1.5,0 in host icon=network

group bridge "Default Bridge docker0" color=amber
node c1 "Container 1" at 0,1 in bridge icon=app sub="172.17.0.2"
node c2 "Container 2" at 1,1 in bridge icon=app sub="172.17.0.3"

group custom "User-Defined Bridge my-net" color=blue
node c3 "Container: backend" at 2,1 in custom icon=app sub="172.18.0.2"
node c4 "Container: db" at 3,1 in custom icon=database sub="172.18.0.3"

eth0 -- c1
eth0 -- c2
eth0 -- c3
eth0 -- c4

c1 .. c2 : "No DNS"
c3 <..> c4 : "Automatic DNS"
```

### 1. The Default Network: Bridge
When you install Docker, it creates a default network called `bridge` (often represented by the `docker0` interface on Linux).

*   **How it works:** Unless specified otherwise, every new container attaches to this default bridge network.
*   **Communication:** Containers on the default bridge can communicate with each other via their internal IP addresses. However, IP addresses change when containers restart.
*   **Limitation:** DNS resolution (pinging a container by its name) does NOT work on the default bridge network.

### 2. User-Defined Bridge Networks (The Best Practice)
For production and multi-container apps, you should create a custom bridge network.

#### Why User-Defined Bridges?
1.  **Automatic DNS Resolution:** Containers can find each other by their container name. If you have a web container and a db container, the web container can connect to `postgres://db:5432`—no need to hardcode IPs!
2.  **Better Isolation:** You can group related containers in one network, isolating them from containers in other networks.

#### Commands
*   **Create a network:**
    ```bash
    docker network create my-app-network
    ```
*   **Run a container on that network:**
    ```bash
    docker run -d --name database --network my-app-network postgres
    docker run -d --name backend --network my-app-network my-node-app
    ```
    *(Now, the backend can reach the database simply by querying the hostname `database`)*

### 3. Host Network
If you use the `host` network driver, the container's network stack is not isolated from the Docker host. The container shares the host's IP address and ports.

```bash
docker run --network host nginx
```
*   **Pros:** Maximum network performance (no network address translation overhead).
*   **Cons:** Port conflicts. If the host is already using port 80, the Nginx container will fail to start. Less secure due to reduced isolation.
*   *Note: This driver only fully works on Linux.*

### 4. None Network
This completely disables networking for the container. It will have a loopback interface (`lo`) but no external network interfaces.
*   *Use Case:* Running highly secure, isolated batch processing jobs that don't need network access.
```bash
docker run --network none alpine
```

### 5. Overlay Network (For Docker Swarm)
Overlay networks connect multiple Docker daemons together and enable swarm services to communicate with each other. You use this when you have a cluster of machines running Docker (though Kubernetes has largely replaced Docker Swarm in the industry).

### 6. Macvlan
Macvlan allows you to assign a MAC address to a container, making it appear as a physical device on your physical network. The Docker daemon routes traffic to containers by their MAC addresses.
*   *Use Case:* Legacy applications that expect to be directly connected to the physical network.

### Summary Exercise
1. Create a network: `docker network create testing-net`.
2. Run two containers on it:
   `docker run -d --name alpine1 --network testing-net alpine sleep 1000`
   `docker run -d --name alpine2 --network testing-net alpine sleep 1000`
3. Exec into the first container: `docker exec -it alpine1 sh`.
4. Ping the second container by name: `ping alpine2`. (Watch it successfully resolve the IP and ping).
5. Exit and clean up.

## Managing Multi-Container Applications

So far, we've used `docker run` to start individual containers. But real-world applications are rarely a single container. You usually have a frontend, a backend, a database, and maybe a caching layer (like Redis).

Starting these manually, creating networks, and linking volumes is tedious and error-prone. Enter **Docker Compose**.

### 1. What is Docker Compose?
Docker Compose is a tool for defining and running multi-container Docker applications. You use a YAML file (`docker-compose.yml`) to configure your application's services. Then, with a single command, you create and start all the services from your configuration.

```arch
node user "User/Browser" at 0,0 icon=user
node web "Web Service" at 1,0 icon=app sub="Flask/Node"
node db "Database Service" at 2,0 icon=postgresql sub="PostgreSQL"
node vol "Named Volume" at 3,0 icon=database sub="DB Data"

user -> web : "Port 5000"
web -> db : "Queries"
db <..> vol : "Persists"
```

> [!TIP] View a full docker-compose example in [examples/04_intermediate_docker_compose](examples/04_intermediate_docker_compose)

### 2. The docker-compose.yml File
The compose file is declarative. You state *what* you want, and Compose makes it happen.

Let's look at an example for a web app that uses Python (Flask) and a Redis database.

```yaml
version: '3.8' # The Compose file format version

services: # Define the containers
  web:
    build: . # Build the image using the Dockerfile in the current directory
    ports:
      - "5000:5000" # Map host port 5000 to container port 5000
    volumes:
      - .:/code # Mount current dir to /code (for live reloading)
    environment:
      - FLASK_ENV=development
    depends_on: # Ensure redis starts before the web service
      - redis

  redis:
    image: "redis:alpine" # Use a pre-built image from Docker Hub
    # No ports mapped to the host, it's only accessible internally by the 'web' service!
```

#### Key Components:
*   **`services`:** The individual containers you want to run.
*   **`build`:** Tells compose to build an image from a Dockerfile.
*   **`image`:** Tells compose to use an existing image.
*   **`ports`:** Port mappings (`HOST:CONTAINER`).
*   **`volumes`:** Volume mappings.
*   **`environment`:** Environment variables.
*   **`depends_on`:** Defines startup order.

### 3. The Magic of Compose Networking
When you run Docker Compose, it automatically does the following:
1.  Creates a user-defined bridge network for your application.
2.  Attaches all defined services to that network.
3.  Allows services to talk to each other using their service name as the hostname.

In the example above, the Python `web` code can connect to the database using the hostname `redis`.

### 4. Docker Compose Commands

You must run these commands in the directory containing your `docker-compose.yml`.

*   **Start everything (in the foreground):**
    ```bash
    docker-compose up
    ```
*   **Start everything (in the background/detached):**
    ```bash
    docker-compose up -d
    ```
*   **Stop and remove containers, networks, and volumes:**
    ```bash
    docker-compose down
    # To remove named volumes as well:
    docker-compose down -v
    ```
*   **View logs for all services:**
    ```bash
    docker-compose logs -f
    ```
*   **Rebuild images (if you changed your Dockerfile or code):**
    ```bash
    docker-compose up -d --build
    ```

### 5. Overrides and Environments
In production, you don't want to use the same configurations as local development (e.g., you don't want bind mounts for live-reloading in prod).

You can use multiple Compose files. By default, Compose reads `docker-compose.yml` and a `docker-compose.override.yml`. 
For production, you might run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
The second file overwrites or adds configuration to the first.

### Summary Exercise
1. Create an empty directory and navigate into it.
2. Create a `docker-compose.yml` with a `postgres` database and an `adminer` (database UI) service.
3. Configure `adminer` to expose port `8080`.
4. Run `docker-compose up -d`.
5. Visit `localhost:8080` in your browser and log into the database using the service name as the host.
6. Clean up with `docker-compose down`.

## Security, Limits, and Internals

To be a Senior Software Engineer, you must understand how Docker works under the hood and how to secure it. Containers are not magical boxes; they are just isolated Linux processes.

### 1. Under the Hood: Namespaces and cgroups

Docker relies on two core Linux kernel features to create the illusion of a separate computer.

#### Linux Namespaces (Isolation)
Namespaces control *what a process can see*. They partition kernel resources.
*   **PID Namespace:** Provides a separate set of Process IDs. Process `1` inside the container is not process `1` on the host.
*   **NET Namespace:** Provides a separate network stack (interfaces, IP addresses, routing tables).
*   **MNT Namespace:** Provides an isolated view of the filesystem (mount points).
*   **UTS Namespace:** Allows the container to have its own hostname.
*   **IPC Namespace:** Isolates Inter-Process Communication.
*   **USER Namespace (Important for Security):** Allows mapping a user inside the container to a different (unprivileged) user on the host.

#### Control Groups (cgroups) (Resource Limiting)
cgroups control *what a process can use*.
They limit, account for, and isolate resource usage (CPU, memory, disk I/O) of a collection of processes. Without cgroups, one rogue container could consume 100% of the host's RAM, crashing the entire server (a "noisy neighbor" problem).

### 2. Resource Limits (Applying cgroups)
Never run containers in production without resource limits!

**Limiting Memory:**
```bash
# Hard limit of 512 Megabytes
docker run -m 512m nginx

# Soft limit (reservation). Container can use more if host has free memory, but will be forced back to 256m if host runs low.
docker run --memory-reservation 256m nginx
```
*Note: If a container exceeds its hard memory limit, the Linux OOM (Out Of Memory) killer will terminate it.*

**Limiting CPU:**
```bash
# Limit to 1.5 CPUs
docker run --cpus="1.5" nginx
```

**In Docker Compose:**
```yaml
services:
  web:
    image: nginx
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 3. Docker Security Best Practices

#### A. Don't run as root!
By default, Docker containers run as the `root` user. If a hacker escapes the container (container breakout), they are root on the host machine!
**Fix:** Define a non-root user in your Dockerfile.
```dockerfile
FROM node:18-alpine
# Create a user 'appuser'
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY . .
# Switch to that user
USER appuser
CMD ["node", "app.js"]
```

#### B. Use Minimal Base Images
Images like `ubuntu` or `debian` are large and contain hundreds of utilities (like `curl`, `wget`, `bash`). This increases the "attack surface".
*   **Fix:** Use `alpine` based images (e.g., `node:alpine`). They are ~5MB and contain almost nothing.
*   **Even better (for compiled languages):** Use `scratch` or Google's `distroless` images. These contain *only* your application and its runtime dependencies. No shell, no utilities. If a hacker gets in, they can't even run `ls`!

#### C. Read-Only Filesystems
If your application doesn't need to write to the disk, run the container with a read-only filesystem. If a hacker compromises the app, they cannot download malicious scripts or modify binaries.
```bash
docker run --read-only nginx
```

#### D. Drop Capabilities
The Linux root user has many "capabilities" (granular permissions like changing ownership, killing processes). A containerized root user has a restricted subset of these, but it's still too many.
You should drop all capabilities and only add back what is strictly necessary.
```bash
# Drop everything, then only allow binding to ports < 1024
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx
```

#### E. Keep Images Scanned and Updated
Use tools like `Trivy`, `Clair`, or Docker's built-in `docker scan` to analyze your images for known CVEs (Common Vulnerabilities and Exposures).

### 4. Docker Daemon Socket (/var/run/docker.sock)
The Docker CLI communicates with the Daemon via a Unix socket: `/var/run/docker.sock`.
**CRITICAL RULE:** Never mount this socket inside a container unless you absolutely trust the container (e.g., a CI/CD agent like Jenkins or Portainer).
```bash
# DANGEROUS!
docker run -v /var/run/docker.sock:/var/run/docker.sock ubuntu
```
If a container has access to this socket, it has root access to your host. It can spawn new containers, delete containers, and compromise the entire system.

### Summary
Understanding namespaces, cgroups, and security principles separates junior developers from senior engineers. In production, security and resource constraints are just as important as the application code itself.

## MAANG/FAANG Interview Questions (Docker & Containers)

When interviewing for DevOps, SRE, or Senior Backend roles at top-tier companies, you won't just be asked "What is a container?". You will be tested on internal architecture, debugging, edge cases, and distributed systems design.

Here are the most frequently asked, high-level interview questions.

---

#### Q1: Can you explain the difference between a Container and a Virtual Machine at the OS level?
**Answer:**
A Virtual Machine uses a Hypervisor (like KVM or VMware) to virtualize the physical hardware. Each VM runs its own complete Guest OS (kernel + user space), which consumes significant RAM and CPU just for the OS overhead.
A Container, on the other hand, virtualizes the OS itself. It runs directly on the Host OS. Containers share the single Host Kernel but use Linux **Namespaces** to isolate their user space (processes, network, mounts) and **cgroups** to limit their hardware resource usage. This makes containers lightweight, fast to boot, and highly efficient.

#### Q2: What happens exactly when you type `docker run -d nginx`?
**Answer:**
1.  The Docker CLI parses the command and sends a REST API request to the Docker Daemon (`dockerd`) via the local Unix socket (`/var/run/docker.sock`).
2.  The Daemon checks its local image cache for the `nginx:latest` image.
3.  If not found, it pulls the image from the configured registry (Docker Hub).
4.  The Daemon instructs `containerd` (the container runtime) to create the container.
5.  `containerd` uses `runc` (the OCI low-level runtime) to interface with the Linux kernel.
6.  `runc` sets up the Namespaces (PID, Mount, Net, etc.) and cgroups.
7.  A read-write layer is mounted on top of the image's read-only layers.
8.  The network interface is created (attached to the default bridge).
9.  The container's main process (defined by `ENTRYPOINT`/`CMD`) is started.
10. Because of `-d`, the CLI detaches, and the Daemon returns the container ID.

#### Q3: How does Docker Image Caching work, and how do you optimize a Dockerfile for it?
**Answer:**
Docker builds images layer by layer. Each instruction in a Dockerfile (`FROM`, `COPY`, `RUN`) creates a new layer. Docker caches these layers. When rebuilding, if an instruction hasn't changed and the layers before it haven't changed, Docker reuses the cached layer.
**Optimization:** You should order instructions from least likely to change to most likely to change.
For example, in Node.js, you should `COPY package.json`, then `RUN npm install`, and *then* `COPY . .` (the source code). If you copy the source code first, any code change invalidates the cache, forcing a slow `npm install` on every build.

#### Q4: You have a container that is constantly crashing with an "OOMKilled" error. How do you troubleshoot this?
**Answer:**
`OOMKilled` (Out of Memory) means the container exceeded its hard memory limit set by cgroups.
1.  **Verify the limit:** I would use `docker inspect <container_id>` to check the `Memory` limit configured for the container.
2.  **Monitor usage:** Use `docker stats` to watch real-time memory consumption, or check Prometheus/Grafana if it's in a Kubernetes cluster.
3.  **Application Profiling:** The root cause is likely a memory leak in the application. I would attach a profiler (e.g., pprof for Go, heap dumps for Java/Node) to identify which objects are not being garbage collected.
4.  **Temporary fix:** If it's a spike in traffic rather than a leak, I might temporarily increase the memory limit in the deployment configuration while the dev team fixes the code.

#### Q5: Explain the difference between `ADD` and `COPY` in a Dockerfile. Which one should you use?
**Answer:**
Both copy files into the image, but `ADD` has two extra features:
1.  It can extract `.tar` files automatically.
2.  It can download files from a remote URL.
**Best Practice:** You should almost always use `COPY`. It is more predictable and transparent. Downloading from URLs via `ADD` is discouraged because it creates an extra layer and you can't easily clean up the downloaded archive in the same layer. Instead, use `RUN curl ... && tar ... && rm ...` to keep the image size small.

#### Q6: What is a Multi-stage build and why is it crucial for production?
**Answer:**
A multi-stage build uses multiple `FROM` statements in a single Dockerfile.
It is crucial because compiled languages (Go, Java) require heavy toolchains (compilers, SDKs) to build the code. If we leave these in the final image, the image becomes massive and insecure (increased attack surface).
With multi-stage builds, Stage 1 (the builder) contains the SDK and compiles the binary. Stage 2 (production) uses a minimal base image (like `alpine` or `scratch`) and simply `COPY --from=builder` the compiled binary. This results in tiny, secure production images.

#### Q7: If you start a container and mount the host's `/var/run/docker.sock` into it, what are the security implications?
**Answer:**
This is extremely dangerous. The `docker.sock` is the Unix socket the Docker daemon listens on. If a container has access to this socket, it can send API requests directly to the host's Docker daemon.
The container can effectively break out of its isolation. It can launch a new privileged container, mount the host's root filesystem `/`, and gain complete root access to the physical host machine. This pattern should only be used for highly trusted administrative tools, and never for user-facing applications.

#### Q8: How would you design a CI/CD pipeline to build and deploy Docker images securely?
**Answer:**
1.  **Code Commit:** Developer pushes code to Git.
2.  **Build:** CI server (e.g., GitHub Actions, Jenkins) checks out code and runs unit tests.
3.  **Docker Build:** CI builds the Docker image using a multi-stage Dockerfile.
4.  **Security Scan:** The CI pipeline runs a vulnerability scanner (like Trivy or Snyk) against the built image. If High/Critical CVEs are found, the build fails.
5.  **Push:** If the scan passes, the image is tagged with a Git hash or semantic version and pushed to a secure, private Container Registry (like AWS ECR, Google Artifact Registry).
6.  **Deploy:** The CD pipeline updates the manifest (e.g., a Kubernetes Deployment or Helm chart) with the new image tag and applies it to the cluster.

---
**End of Docker Guide**
You have now completed the zero-to-hero journey for Docker and Containers!

## Registries, CI/CD, and Image Distribution

Building images locally is only half the battle. To deploy applications, those images must be stored centrally and distributed to your production servers (or Kubernetes clusters). This is where Registries and CI/CD come in.

### 1. What is a Docker Registry?
A registry is a highly scalable server-side application that stores and lets you distribute Docker images.
*   **Docker Hub:** The default, public registry provided by Docker. (Like GitHub for open-source code).
*   **Private Registries:** Used by enterprises to keep proprietary code secure. Examples include AWS ECR (Elastic Container Registry), Google Artifact Registry, Azure Container Registry, and self-hosted solutions like Harbor or Artifactory.

### 2. Working with Registries (Pushing an Image)

To push an image to a registry, the image name must contain the registry URL and your username/project ID.

**Step 1: Tag the Image correctly**
Let's say you built a local image: `docker build -t my-app:v1 .`
To push it to your Docker Hub account (e.g., username `johndoe`), you must tag it:
```bash
# Format: registry_url/username/repository:tag
# (Docker Hub URL is implied if omitted)
docker tag my-app:v1 johndoe/my-app:v1
```

**Step 2: Authenticate**
```bash
docker login
# Or for a cloud provider like AWS:
# aws ecr get-login-password | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
```

**Step 3: Push the Image**
```bash
docker push johndoe/my-app:v1
```
Docker will push the image layer by layer. Because of layer caching, if you only changed one line of code, Docker only pushes that tiny new layer, saving massive amounts of bandwidth and time.

### 3. Docker BuildKit (The Modern Build Engine)
In older versions of Docker, builds were sequential and sometimes slow. Docker introduced **BuildKit**, a modern, highly optimized build engine.

It is enabled by default in modern Docker Desktop installations. If you are on an older Linux server, you can enable it by setting an environment variable:
```bash
DOCKER_BUILDKIT=1 docker build -t my-app .
```
**Benefits of BuildKit:**
*   **Concurrent Builds:** It builds independent multi-stage layers at the same time.
*   **Better Caching:** It caches aggressively and only pulls files needed for the current build stage.
*   **Secrets Management:** It allows you to pass secrets (like SSH keys or API tokens) into a build *without* leaving them in the final image layers.

### 4. Containerizing in CI/CD (The Big Picture)
As a Senior Engineer, you design the automation. Here is what a standard Continuous Integration / Continuous Deployment (CI/CD) pipeline looks like for containers:

```arch
node dev "Developer" at 0,0 icon=developer
node gh "GitHub" at 1,0 icon=github-icon
node run "CI Runner" at 1,1 icon=process

group ci "Continuous Integration" color=blue
node tst "Unit Tests" at 1,2 in ci icon=check
node bld "docker build" at 1,3 in ci icon=docker-icon
node scn "Security Scan" at 1,4 in ci icon=shield sub="Trivy"

group cd "Continuous Deployment" color=purple
node psh "docker push" at 2,4 in cd icon=cli
node reg "Private Registry" at 2,5 in cd icon=database sub="ECR"
node dep "Deployment" at 2,6 in cd icon=process sub="ArgoCD"
node k8s "Kubernetes Cluster" at 2,7 in cd icon=kubernetes

node alert "Alert Developer" at 0,3 icon=alert

dev -> gh : "git push"
gh -> run : "Triggers"
run -> tst
tst -> bld : "Pass"
bld -> scn
scn -> psh : "Pass"
psh -> reg
reg -> dep : "GitOps"
dep -> k8s
tst -> alert : "Fail"
scn -> alert : "Fail"
```

1.  **Code Push:** A developer pushes a commit to the `main` branch.
2.  **Trigger:** GitHub Actions (or Jenkins/GitLab CI) detects the push.
3.  **Test:** The pipeline spins up a temporary container, mounts the code, and runs Unit Tests.
4.  **Build:** If tests pass, the pipeline runs `docker build`.
5.  **Scan:** The pipeline uses a tool like **Trivy** to scan the image for CVEs (Security Vulnerabilities). If a critical vulnerability is found, the pipeline fails.
6.  **Push:** The pipeline authenticates with the secure Private Registry (e.g., AWS ECR) and runs `docker push`.
7.  **Deploy (GitOps):** The pipeline updates a Kubernetes manifest repository with the new image tag. A tool like ArgoCD detects the change and pulls the new image into the production cluster.

### Summary
You now understand the complete lifecycle: from writing a `Dockerfile` locally, handling storage and networking, securing the container processes, to finally pushing the image to a remote registry via an automated CI/CD pipeline. 

You are now fully equipped to master Docker in a production environment!
