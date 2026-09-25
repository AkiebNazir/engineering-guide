# Exercise 5: Enterprise CI/CD Golden Path Migration 🔴

## 🎯 Objective
Simulate the Platform Engineering process of analyzing a messy, custom pipeline and refactoring it to use a Golden Path template, calculating the cost and time savings.

## 📋 Prerequisites
- Strong understanding of CI/CD concepts.
- Familiarity with CI/CD optimization.

## 📝 Instructions

You are a Platform Engineer. A team is complaining their build takes 25 minutes and costs too much.

Their current `custom-pipeline.yml`:
```yaml
jobs:
  build:
    runs-on: heavy-expensive-runner
    steps:
      - uses: actions/checkout@v3
      - run: sleep 300 # Waiting for DB to spin up manually
      - run: apt-get update && apt-get install -y python3 python3-pip
      - run: pip install -r requirements.txt # No caching
      - run: pytest tests/ # Runs 5000 E2E tests sequentially
      - run: docker build -t app:latest .
```

**Task 1:** Write a Python script `analyze_savings.py` that calculates the cost difference between the old way and the optimized Golden Path way.
- Old Pipeline: 25 mins * $0.016/min (heavy runner) * 100 runs/day
- New Pipeline (Golden path with caching and parallelism): 5 mins * $0.008/min (standard runner) * 100 runs/day

**Task 2:** Write the script to output the Monthly (30 day) savings.

```python
# analyze_savings.py
def calculate_cost(minutes, cost_per_min, runs_per_day, days):
    return minutes * cost_per_min * runs_per_day * days

old_cost = calculate_cost(25, 0.016, 100, 30)
new_cost = calculate_cost(5, 0.008, 100, 30)
savings = old_cost - new_cost

print(f"Old Monthly Cost: ${old_cost:.2f}")
print(f"New Monthly Cost: ${new_cost:.2f}")
print(f"Total Monthly Savings: ${savings:.2f}")
print(f"Developer Time Saved (Hours/Month): {((25-5)*100*30)/60} hrs")
```

## 💡 Hints
- Golden Paths aren't just about standardizing code; they enforce best practices like caching, correct runner sizing, and avoiding sleep commands.
- Enterprise scale means small inefficiencies compound massively. 20 minutes saved * 100 runs * 30 days is 1,000 hours of waiting time eliminated per month!

## ✅ Expected Output / Solution
```
Old Monthly Cost: $1200.00
New Monthly Cost: $120.00
Total Monthly Savings: $1080.00
Developer Time Saved (Hours/Month): 1000.0 hrs
```

## 🧠 Key Takeaway
Platform Engineering is highly quantifiable. By providing optimized Golden Paths, you reduce infrastructure costs significantly while simultaneously giving thousands of hours of productivity back to the engineering organization.
