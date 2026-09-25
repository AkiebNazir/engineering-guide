# Chapter 14: Advanced CI/CD Patterns

<Exercise 5: GitOps Auto-Rollback Simulator 🔴>
## 🎯 Objective
Simulate a GitOps continuous deployment loop in Python that checks application health and automatically rolls back the version if a failure is detected.

## 📋 Prerequisites
- Python 3.x

## 📝 Instructions
1. Create a script simulating a GitOps agent.
2. It tracks the "desired state" (version in a mock config file) and "actual state" (mock cluster).
3. If it updates the cluster and a health check fails, it automatically reverts to the previous version.

## 💡 Hints
- Use simple variables to represent state. Implement a `sync()` function and a `health_check()` function.

## ✅ Expected Output / Solution
```python
import time

class GitOpsAgent:
    def __init__(self):
        self.cluster_version = "v1.0.0"
        self.desired_version = "v1.0.0"
        self.history = ["v1.0.0"]

    def sync(self, new_version):
        print(f"[Agent] Syncing desired state: {new_version}...")
        self.desired_version = new_version
        self.deploy(new_version)
        
        if not self.health_check():
            print("[Agent] ❌ Health check failed! Initiating auto-rollback...")
            self.rollback()
        else:
            print("[Agent] ✅ Deployment healthy.")
            self.history.append(new_version)

    def deploy(self, version):
        print(f"[Cluster] Deploying {version}...")
        time.sleep(1)
        self.cluster_version = version

    def health_check(self):
        # Simulate a bug in v2.0.0
        if self.cluster_version == "v2.0.0":
            return False
        return True

    def rollback(self):
        last_good_version = self.history[-1]
        print(f"[Agent] Rolling back to {last_good_version}")
        self.deploy(last_good_version)
        self.desired_version = last_good_version
        print(f"[Agent] Rollback complete. Current version: {self.cluster_version}")

if __name__ == "__main__":
    agent = GitOpsAgent()
    print(f"Initial State: {agent.cluster_version}")
    
    # Try deploying a good version
    agent.sync("v1.1.0")
    print("-" * 30)
    
    # Try deploying a bad version
    agent.sync("v2.0.0")
```

## 🧠 Key Takeaway
GitOps combined with automated observability enables highly resilient self-healing pipelines, ensuring bad code doesn't stay in production long.
</Exercise 5: GitOps Auto-Rollback Simulator 🔴>
