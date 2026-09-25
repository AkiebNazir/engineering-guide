# Exercise 5: Zero-Downtime Blue/Green Deployment Simulation 🔵🟢

## 🎯 Objective
Simulate a Blue/Green deployment using Python. You will script a system that switches traffic via an Nginx-like reverse proxy configuration file from the old environment (Blue) to the new environment (Green).

## 📋 Prerequisites
- Python 3 installed
- Basic understanding of reverse proxies/load balancers

## 📝 Instructions
1. Create a Python script `blue_green_deploy.py`.
2. Assume two instances of your app are running locally on different ports (e.g., Blue on 8081, Green on 8082).
3. The "load balancer" configuration is just a JSON file `router.json` that looks like `{"active_port": 8081}`.
4. Your script needs to:
   - Read the current active port.
   - Determine which environment is inactive (the target for the new deployment).
   - "Deploy" to the inactive environment.
   - Run a smoke test on the newly deployed environment.
   - If the test passes, update `router.json` to point traffic to the new environment.
   - If it fails, do nothing (leave traffic pointing to the old environment).

## 💡 Hints
- Use the `json` module to read/write `router.json`.
- Treat a simple function returning True/False as your smoke test.

## ✅ Expected Output / Solution

```python
# blue_green_deploy.py
import json
import os
import random

ROUTER_FILE = "router.json"
BLUE_PORT = 8081
GREEN_PORT = 8082

def init_router():
    if not os.path.exists(ROUTER_FILE):
        with open(ROUTER_FILE, "w") as f:
            json.dump({"active_port": BLUE_PORT}, f)

def read_active_port():
    with open(ROUTER_FILE, "r") as f:
        config = json.load(f)
        return config.get("active_port")

def update_router(new_port):
    with open(ROUTER_FILE, "w") as f:
        json.dump({"active_port": new_port}, f)
    print(f"🔄 Traffic successfully routed to port {new_port}")

def deploy_to_env(port):
    print(f"📦 Deploying new code to background environment on port {port}...")
    # Simulate deployment time
    return True

def smoke_test(port):
    print(f"💨 Running smoke test on port {port}...")
    # Simulate a 20% failure rate
    success = random.random() > 0.2
    if success:
        print("✅ Smoke test passed!")
    else:
        print("❌ Smoke test failed!")
    return success

def run_pipeline():
    init_router()
    active_port = read_active_port()
    
    # Determine target environment
    target_port = GREEN_PORT if active_port == BLUE_PORT else BLUE_PORT
    active_env_name = "Blue" if active_port == BLUE_PORT else "Green"
    target_env_name = "Green" if active_port == BLUE_PORT else "Blue"
    
    print(f"Current Live Environment: {active_env_name} ({active_port})")
    print(f"Targeting Deployment to: {target_env_name} ({target_port})")
    print("-" * 40)
    
    # Deploy to inactive environment
    deploy_to_env(target_port)
    
    # Test the new deployment safely without affecting users
    if smoke_test(target_port):
        print("🎉 Flipping the switch!")
        update_router(target_port)
    else:
        print(f"⚠️ Deployment aborted. Live traffic remains on {active_env_name} ({active_port}).")

if __name__ == "__main__":
    run_pipeline()
```

## 🧠 Key Takeaway
Blue/Green deployments eliminate downtime and reduce risk. By deploying to an identical, idle environment, you can test production configurations safely. If something goes wrong, you haven't touched the live user traffic. If it succeeds, the switch is nearly instantaneous.
