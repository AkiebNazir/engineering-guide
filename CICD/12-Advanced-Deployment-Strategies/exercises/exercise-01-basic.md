# Exercise 1: Recreate vs. Rolling Deployment Simulator 🟢

## 🎯 Objective
Simulate the difference in uptime between a recreate deployment and a rolling deployment using a simple Python script.

## 📋 Prerequisites
- Python 3.8+

## 📝 Instructions

1. Create a file named `deployment_simulator.py`.
2. Write a script that simulates a cluster of servers.
3. Implement a `recreate_deploy` function that shuts all down, waits, and starts all up.
4. Implement a `rolling_deploy` function that updates them one by one.

```python
import time

class Server:
    def __init__(self, id, version):
        self.id = id
        self.version = version
        self.status = "UP"

    def update(self, new_version):
        self.status = "DOWN"
        time.sleep(1) # Simulate update time
        self.version = new_version
        self.status = "UP"

def check_cluster_availability(cluster):
    up_count = sum(1 for s in cluster if s.status == "UP")
    print(f"Cluster availability: {up_count}/{len(cluster)} servers UP")
    return up_count > 0

def recreate_deploy(cluster, new_version):
    print("\n--- Starting Recreate Deployment ---")
    for s in cluster:
        s.status = "DOWN"
    
    check_cluster_availability(cluster)
    time.sleep(2)
    
    for s in cluster:
        s.version = new_version
        s.status = "UP"
    
    check_cluster_availability(cluster)

def rolling_deploy(cluster, new_version):
    print("\n--- Starting Rolling Deployment ---")
    for s in cluster:
        print(f"Updating Server {s.id}...")
        s.update(new_version)
        check_cluster_availability(cluster)

if __name__ == "__main__":
    cluster1 = [Server(1, "v1"), Server(2, "v1"), Server(3, "v1")]
    recreate_deploy(cluster1, "v2")

    cluster2 = [Server(1, "v1"), Server(2, "v1"), Server(3, "v1")]
    rolling_deploy(cluster2, "v2")
```

## ✅ Expected Output
```
--- Starting Recreate Deployment ---
Cluster availability: 0/3 servers UP
Cluster availability: 3/3 servers UP

--- Starting Rolling Deployment ---
Updating Server 1...
Cluster availability: 2/3 servers UP
Updating Server 2...
Cluster availability: 2/3 servers UP
Updating Server 3...
Cluster availability: 2/3 servers UP
```

## 🧠 Key Takeaway
Recreate deployments cause a total loss of availability (0/3 UP). Rolling deployments maintain partial availability throughout the deployment process.
