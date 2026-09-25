import os
import re

base_dir = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Docker_Container"
md_file = os.path.join(base_dir, "Docker_Container.md")

with open(md_file, "r") as f:
    content = f.read()

# Replace diagrams
arch_to_mermaid = [
    (r"```arch\n%% caption: Virtual Machine vs Container Architecture.*?```", 
     """```mermaid\nflowchart TD\n    subgraph VM ["Virtual Machine Approach"]\n        hw1[Server Hardware] --> hyp[Hypervisor]\n        hyp --> vm1_os[Guest OS Ubuntu]\n        vm1_os --> vm1_app[App 1 + Libs]\n        hyp --> vm2_os[Guest OS Windows]\n        vm2_os --> vm2_app[App 2 + Libs]\n    end\n\n    subgraph Cont ["Container Approach"]\n        hw2[Server Hardware] --> hos[Host OS]\n        hos --> de[Docker Engine]\n        de --> c1[Container 1 App 1]\n        de --> c2[Container 2 App 2]\n    end\n```"""),
    
    (r"```arch\n%% caption: Docker Storage Types.*?```",
     """```mermaid\nflowchart TD\n    subgraph Host ["Host Machine OS"]\n        fs1[/"/path/to/my/project (Bind Mount)"/]\n        fs2[/"/var/lib/docker/... (Docker Volume)"/]\n        ram[/"Host RAM (tmpfs)"/]\n    end\n\n    subgraph Cont ["Docker Container"]\n        m1[/"/app/code"/]\n        m2[/"/var/lib/postgresql/data"/]\n        m3[/"/app/secrets"/]\n        app[Running Application]\n    end\n\n    fs1 <--> m1\n    fs2 <--> m2\n    ram <--> m3\n    m1 <--> app\n    m2 <--> app\n    m3 <--> app\n```"""),
    
    (r"```arch\n%% caption: Docker Default vs User-Defined Networks.*?```",
     """```mermaid\nflowchart TD\n    subgraph Host ["Host OS Network"]\n        eth0[Physical Interface eth0]\n    end\n\n    subgraph Bridge ["Default Bridge docker0"]\n        c1[Container 1 172.17.0.2]\n        c2[Container 2 172.17.0.3]\n    end\n\n    subgraph Custom ["User-Defined Bridge my-net"]\n        c3[Container: backend 172.18.0.2]\n        c4[Container: db 172.18.0.3]\n    end\n\n    eth0 --- c1\n    eth0 --- c2\n    eth0 --- c3\n    eth0 --- c4\n\n    c1 -. "No DNS" .- c2\n    c3 <-->|"Automatic DNS"| c4\n```"""),
     
    (r"```arch\n%% caption: Docker Compose Multi-Container Application.*?```",
     """```mermaid\nflowchart LR\n    user[User/Browser]\n    web[Web Service Flask/Node]\n    db[(Database Service PostgreSQL)]\n    vol[(Named Volume DB Data)]\n\n    user -->|"Port 5000"| web\n    web -->|"Queries"| db\n    db <-->|"Persists"| vol\n```"""),
     
    (r"```arch\n%% caption: Standard CI/CD Pipeline for Containers.*?```",
     """```mermaid\nflowchart TD\n    dev[Developer] -->|"git push"| gh[GitHub]\n    gh -->|"Triggers"| run[CI Runner]\n\n    subgraph CI ["Continuous Integration"]\n        run --> tst[Unit Tests]\n        tst -->|"Pass"| bld[docker build]\n        bld --> scn[Security Scan Trivy]\n    end\n\n    subgraph CD ["Continuous Deployment"]\n        psh[docker push]\n        reg[(Private Registry ECR)]\n        dep[Deployment ArgoCD]\n        k8s[Kubernetes Cluster]\n    end\n\n    alert[Alert Developer]\n\n    scn -->|"Pass"| psh\n    psh --> reg\n    reg -->|"GitOps"| dep\n    dep --> k8s\n\n    tst -->|"Fail"| alert\n    scn -->|"Fail"| alert\n```""")
]

