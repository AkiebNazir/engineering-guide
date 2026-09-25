# Exercise 3: Blue/Green Router Simulator 🟡

## 🎯 Objective
Build a load balancer simulator in Python that routes traffic between a Blue environment and a Green environment, demonstrating instant switchovers and rollbacks.

## 📋 Prerequisites
- Python 3.8+

## 📝 Instructions

1. Create a script named `blue_green.py`.
2. Define a Router class that manages traffic state.
3. Simulate user requests before, during, and after a switch.

```python
import random

class Router:
    def __init__(self):
        self.active_env = "BLUE"
        self.environments = {
            "BLUE": "v1.0 (Stable)",
            "GREEN": "v2.0 (New Release)"
        }

    def route_request(self, user_id):
        version = self.environments[self.active_env]
        print(f"User {user_id} routed to {self.active_env} env running {version}")

    def switch_traffic(self, target_env):
        if target_env in self.environments:
            print(f"\n[!] Switching all traffic to {target_env} environment...\n")
            self.active_env = target_env
        else:
            print("Invalid environment.")

def simulate_traffic(router, num_requests):
    for i in range(num_requests):
        router.route_request(f"U-{random.randint(100, 999)}")

if __name__ == "__main__":
    router = Router()
    
    print("--- Normal Traffic ---")
    simulate_traffic(router, 3)
    
    print("\n--- Deploying v2 to GREEN (Idle) ---")
    print("Running tests on GREEN... Tests passed.")
    
    # The Cutover
    router.switch_traffic("GREEN")
    simulate_traffic(router, 2)
    
    print("\n--- Oh no! Critical Bug Detected! ---")
    print("Initiating instant rollback...")
    
    # The Rollback
    router.switch_traffic("BLUE")
    simulate_traffic(router, 2)
```

## ✅ Expected Output
```
--- Normal Traffic ---
User U-543 routed to BLUE env running v1.0 (Stable)
User U-128 routed to BLUE env running v1.0 (Stable)
...

--- Deploying v2 to GREEN (Idle) ---
Running tests on GREEN... Tests passed.

[!] Switching all traffic to GREEN environment...

User U-999 routed to GREEN env running v2.0 (New Release)
...

--- Oh no! Critical Bug Detected! ---
Initiating instant rollback...

[!] Switching all traffic to BLUE environment...

User U-456 routed to BLUE env running v1.0 (Stable)
```

## 🧠 Key Takeaway
Blue/Green deployments require zero time to rollback. It is a simple configuration change at the router level, eliminating the need to re-deploy old code.
