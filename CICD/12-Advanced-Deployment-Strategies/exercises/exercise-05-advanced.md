# Exercise 5: Canary Release Traffic Splitter 🔴

## 🎯 Objective
Build a sophisticated routing mechanism in Python that implements a Canary release. It will route a specific percentage of traffic to the new version based on weights.

## 📋 Prerequisites
- Python 3.8+

## 📝 Instructions

1. Create a file `canary_router.py`.
2. Implement a weighted random choice algorithm to direct traffic.
3. Simulate 100 requests.
4. Calculate and print the actual distribution to prove the canary percentage is accurate.

```python
import random
from collections import Counter

class CanaryRouter:
    def __init__(self, stable_weight=90, canary_weight=10):
        self.routes = {
            "v1_stable": stable_weight,
            "v2_canary": canary_weight
        }
        
    def set_weights(self, stable, canary):
        self.routes["v1_stable"] = stable
        self.routes["v2_canary"] = canary
        print(f"\n[Config] Weights updated: Stable={stable}%, Canary={canary}%")

    def route_request(self):
        targets = list(self.routes.keys())
        weights = list(self.routes.values())
        
        # random.choices picks elements based on relative weights
        selected = random.choices(targets, weights=weights, k=1)[0]
        return selected

def run_simulation(router, num_requests):
    results = []
    for _ in range(num_requests):
        results.append(router.route_request())
        
    counts = Counter(results)
    print(f"Simulation Results ({num_requests} reqs):")
    for version, count in counts.items():
        percentage = (count / num_requests) * 100
        print(f"  {version}: {count} requests ({percentage:.1f}%)")

if __name__ == "__main__":
    # Start with a 10% canary
    router = CanaryRouter(90, 10)
    print("--- Phase 1: 10% Canary ---")
    run_simulation(router, 1000)
    
    # Ramp up to 50%
    router.set_weights(50, 50)
    print("--- Phase 2: 50% Rollout ---")
    run_simulation(router, 1000)
    
    # Full release
    router.set_weights(0, 100)
    print("--- Phase 3: Full Release ---")
    run_simulation(router, 100)
```

## 💡 Hints
- The `random.choices` function in Python is perfect for weighted random routing.

## ✅ Expected Output
```
--- Phase 1: 10% Canary ---
Simulation Results (1000 reqs):
  v1_stable: 902 requests (90.2%)
  v2_canary: 98 requests (9.8%)

[Config] Weights updated: Stable=50%, Canary=50%
--- Phase 2: 50% Rollout ---
Simulation Results (1000 reqs):
  v2_canary: 492 requests (49.2%)
  v1_stable: 508 requests (50.8%)

[Config] Weights updated: Stable=0%, Canary=100%
--- Phase 3: Full Release ---
Simulation Results (100 reqs):
  v2_canary: 100 requests (100.0%)
```
*(Your exact numbers will vary slightly due to randomness, but should be close to the target percentages).*

## 🧠 Key Takeaway
Canary deployments limit blast radius. If v2_canary had a critical bug during Phase 1, only ~10% of users would experience it, giving you time to analyze metrics and rollback if necessary.