for pat, repl in arch_to_mermaid:
    content = re.sub(pat, repl, content, flags=re.DOTALL)

# Add TOC
toc = """
## Interactive Examples

To help you bridge theory and practice, this guide includes interactive examples. 
There are two sets of examples:
- `examples/`: Focuses on interpreted languages (Python, Node.js) where containerization is straightforward.
- `examples_go/`: Focuses on compiled languages (Go), which introduces concepts like multi-stage builds to keep final images small and secure.

> [!TIP] Check out the [examples folder](examples) and [examples_go folder](examples_go) for hands-on applications of these concepts!

"""

content = re.sub(r"(## Introduction to Docker & Containerization\n)", r"\1" + toc, content)

# Add TIP callouts
content = re.sub(r"(### 3\. Example: Containerizing a Node\.js App)", 
                 r"> [!TIP] View a working Node.js example in [examples/02_basic_node_app](examples/02_basic_node_app)\n\n\1", content)
content = re.sub(r"(### 7\. Multi-Stage Builds \(Advanced but Essential\))", 
                 r"> [!TIP] View multi-stage build examples in [examples/03_intermediate_multi_stage](examples/03_intermediate_multi_stage) and [examples_go/03_intermediate_go_multistage](examples_go/03_intermediate_go_multistage)\n\n\1", content)
content = re.sub(r"(### 2\. The docker-compose\.yml File)", 
                 r"> [!TIP] View a full docker-compose example in [examples/04_intermediate_docker_compose](examples/04_intermediate_docker_compose)\n\n\1", content)
content = re.sub(r"(### 4\. Container Lifecycle Commands)", 
                 r"> [!TIP] Explore basic python app deployment in [examples/01_basic_python_app](examples/01_basic_python_app)\n\n\1", content)

with open(md_file, "w") as f:
    f.write(content)

print("Updated Docker_Container.md")

# Update READMEs
def rewrite_readme(example_dir):
    for root, dirs, files in os.walk(example_dir):
        if 'README.md' in files:
            dir_name = os.path.basename(root)
            readme_path = os.path.join(root, 'README.md')
            
            # Read files to understand
            goal = f"Demonstrate {dir_name.replace('_', ' ')}"
            
            content = f"""# {dir_name.replace('_', ' ').title()}

**Goal:** {goal}
**Key Concepts:** [Docker & Containerization Guide](../../Docker_Container.md)
**Prerequisites:** Docker installed
**Step-by-Step Execution:**
1. Navigate to this directory.
2. Build the image:
   ```bash
   docker build -t {dir_name.lower()} .
   ```
3. Run the container:
   ```bash
   docker run -p 8080:8080 {dir_name.lower()}
   ```
   *(Modify port if application uses a different port)*

**Try it yourself:** Modify the application code and rebuild the image to see the changes.

**Teardown:**
```bash
docker ps -a
docker rm -f <container_id>
```
"""
            # Refine if it has docker-compose
            if 'docker-compose.yml' in files:
                content = f"""# {dir_name.replace('_', ' ').title()}

**Goal:** {goal}
**Key Concepts:** [Docker & Containerization Guide](../../Docker_Container.md) - Docker Compose
**Prerequisites:** Docker and Docker Compose installed
**Step-by-Step Execution:**
1. Navigate to this directory.
2. Start the services:
   ```bash
   docker-compose up -d
   ```
3. View logs:
   ```bash
   docker-compose logs -f
   ```

**Try it yourself:** Add a new service to `docker-compose.yml` or scale an existing one.

**Teardown:**
```bash
docker-compose down
```
"""
            with open(readme_path, "w") as f:
                f.write(content)
            print(f"Updated {readme_path}")

rewrite_readme(os.path.join(base_dir, "examples"))
rewrite_readme(os.path.join(base_dir, "examples_go"))

