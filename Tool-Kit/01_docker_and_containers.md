# Docker and Containerization

Containers are the unit of deployment for modern backend applications. An image packages
your code, its runtime, system libraries and configuration into one immutable,
content-addressed artifact that runs the same way on a laptop, a CI runner and a
production Kubernetes node. This chapter starts from "what problem does a container
solve" and goes down to the kernel features that make one (namespaces, cgroups,
overlay filesystems), then covers what an interviewer or an on-call shift will test:
writing fast, small, secure `Dockerfile`s, the build cache, storage and networking,
resource limits and exit codes, supply-chain security, and a debugging playbook.

## Foundations — What is a container, and why does everyone ship software in one?

### The problem: "it works on my machine"

A Python service needs Python 3.12, `libpq` for Postgres, a specific OpenSSL, a timezone
database and forty pip packages at exact versions. Your laptop has some of these,
at slightly different versions. The CI runner has others. The production server was set
up by hand two years ago. Each difference is a chance for the service to behave
differently, and the classic result is a bug that only appears in production.

Before containers, teams fought this three ways, each with a cost:

| Approach | What you ship | Problem |
|---|---|---|
| Configuration management (Ansible, Chef, Puppet) | A script that installs everything on a long-lived server | Servers drift; two runs a year apart produce different machines |
| Virtual machine images | A whole guest OS per app | Gigabytes per image, tens of seconds to boot, one kernel per app |
| Language bundles (fat JARs, virtualenvs) | The app plus its language-level dependencies | Still depends on the host's system libraries and OS |

A **container image** fixes the problem by shipping the app *together with its entire
user-space filesystem* (everything except the kernel), and a **container** runs that
filesystem as an isolated process on any Linux kernel. The image is built once, given a
content hash, and the same bytes run everywhere.

### The pieces

| Piece | What it is | Everyday analogy |
|---|---|---|
| **Image** | A read-only stack of filesystem layers plus metadata (entrypoint, env, user, ports) | A frozen meal: prepared once, identical every time you heat it |
| **Container** | A running (or stopped) instance of an image: a process with its own view of the filesystem, network and process table, plus a thin writable layer | The meal on your plate: you can add salt, but the frozen original is unchanged |
| **Dockerfile** | The recipe that builds an image, one instruction per step | The recipe card |
| **Registry** | A server that stores and serves images by name and digest (Docker Hub, GitHub Container Registry, Amazon ECR, Google Artifact Registry) | The supermarket freezer |
| **Engine / runtime** | The software on the host that pulls images and starts containers (Docker Engine, containerd, CRI-O, runc) | The microwave |

### How they fit, in one example

