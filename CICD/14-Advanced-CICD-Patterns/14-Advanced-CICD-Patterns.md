# Chapter 14: Advanced CI/CD Patterns

## 🎯 Learning Objectives
By the end of this chapter, you will be able to:
- Understand and implement GitOps principles using Kubernetes manifests.
- Master Trunk-Based Development and monorepo CI/CD strategies.
- Design reusable workflows and dynamically generated pipelines.
- Implement ephemeral environments and self-healing CI/CD patterns.
- Extend CI/CD practices to MLOps and event-driven architectures.

## 📖 Introduction
Imagine running a massive logistics hub where millions of packages (code commits) arrive daily. Traditional sorting mechanisms work for small scale, but as the volume explodes, you need automated routing, intelligent self-healing belts, and real-time tracking. Advanced CI/CD patterns are the "next-gen logistics" for your software delivery. By treating everything as code—including the deployment state (GitOps) and the pipelines themselves—you create resilient, highly automated, and scalable delivery networks.

## 🔑 Key Terminology
| Term | Definition |
|------|------------|
| **GitOps** | An operational framework that takes DevOps practices used for application development (like version control and CI/CD) and applies them to infrastructure automation. |
| **Trunk-Based Dev** | A branching model where developers merge small, frequent updates into a core "trunk" or main branch. |
| **Monorepo** | A software development strategy where code for many projects is stored in the same repository. |
| **ChatOps** | The use of chat clients, chatbots, and real-time communication tools to execute software deployment and operational tasks. |
| **Ephemeral Env** | Temporary, isolated environments spun up for a specific pull request or feature branch, and destroyed afterward. |

## 🔄 GitOps vs Traditional CI/CD

In traditional CI/CD, the CI server is god. It builds, tests, and *pushes* changes directly to production servers. In GitOps, an agent inside the cluster *pulls* changes from a Git repository, ensuring the system state matches the declared state in Git.

```arch
node a "Git Repo" at 0,0 icon=doc color=slate
node b "CI/CD Server" at 1,0 icon=server color=blue
node c "Prod Cluster" at 2,0 icon=gateway color=purple
a -> b -> c
node d "Git Repo" at 0,1 icon=doc color=slate
node e "CI Server (Build/Push)" at 1,1 icon=server color=blue
node f "Config Repo" at 2,1 icon=doc color=amber
node g "GitOps Agent (ArgoCD)" at 2,2 icon=process color=teal
d -> e -> f
g -> f : "Pulls Config"
```

### GitOps Example: Kubernetes Manifest
Here is a standard deployment manifest that a GitOps controller would sync:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myregistry.com/api:v1.4.2
        ports:
        - containerPort: 8080
```

## 🌳 Trunk-Based Development & Monorepos

### Trunk-Based Development
Instead of long-lived feature branches, developers merge to `main` daily. This requires rigorous automated testing and feature flags.

### Monorepo CI/CD Challenges
In a monorepo, a single commit might touch only one of fifty microservices. Running the entire test suite would take hours. The solution is **path-based triggering** and **dependency graph analysis**.

```yaml
# Example CI Config for Monorepo
name: Monorepo CI
on:
  push:
    paths:
      - 'services/auth/**'
      - 'shared/libs/**'

jobs:
  build-auth:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building Auth Service"
```

## ⚙️ Advanced Pipeline Patterns

### Dynamic Pipelines in Python
Sometimes static YAML isn't enough. You can write scripts that dynamically generate pipeline configurations based on the repository state.

```python
# generate_pipeline.py
import os
import json

def generate_pipeline():
    services = [d for d in os.listdir('./services') if os.path.isdir(f'./services/{d}')]
    pipeline = {
        "name": "Dynamic CI",
        "jobs": {}
    }
    
    for service in services:
        pipeline["jobs"][f"build-{service}"] = {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"name": "Checkout", "uses": "actions/checkout@v3"},
                {"name": f"Test {service}", "run": f"cd services/{service} && make test"}
            ]
        }
    
    with open('dynamic-pipeline.json', 'w') as f:
        json.dump(pipeline, f, indent=2)
    print(f"Generated pipeline for {len(services)} services.")

if __name__ == "__main__":
    generate_pipeline()
```

### Pipeline Orchestration: Fan-Out / Fan-In
```arch
node a "Code Push" at 1,0 icon=user color=slate
node b "Lint" at 1,1 shape=card color=amber
a -> b
node c "Unit Test (Fan-Out)" at 0,2 shape=card color=green
node d "Integration Test" at 1,2 shape=card color=green
node e "Security Scan" at 2,2 shape=card color=green
b -> c
b -> d
b -> e
node f "Build Artifact (Fan-In)" at 1,3 icon=doc color=purple
c -> f
d -> f
e -> f
node g "Deploy to Staging" at 1,4 icon=gateway color=teal
f -> g
```

## 🌩️ Ephemeral Environments & ChatOps

### Ephemeral Environments
Triggered on a Pull Request, the pipeline spins up a lightweight namespace in Kubernetes, deploys the app, and posts the URL back to the PR as a comment.

### ChatOps
Triggering deployments from Slack.

```go
// chatops_handler.go
package main

import (
	"fmt"
	"net/http"
	"strings"
)

func slackCommandHandler(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()
	text := r.FormValue("text")
	
	if strings.HasPrefix(text, "deploy") {
		parts := strings.Split(text, " ")
		if len(parts) >= 2 {
			service := parts[1]
			fmt.Fprintf(w, "🚀 Triggering deployment for %s...", service)
			// Trigger API call to CI/CD server
			return
		}
	}
	fmt.Fprintf(w, "Unknown command. Try: /ops deploy <service>")
}

func main() {
	http.HandleFunc("/slack/command", slackCommandHandler)
	http.ListenAndServe(":8080", nil)
}
```

## 💡 Best Practices
- **Do** treat your pipeline configurations as code. Code review them like any other software.
- **Do** isolate state changes. Use Git as the single source of truth for environments.
- **Don't** build massive, monolithic pipelines. Use reusable modules.
- **Don't** allow manual intervention in the middle of a continuous delivery pipeline.

## 🔗 How This Connects
- **Previous:** Chapter 13 covered Monitoring and Observability, which are critical for self-healing pipelines.
- **Next:** Chapter 15 scales these patterns up in "CI/CD at Scale".

## 📝 Chapter Summary
| Concept | Key Benefit |
|---------|-------------|
| **GitOps** | Immutable, versioned infrastructure and deployments. |
| **Dynamic Pipelines** | Adapts to monorepo structure without manual YAML duplication. |
| **Ephemeral Env** | End-to-end testing of features before merging. |

## ➡️ What's Next
Dive into the exercises to implement a dynamic pipeline, set up a ChatOps webhook, and mock a GitOps deployment workflow!