You write a `Dockerfile`, run `docker build -t shop-api:1.4.2 .`, and Docker produces an
image whose identity is a SHA-256 digest such as `sha256:3f1c…`. You `docker push` it to
a registry. A production host (or Kubernetes node) runs `docker pull` / the runtime pulls
it, and starts it with `docker run -p 8080:8080 shop-api:1.4.2`. The process inside sees
its own `/` (the image's files), its own process tree where it is PID 1, its own network
interface, and a memory cap. It shares the host's kernel with every other container on
the machine.

```arch
%% caption: Build once, push the immutable image to a registry, and run the same bytes everywhere.
grid 170x110
node dev "Developer" at 0,0 icon=developer sub="writes Dockerfile"
node build "docker build" at 1,0 icon=package sub="BuildKit"
node reg "Registry" at 2,0 icon=storage sub="name:tag → digest"
group hosts "Anywhere with a Linux kernel" color=blue icon=server
node ci "CI runner" at 1,1 in hosts icon=worker sub="runs tests"
node prod "Prod node" at 2,1 in hosts icon=container sub="runs service"
node lap "Laptop" at 3,1 in hosts icon=desktop sub="reproduces bug"
dev -> build : "source"
build -> reg : "push"
reg -> ci
reg -> prod
reg -> lap
```

### Container vs virtual machine

A VM virtualizes *hardware*: a hypervisor presents virtual CPUs, disks and NICs, and each
VM boots its own full kernel. A container virtualizes the *operating system's view*: it
is an ordinary Linux process that the kernel has been told to isolate (namespaces) and
limit (cgroups). There is no guest kernel and no boot.

```arch
%% caption: VMs each boot a guest kernel on a hypervisor; containers are isolated processes sharing the host kernel.
grid 140x95
group vm "Virtual machines" color=slate icon=server
node va "App A" at 0,0 in vm icon=app
node vb "App B" at 1,0 in vm icon=app
node ga "Guest OS" at 0,1 in vm icon=server
node gb "Guest OS" at 1,1 in vm icon=server
node hyp "Hypervisor" at 0.5,2 in vm icon=cpu
group ct "Containers" color=blue icon=container
node ca "App A + libs" at 2,0 in ct icon=container
node cb "App B + libs" at 3,0 in ct icon=container
node rt "Container runtime" at 2.5,1 in ct icon=docker-icon
node kern "Shared host kernel" at 2.5,2 in ct icon=linux-tux
va -> ga
vb -> gb
ga -> hyp
gb -> hyp
ca -> rt
cb -> rt
rt -> kern
```

| | Virtual machine | Container |
|---|---|---|
| Isolation boundary | Hardware virtualization; separate kernel | Kernel namespaces, cgroups, seccomp, capabilities |
| Start time | Seconds to tens of seconds (boot) | ≈ tens to hundreds of milliseconds (process start) |
| Image size | Gigabytes | Megabytes (a static Go binary on `scratch` can be under 20 MB) |
| Can run a different kernel/OS | Yes (Windows guest on Linux host) | No; a Linux container needs a Linux kernel (Docker Desktop runs a small Linux VM on macOS/Windows for this reason) |
| Security strength | Strong; hypervisor escapes are rare | Weaker; a kernel bug can be a container escape. Sandboxes such as gVisor and Kata Containers close the gap |

**Precision note:** "a container is a lightweight VM" is the most common wrong answer in
interviews. The precise answer is **a container is a process with namespaces for
isolation and cgroups for limits, running from a layered image filesystem, on a shared
kernel.** [Operating Systems & Hardware Symbiosis](../CSFundamentals/01_operating_systems_deep_dive.md) §6 covers the process
side of this.

### Vocabulary you will meet below

| Term | Meaning |
|---|---|
| OCI | Open Container Initiative: the vendor-neutral specs for the image format, the runtime and registry distribution. Docker, Podman, containerd and Kubernetes all speak it |
| Layer | A tarball of filesystem changes produced by one build step, identified by its digest |
| Tag vs digest | A tag (`:1.4.2`, `:latest`) is a movable name; a digest (`@sha256:…`) is the immutable content hash |
| Base image | The image in your `FROM` line (e.g. `python:3.12-slim`, `gcr.io/distroless/static`) |
| BuildKit | Docker's build engine (the default since Docker Engine 23.0); parallel stages, cache mounts, secrets |
| containerd / runc | The daemon that manages images and container lifecycles, and the low-level tool that actually creates the namespaces and cgroups |

## 1. Under the hood: namespaces, cgroups and the runtime stack

### Namespaces: what a process can *see*

The kernel gives each container its own instance of several global resources:

| Namespace | Isolates | Effect inside the container |
|---|---|---|
| `pid` | Process IDs | The app is PID 1; it cannot see host processes |
| `net` | Network interfaces, routing tables, ports, iptables | Its own `eth0` and `localhost`; can bind port 80 without clashing with the host |
| `mnt` | Mount table | Its own `/` built from the image layers |
| `uts` | Hostname and domain name | `hostname` returns the container ID or the name you set |
| `ipc` | System V IPC, POSIX message queues | Cannot attach to host shared memory |
| `user` | UID/GID mapping | Root inside can map to an unprivileged UID outside (rootless mode) |
| `cgroup` | View of the cgroup hierarchy | Sees only its own cgroup subtree |
| `time` | Boot and monotonic clocks | Rarely used by Docker |

You can see them from the host: `ls -l /proc/<pid>/ns/` lists one symlink per namespace,
and two processes share a namespace exactly when the inode numbers match. `nsenter -t
<pid> -n ss -ltnp` runs the host's `ss` inside a container's network namespace, which is
how you debug a container image that has no shell.

### Cgroups: what a process can *use*

Control groups (cgroup v2 is the default on current distributions and on Kubernetes)
account and limit resources for a group of processes:

- **memory.max**: a hard ceiling. Exceed it and the kernel's OOM killer kills a process in
  the cgroup; Docker reports the container as `OOMKilled` with exit code **137**
  (128 + SIGKILL 9), even if the host has free RAM.
- **cpu.max**: a quota per period (default period 100 ms). `--cpus=1.5` means 150 ms of
  CPU time per 100 ms period across all cores. A multi-threaded app that burns its
  quota early in the period is **throttled** for the rest of it, which shows up as p99
  latency spikes, not as high CPU. This is the root of the "remove CPU limits"
  debate in Kubernetes (chapter 02 §4).
- **cpu.weight**: relative share when CPUs are contended (Docker's `--cpu-shares`).
- **pids.max**: caps process count, which stops a fork bomb.
- **io.max**: per-device read/write bandwidth and IOPS limits.

### The runtime stack

```arch
%% caption: The docker CLI talks to dockerd, which delegates to containerd; runc creates the namespaces and cgroups, then exits.
grid 180x88
node cli "docker CLI" at 0,0 icon=cli sub="REST over a Unix socket"
node dockerd "dockerd" at 0,1 icon=docker-icon sub="builds, networks, volumes"
node containerd "containerd" at 0,2 icon=container sub="images, snapshots, lifecycle"
node shim "containerd-shim" at 0,3 icon=process sub="one per container"
node runc "runc" at 1,3 icon=code sub="OCI runtime, exits after start"
node app "Your process" at 0,4 icon=app sub="PID 1 in its namespaces"
node kubelet "kubelet" at 1,1 icon=kubernetes sub="Kubernetes node agent"
cli -> dockerd -> containerd -> shim
kubelet -> containerd : "CRI"
shim -> runc : "create"
shim -> app : "stdio, exit code"
runc ..> app : "clone + exec"
```

- **dockerd** is the Docker daemon: it owns builds (via BuildKit), networks, volumes and
  the API the CLI calls.
- **containerd** (a CNCF graduated project) manages images, snapshots (layer mounts) and
  container lifecycles. Kubernetes talks to it directly through the Container Runtime
  Interface (CRI).
- **runc** reads an OCI runtime bundle (a root filesystem plus a `config.json`), calls
  `clone()` with the namespace flags, writes the cgroup files, applies seccomp and
  capabilities, `exec`s your entrypoint and exits. The **shim** stays behind as the
  parent, so dockerd or containerd can restart without killing your containers.

**Kubernetes and Docker, precisely:** Kubernetes removed *dockershim* (its built-in
adapter to dockerd) in v1.24 (2022). Nodes now run containerd or CRI-O directly. Images
built with `docker build` still run unchanged, because they are OCI images; what went
away is only dockerd on the node.

## 2. Images and layers

### What an image actually is

An image is a **manifest** (a JSON document) that points at a **config** blob (entrypoint,
env, user, working dir, history) and an ordered list of **layer** blobs (compressed
tarballs). Every blob is stored and fetched by its SHA-256 digest, so a layer shared by
two images is stored and downloaded once. A multi-architecture image is an **index**
(manifest list) pointing at one manifest per platform, such as `linux/amd64` and
`linux/arm64`; the runtime picks the one matching the host.

```bash
docker buildx imagetools inspect python:3.12-slim   # the index and per-platform manifests
docker image inspect shop-api:1.4.2 --format '{{json .RootFS.Layers}}'
docker history shop-api:1.4.2                       # which instruction made which layer, and its size
```

### How layers become a filesystem: overlayfs

At run time the storage driver (`overlay2` on Linux) stacks the read-only image layers
as `lowerdir`s and adds one empty writable `upperdir` for the container:

```arch
%% caption: overlayfs shows one merged root; a lookup falls through from the writable layer down the read-only image layers.
grid 230x80
group ctr "Container" color=blue icon=container
node merged "Merged view: /" at 0,0 in ctr icon=folder sub="what the process sees"
node up "Writable upperdir" at 0,1 in ctr icon=edit sub="copy-up, whiteouts"
group img "Image (read-only, shared)" color=slate icon=layers
node l4 "Layer 4: COPY app" at 0,2 in img icon=layers
node l3 "Layer 3: pip install" at 0,3 in img icon=layers
node l2 "Layer 2: apt packages" at 0,4 in img icon=layers
node l1 "Layer 1: debian base" at 0,5 in img icon=layers
merged -> up : "lookup"
up -> l4
l4 -> l3 -> l2 -> l1
```

- **Reads** fall through the stack: the topmost layer that has the file wins.
- **Writing an image file** triggers **copy-up**: the whole file is copied into the
  upperdir first. Appending one line to a 2 GB file in the image copies 2 GB. Databases
  must therefore write to a **volume**, not the container filesystem.
- **Deleting an image file** creates a **whiteout** entry in the upper layer. The bytes
  are still in the lower layer. This is why `RUN rm big.tar` in a *later* instruction
  does not shrink the image, and why a secret `COPY`'d in one layer and deleted in the
  next is still extractable with `docker save`.

### Tags, digests and reproducibility

`python:3.12-slim` is re-pointed every time Debian ships a security fix. That is what you
want for patching, and exactly what you do not want when you need to know what is running.
Production practice:

- Build with a tag, deploy by **digest**: `image: registry.example.com/shop-api@sha256:3f1c…`.
  Kubernetes, Argo CD and Helm all accept digests.
- Never deploy `:latest`. It is only a default name, not "the newest": it points at
  whatever was last pushed without a tag.
- Rebuild regularly (e.g. nightly or weekly) so the base-image patches actually reach you,
  and let tooling such as Renovate or Dependabot bump pinned digests with a PR.

## 3. Writing Dockerfiles that build fast, stay small and run safely

### The build cache, precisely

BuildKit caches each instruction's result. An instruction's cache key is its text plus
its parent layer, and for `COPY`/`ADD` also a checksum of the files copied. **The first
instruction whose key changes invalidates itself and every instruction after it.**
Everything else follows from that rule:

1. **Order by frequency of change.** OS packages at the top, dependency manifests next,
   dependency install, then the source code last.
2. **Copy the dependency manifest alone first** (`go.mod go.sum`, `package.json
   package-lock.json`, `pyproject.toml uv.lock`), install, *then* `COPY . .`. Editing one
   source line then reuses the expensive dependency layer.
3. **Use a `.dockerignore`.** `COPY . .` otherwise sends `.git/`, `node_modules/`, local
   `.env` files and build output into the context, busts the cache on every commit, and
   can leak secrets into the image.
4. **Clean up in the same `RUN`.** `apt-get update && apt-get install -y --no-install-recommends … && rm -rf /var/lib/apt/lists/*`
   in one instruction. A cleanup in a later layer only adds a whiteout.
5. **Cache mounts for package managers.** `RUN --mount=type=cache,target=/root/.cache/pip pip install …`
   keeps the download cache on the builder between builds without putting it in any layer.

### Multi-stage builds

A multi-stage build uses one stage with compilers and headers to produce an artifact,
and a final stage that copies in only the artifact. The build tools never reach
production, which shrinks the image and the attack surface.

### Example: a production Go Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
# ---- Stage 1: build --------------------------------------------------------
FROM golang:1.26-alpine AS builder

# CA certificates for outbound HTTPS, tzdata for time.LoadLocation
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /src
# Dependency manifests first: this layer is reused until go.mod/go.sum change
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download

# Then the source
COPY . .
# Static binary; TARGETOS/TARGETARCH are set by buildx for multi-platform builds
ARG TARGETOS TARGETARCH
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} \
    go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server

# ---- Stage 2: run ----------------------------------------------------------
FROM scratch
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /out/server /server

# A numeric UID works on scratch without an /etc/passwd entry
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["/server"]
```

The owner's original version created a named user with `adduser` and copied
`/etc/passwd`; that works too. A numeric `USER 10001:10001` is simpler on `scratch` and
satisfies Kubernetes `runAsNonRoot`, which can only verify a *numeric* UID.

**When not to use `scratch`:** it has no shell, no libc and no CA bundle unless you copy
one in. For anything dynamically linked (Python, Node, Java, Go with cgo) use a *distroless*
image (`gcr.io/distroless/python3-debian12`, `…/java21-debian12`, `…/base-debian12`) or a
`-slim` Debian image. Alpine uses musl libc, which occasionally breaks prebuilt wheels
and changes DNS resolver behavior; prefer Debian-slim or distroless for Python.

### Example: a Python service

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /venv && /venv/bin/pip install -r requirements.txt

FROM base AS runtime
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=deps /venv /venv
COPY --chown=10001:10001 src/ ./src/
ENV PATH="/venv/bin:$PATH"
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD ["python", "-c", "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "src.main:app"]
```

`PYTHONUNBUFFERED=1` matters more than it looks: without it Python block-buffers stdout
when it is not a terminal, and logs appear in bursts or are lost when the container is
killed.

### `ENTRYPOINT`, `CMD`, and why PID 1 matters

| Form | Written as | What runs as PID 1 |
|---|---|---|
| exec form | `ENTRYPOINT ["/server", "--port", "8080"]` | `/server` itself |
| shell form | `ENTRYPOINT /server --port 8080` | `/bin/sh -c "/server --port 8080"` |

`docker stop` (and Kubernetes pod termination) sends **SIGTERM** to PID 1, waits a grace
period (10 s in Docker, 30 s by default in Kubernetes), then sends **SIGKILL**. With the
shell form, `sh` is PID 1 and does not forward SIGTERM to your app, so the app never
drains connections and is killed hard after the grace period: every deploy drops
in-flight requests and takes 10–30 s longer. Two more PID 1 quirks: the kernel does not
apply default signal handlers to PID 1 (a process that installs no SIGTERM handler
ignores it), and PID 1 must reap zombie children. Use the exec form, handle SIGTERM in
the app, and add a tiny init (`docker run --init`, or `tini` as the entrypoint) if the
app spawns children.

`ENTRYPOINT` is the executable; `CMD` supplies default arguments that `docker run image
<args>` replaces. A wrapper script entrypoint should end with `exec "$@"` so the real
process replaces the shell.

### Build-time secrets and arguments

`ARG` and `ENV` values are recorded in the image config and history. Never pass a token
that way. BuildKit secret mounts make the secret available to one `RUN` only, and it is
never written to a layer:

```dockerfile
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN="$(cat /run/secrets/npm_token)" npm ci
```

```bash
docker build --secret id=npm_token,env=NPM_TOKEN -t web:dev .
```

### Multi-platform builds

Apple-silicon laptops and Graviton/Axion servers are `arm64`; most CI runners are `amd64`.
An `amd64`-only image on an `arm64` node fails with `exec format error`.

```bash
docker buildx create --use --name multi
docker buildx build --platform linux/amd64,linux/arm64 \
  -t registry.example.com/shop-api:1.4.2 --push .
```

Cross-compiling in the build stage (Go with `GOARCH`, as above) is far faster than QEMU
emulation, which can be ≈ 5–20× slower for compile-heavy steps.

### Dockerfile checklist

| Rule | Why |
|---|---|
| Pin the base image (at least a minor version, ideally a digest in prod) | Reproducible builds |
| Dependency manifest before source | Cache reuse |
| `.dockerignore` with `.git`, `node_modules`, `.env*`, build output | Smaller context, no leaked secrets, stable cache |
| Multi-stage, minimal final stage | Size and attack surface |
| Exec-form `ENTRYPOINT`/`CMD`, handle SIGTERM | Graceful shutdown |
| Numeric non-root `USER` | Defense in depth; `runAsNonRoot` compatibility |
| No secrets in `ARG`/`ENV`/`COPY` | They persist in layers and history |
| One process per container | Restart, scale and log each concern independently |
| Logs to stdout/stderr | The runtime collects them; see chapter 06 |

## 4. Storage: the writable layer, volumes and bind mounts

Containers are ephemeral. `docker rm` deletes the writable layer and everything written
into it. To keep data, mount storage from outside the container:

| Type | Syntax | Managed by | Use for |
|---|---|---|---|
| Named volume | `-v pgdata:/var/lib/postgresql/data` or `--mount type=volume,src=pgdata,dst=…` | Docker (`/var/lib/docker/volumes/`) | Databases and app state on a single host |
| Bind mount | `-v "$PWD/src:/app/src"` or `--mount type=bind,…` | You (any host path) | Local development (live code reload), injecting config files |
| tmpfs | `--tmpfs /tmp:size=64m` | Kernel RAM | Scratch space, secrets that must never touch disk |

```bash
# Postgres with a named volume: data survives container removal and upgrades
docker volume create pgdata
docker run -d --name my-db \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/pg_pw \
  -v "$PWD/pg_pw.txt:/run/secrets/pg_pw:ro" \
  postgres:17
```

Failure modes you will meet:

- **Permission denied on a bind mount.** The container runs as UID 10001 but the host
  directory belongs to UID 1000. Match the UIDs, `chown` the directory, or use rootless
  Docker / user namespaces.
- **Slow bind mounts on macOS/Windows.** Docker Desktop shares files into its Linux VM;
  large `node_modules` trees are much slower through a bind mount than in a volume.
  Put dependencies in a named volume and bind-mount only the source.
- **Volume shadowing.** Mounting a volume over a directory hides whatever the image had
  there. A *new, empty* named volume is pre-populated from the image; a bind mount never is.
- **Disk full on the host.** `docker system df` shows image, container, volume and
  build-cache usage; `docker system prune` (add `--volumes` only if you mean it) and
  `docker builder prune` reclaim space. Log files of chatty containers are a common
  culprit: set `--log-opt max-size=10m --log-opt max-file=3` for the default `json-file`
  driver, or use the `local` driver, which rotates by default.

In Kubernetes the same ideas become PersistentVolumes and PersistentVolumeClaims
(chapter 02 §8).

## 5. Networking

### Network drivers

| Driver | What it gives you | Use for |
|---|---|---|
| `bridge` (default) | A private subnet on a Linux bridge (`docker0`), NAT to the outside | Single-host apps |
| user-defined bridge | Same, plus **DNS by container name** and isolation from other networks | Every multi-container setup (Compose creates one per project) |
| `host` | No network namespace; the container uses the host's interfaces | Max network performance, or tools that need the host's view |
| `none` | Only loopback | Batch jobs that must not touch the network |
| `macvlan` / `ipvlan` | The container gets an address on the physical LAN | Legacy apps that must look like a physical host |
| `overlay` | A VXLAN network across hosts | Docker Swarm (Kubernetes uses CNI plugins instead) |

### How `-p 8080:80` works

```arch
%% caption: A published port is a DNAT rule on the host that forwards to the container's private IP on the bridge.
grid 170x100
node client "Client" at 1,0 icon=browser sub="host-ip:8080"
group host "Docker host" color=purple icon=server
node nat "iptables DNAT" at 1,1 in host icon=firewall sub="8080 → 172.18.0.3:80"
node br "Bridge br-app" at 1,2 in host icon=network sub="172.18.0.0/16"
node web "web container" at 0,3 in host icon=container sub="172.18.0.3:80"
node db "db container" at 2,3 in host icon=db sub="172.18.0.2:5432"
node dns "Embedded DNS" at 0,2 in host icon=dns sub="127.0.0.11"
client -> nat -> br
br -> web : "veth"
br -> db : "veth"
web ..> dns : "resolve db"
```

Docker creates a veth pair per container, one end in the container's network namespace
as `eth0` and the other attached to the bridge. Publishing a port installs a DNAT rule in
the host's packet filter (iptables, or nftables in newer releases) that rewrites the
destination to the container's IP, and a masquerade rule so containers can reach the
internet through the host.

```bash
docker network create app-net
docker run -d --name db  --network app-net postgres:17
docker run -d --name web --network app-net -p 127.0.0.1:8080:80 my-web-image
# inside "web", the database is reachable as db:5432 via Docker's embedded DNS (127.0.0.11)
```

Things interviewers and incidents probe:

- **Default bridge has no name-based DNS.** Containers on the legacy `docker0` bridge can
  only reach each other by IP. Always create a network (Compose does this for you).
- **Published ports bypass host firewalls such as `ufw`.** Docker inserts its rules
  before the host's own chains, so `-p 5432:5432` exposes Postgres on every interface
  even if `ufw deny 5432` is set. Bind to loopback (`-p 127.0.0.1:5432:5432`) or
  don't publish internal services at all.
- **`localhost` inside a container is the container.** A container that calls
  `localhost:5432` is not reaching the host's database. Use the service name on a shared
  network, or `host.docker.internal` (built into Docker Desktop; on Linux add
  `--add-host=host.docker.internal:host-gateway`).
- **The app must listen on `0.0.0.0`,** not `127.0.0.1`, or traffic arriving on `eth0`
  never reaches it. This is the most common cause of "port is published but I get
  connection reset".
- **MTU mismatches** on VPNs or overlay networks cause large responses to hang while small
  ones work.

## 6. Docker Compose for local development

Compose describes a multi-container app in one YAML file and runs it with
`docker compose up`. Compose v2 is a Docker CLI plugin (`docker compose`, with a space);
the Python `docker-compose` v1 reached end of life in 2023. The top-level `version:` key
is obsolete and ignored by the current Compose Specification, so leave it out.

```yaml
# compose.yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      DB_URL: postgres://app:app@db:5432/shop
    depends_on:
      db:
        condition: service_healthy   # wait for the healthcheck, not just "container started"
    develop:
      watch:                          # `docker compose watch` syncs code without a rebuild
        - action: sync
          path: ./src
          target: /app/src
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: shop
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d shop"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```

**Precision note:** plain `depends_on: [db]` only orders *container start*; the API
can still start before Postgres accepts connections. Use `condition: service_healthy`
with a healthcheck, and make the app retry its first connection anyway, because in
production nothing guarantees start order.

Useful commands: `docker compose up -d --build`, `docker compose logs -f api`,
`docker compose exec db psql -U app shop`, `docker compose down` (add `-v` to delete
volumes), and profiles (`profiles: [debug]`) for optional services.

Compose is a local and single-host tool. For many hosts, failover and rolling updates,
you need an orchestrator: Kubernetes, chapter 02.

## 7. Running containers: limits, health, restarts and exit codes

```bash
# --memory-swap equal to --memory disables swap for the container
docker run -d --name api \
  --memory=512m --memory-swap=512m \
  --cpus=1.5 --pids-limit=256 \
  --restart=on-failure:5 \
  --read-only --tmpfs /tmp \
  --cap-drop=ALL --security-opt no-new-privileges \
  --log-opt max-size=10m --log-opt max-file=3 \
  -p 127.0.0.1:8080:8080 shop-api:1.4.2
```

**Language runtimes and limits.** Modern runtimes read cgroup limits: the JVM (since
10, backported to 8u191) sizes its heap from the container's memory limit, and Go 1.25+
sets `GOMAXPROCS` from the CPU limit. Older runtimes see the *host's* CPUs and RAM,
spawn too many threads and get throttled or OOM-killed. Set `GOMEMLIMIT` for Go, and
`-XX:MaxRAMPercentage=75` for Java, so the garbage collector works before the cgroup
kills the process.

**Exit codes to recognize on sight:**

| Code | Meaning | Usual cause |
|---|---|---|
| 0 | Clean exit | The main process finished (a web server should not) |
| 1 | Application error | Uncaught exception, bad config |
| 125 | Docker itself failed | Bad flag, daemon error |
| 126 | Command cannot be invoked | Entrypoint not executable |
| 127 | Command not found | Wrong path, or a shell script with CRLF line endings / missing interpreter |
| 137 | Killed by SIGKILL (128+9) | OOM kill (`docker inspect` shows `"OOMKilled": true`) or a stop that exceeded the grace period |
| 139 | SIGSEGV (128+11) | Native crash; often a musl/glibc mismatch |
| 143 | SIGTERM (128+15) | Normal `docker stop` of an app that exits on SIGTERM |

**Restart policies:** `no` (default), `on-failure[:N]`, `always`, `unless-stopped`.
A `HEALTHCHECK` only marks a container `unhealthy`; plain Docker does not restart it
for that (Swarm and Kubernetes probes do act on health).

## 8. Container security and the supply chain

A container is a weaker boundary than a VM, and an image is software you ship to
production with every one of its packages. Defense in depth:

| Layer | Practice |
|---|---|
| Image contents | Minimal base (distroless, `-slim`, Chainguard/Wolfi-style images); no shells or package managers in prod images when you can avoid them |
| Vulnerabilities | Scan in CI and in the registry: Trivy, Grype, Docker Scout. Fail on fixable criticals; rebuild often so base patches land |
| Provenance | Generate an SBOM (`docker buildx build --sbom=true`, Syft) and build provenance attestations (SLSA) |
| Signing | Sign images with Sigstore `cosign` (keyless via OIDC in CI) and verify at admission (Kyverno, Sigstore policy-controller, Connaisseur) |
| Runtime user | Non-root `USER`; rootless Docker or Podman; user namespaces |
| Privileges | `--cap-drop=ALL` then add back only what is needed; `no-new-privileges`; never `--privileged` in prod |
| Kernel surface | Docker's default seccomp profile blocks ≈ 40+ risky syscalls; AppArmor/SELinux profiles |
| Filesystem | `--read-only` root, writable `tmpfs` only where required |
| Host | Never mount `/var/run/docker.sock` into a container: that socket is root on the host |
| Strong isolation | gVisor (user-space kernel) or Kata Containers (lightweight VM per pod) for untrusted code |

Rootless containers: Podman runs rootless by default and has no daemon; Docker supports
a rootless mode. In both, "root" inside the container maps to your unprivileged UID
outside, so an escape lands as a normal user.

## 9. Debugging a container: a playbook

```bash
docker ps -a                                   # is it running, restarting, or exited (and with what code)?
docker logs --tail=200 -f <ctr>                # stdout/stderr
docker inspect <ctr> --format '{{.State.ExitCode}} {{.State.OOMKilled}} {{.RestartCount}}'
docker exec -it <ctr> sh                       # shell inside a running container (if the image has one)
docker stats                                   # live CPU, memory, network, block I/O per container
docker top <ctr>                               # processes inside, as the host sees them
docker events --since 10m                      # die, oom, kill, health_status events
docker run -it --entrypoint sh shop-api:1.4.2  # start a crashing image with a shell instead
docker cp <ctr>:/app/config.yaml .             # copy files out, works on stopped containers too
docker diff <ctr>                              # files changed in the writable layer
```

**No shell in the image (distroless / scratch)?** Debug from outside instead of adding
one:

```bash
PID=$(docker inspect -f '{{.State.Pid}}' <ctr>)
sudo nsenter -t "$PID" -n ss -ltnp            # host tools inside the container's network namespace
docker run -it --rm --pid=container:<ctr> --network=container:<ctr> \
  nicolaka/netshoot                           # a toolbox container sharing its namespaces
```

Kubernetes has the same idea built in: `kubectl debug -it <pod> --image=busybox
--target=<container>` adds an *ephemeral container* (chapter 02 §12).

**Symptom → cause table:**

| Symptom | Look at | Likely cause |
|---|---|---|
| Exits immediately with 0 | `docker logs`, the `CMD` | The main process finished: a backgrounded daemon (`nginx` without `daemon off`), or a script that returns |
| Exit 137, `OOMKilled: true` | `docker stats`, memory limit | Heap sized for the host, a leak, or the limit is simply too low |
| `exec format error` | `docker image inspect --format '{{.Architecture}}'` | Wrong CPU architecture (arm64 vs amd64) |
| `exec /entrypoint.sh: no such file or directory` although the file exists | `file entrypoint.sh` | CRLF line endings or a missing interpreter (`#!/bin/bash` on Alpine) |
| Port published, connection refused/reset | `ss -ltnp` inside | App bound to `127.0.0.1` instead of `0.0.0.0` |
| Slow shutdowns, dropped requests on deploy | `docker stop -t` timing | Shell-form entrypoint, SIGTERM not handled |
| Build re-downloads dependencies every time | `docker build --progress=plain` | Source copied before the dependency install; no `.dockerignore` |
| Image is 1.5 GB for a 20 MB app | `docker history`, `dive` | Full base image, build tools in the final stage, cleanup in a separate layer |

## 10. The wider container ecosystem (2026)

| Tool | What it is | When you meet it |
|---|---|---|
| Docker Engine / Docker Desktop | The daemon and CLI; Desktop bundles a Linux VM for macOS/Windows | Local development everywhere; Desktop needs a paid subscription for larger companies |
| Podman | Daemonless, rootless-by-default, Docker-compatible CLI | RHEL/Fedora hosts, rootless CI |
| containerd + nerdctl | The runtime Kubernetes uses; nerdctl is a Docker-like CLI for it | Kubernetes nodes, debugging a node |
| CRI-O | A Kubernetes-only CRI runtime | OpenShift |
| BuildKit / `docker buildx` | The build engine; also runs standalone in CI | Every modern Docker build |
| Buildah, ko, Jib, Cloud Native Buildpacks | Build images without a Dockerfile or without a daemon | Go (ko), Java (Jib), platform teams (Buildpacks) |
| Kaniko | Daemonless builds inside a Kubernetes pod | Legacy CI; Google archived the upstream repository in 2025, so new setups use BuildKit rootless or Buildah |
| Registries | Docker Hub (pull rate limits for anonymous users), GHCR, ECR, Artifact Registry, Harbor | Use a pull-through cache/mirror in CI to avoid rate limits |

## Common interview questions

**"What is a container, precisely? How is it different from a VM?"**
A container is a Linux process isolated with namespaces (pid, net, mnt, uts, ipc, user,
cgroup) and constrained with cgroups, running from an image's layered root filesystem, on
the host's shared kernel. A VM runs a full guest kernel on virtualized hardware. So
containers start in milliseconds and are megabytes, but share the kernel's attack
surface; VMs boot in seconds and isolate more strongly.

**"My build takes ten minutes every time I change one line of code."**
The dependency install sits after `COPY . .`, so any source change invalidates it. Copy
only the dependency manifest, install, then copy the source. Add a `.dockerignore` so
`.git` and build output don't bust the cache, and use BuildKit cache mounts for the
package manager's download cache.

**"My image is 1.5 GB but the app is 20 MB."**
A full OS or SDK base image, and build tools shipped to production. Use a multi-stage
build that copies only the artifact into distroless, `-slim` or `scratch`, and do
installs and cleanup in the same `RUN`. `docker history` / `dive` show which layer is big.

**"I deleted a secret file in a later `RUN`. Is it gone from the image?"**
No. Layers are additive; the delete is a whiteout, and the earlier layer still contains
the file (`docker save` and untar to see it). Use `RUN --mount=type=secret`, and rotate
the leaked secret.

**"The container gets exit code 137. What happened?"**
It received SIGKILL. Check `docker inspect` for `OOMKilled: true` (the cgroup memory
limit was hit) versus a stop that exceeded the grace period. Then look at heap sizing
versus the limit (`GOMEMLIMIT`, `MaxRAMPercentage`) and at leaks.

**"Why do our deploys drop requests and take 30 seconds per pod?"**
The app does not shut down on SIGTERM: typically a shell-form `ENTRYPOINT`/`CMD` (so `sh`
is PID 1 and swallows the signal) or no signal handler. Use exec form, handle SIGTERM by
draining, and add `--init`/`tini` if it spawns children.

**"CMD vs ENTRYPOINT?"**
`ENTRYPOINT` is the executable; `CMD` is its default arguments (or the default command
if there is no entrypoint). Arguments to `docker run image …` replace `CMD`; `--entrypoint`
replaces `ENTRYPOINT`.

**"Does Kubernetes still support Docker?"**
Kubernetes removed dockershim in 1.24, so nodes don't run dockerd; they run containerd or
CRI-O through the CRI. Docker-built images are OCI images and run unchanged.

**"How do you make an image build reproducible and trustworthy?"**
Pin base images by digest, lock dependencies, build in CI with BuildKit, produce an SBOM
and provenance, scan for vulnerabilities, sign with cosign, deploy by digest and verify
signatures at admission.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Can run `docker run`, `docker ps`, `docker logs`, use a Compose file someone else wrote, and explain image vs container |
| Junior (L3) | Software Engineer I / New grad | L3 | Writes a working Dockerfile with a sensible base, exposes ports, uses volumes and a user-defined network, reads logs and exit codes, knows the cache-ordering rule |
| Mid (L4) | Software Engineer II | L4 | Multi-stage builds, `.dockerignore`, non-root, exec-form entrypoints and SIGTERM handling, Compose with healthchecks, diagnoses OOMKilled/137, wrong-arch and bind-to-localhost bugs without help |
| Senior (L5) | Senior Software Engineer | L5 | Explains namespaces, cgroups, overlayfs copy-up and whiteouts and the dockerd → containerd → runc stack; tunes runtimes to cgroup limits; sets team standards for base images, scanning, SBOMs, signing, digests and multi-arch builds |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Owns the org's container platform and supply-chain policy (golden base images, patch cadence, admission verification, sandboxing for untrusted workloads), and weighs container vs VM vs sandbox isolation and build-system choices across the fleet |

## Interview checklist

- [ ] I can define a container as namespaces + cgroups + a layered root filesystem on a shared kernel, and contrast it with a VM.
- [ ] I can list the namespaces and say what each isolates, and name the cgroup controls for memory, CPU and PIDs.
- [ ] I can explain CPU throttling under a cgroup quota and why it hurts p99 latency.
- [ ] I can explain image layers, overlayfs copy-up and whiteouts, and why deleting a secret in a later layer does not remove it.
- [ ] I can explain the build cache rule and order a Dockerfile for maximum cache reuse.
- [ ] I can write a multi-stage Dockerfile with a non-root user and an exec-form entrypoint.
- [ ] I can explain PID 1 signal handling, `docker stop` and the grace period, and what `tini`/`--init` fixes.
- [ ] I know tag vs digest and why production deploys by digest.
- [ ] I can explain how a published port works and why `-p` bypasses `ufw`.
- [ ] I can read exit codes 0, 1, 125, 126, 127, 137, 139 and 143.
- [ ] I can debug a distroless container with `nsenter` or a namespace-sharing toolbox container.
- [ ] I can name the supply-chain controls: scanning, SBOM, provenance, cosign signing, admission verification.
- [ ] I know what dockershim's removal did and did not change for Kubernetes users.

Related: [Kubernetes and Orchestration](02_kubernetes_and_helm.md) (running containers across a fleet),
[Operating Systems & Hardware Symbiosis](../CSFundamentals/01_operating_systems_deep_dive.md) §6 (processes, namespaces, cgroups),
[Platform and Infrastructure](../SystemDesign/building_blocks/16_platform_and_infra.md) (containers vs VMs in design
interviews), [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) (building images in CI),
[Secret Management](11_secret_management.md) (keeping secrets out of images).
