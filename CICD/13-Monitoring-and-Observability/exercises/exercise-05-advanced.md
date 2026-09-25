# Exercise 5: Monitoring-Driven Automated Rollback ⏪

## 🎯 Objective
Simulate a deployment pipeline that monitors application health post-deployment and triggers an automatic rollback if error rates exceed a threshold.

## 📋 Prerequisites
- Python 3.9+

## 📝 Instructions

In advanced CD (like ArgoCD or Spinnaker), an automated canary analysis occurs after a deployment. If the new version throws too many errors, the pipeline automatically aborts and rolls back. We will build a script that mimics this logic.

### Step 1: Create the Simulated Rollback Script
Create a file named `deployment_verifier.py`.

```python
import time
import random
import sys

def fetch_error_rate_from_monitoring():
    """
    Simulates querying Prometheus or Datadog for the error rate
    of the newly deployed version.
    """
    # Simulate a bad deployment (error rate spikes over time)
    # 0.01 = 1%, 0.10 = 10%
    base_error = 0.01 
    spike = random.uniform(0.0, 0.15)
    return base_error + spike

def rollback():
    print("🚨 INITIATING AUTOMATED ROLLBACK...")
    print("Executing rollback commands (e.g., git revert, helm rollback)...")
    time.sleep(2)
    print("✅ Rollback successful. System restored to previous stable state.")

def verify_deployment(duration_seconds=30, check_interval=5, threshold=0.08):
    print("🚀 Deployment finished. Starting automated metric verification...")
    
    end_time = time.time() + duration_seconds
    
    while time.time() < end_time:
        error_rate = fetch_error_rate_from_monitoring()
        print(f"[{time.strftime('%H:%M:%S')}] Current error rate: {error_rate:.2%}")
        
        if error_rate > threshold:
            print(f"❌ ERROR RATE THRESHOLD EXCEEDED ({error_rate:.2%} > {threshold:.2%})")
            rollback()
            sys.exit(1) # Fail the CI/CD pipeline step
            
        time.sleep(check_interval)
        
    print("🎉 Verification complete. Deployment is stable.")
    sys.exit(0)

if __name__ == "__main__":
    verify_deployment()
```

### Step 2: Run the Simulation
Run the script multiple times: `python deployment_verifier.py`
Because of the random simulation, sometimes it will succeed, and sometimes it will trigger the rollback.

## 💡 Hints
- The threshold is set to 8% (`0.08`). 
- In a real system, you would query an actual Prometheus endpoint (e.g., `rate(http_requests_total{status="500", version="v2"}[1m])`).

## ✅ Expected Output / Solution
**Failed Deployment:**
```text
🚀 Deployment finished. Starting automated metric verification...
[12:30:00] Current error rate: 5.20%
[12:30:05] Current error rate: 2.10%
[12:30:10] Current error rate: 11.40%
❌ ERROR RATE THRESHOLD EXCEEDED (11.40% > 8.00%)
🚨 INITIATING AUTOMATED ROLLBACK...
Executing rollback commands (e.g., git revert, helm rollback)...
✅ Rollback successful. System restored to previous stable state.
```

## 🧠 Key Takeaway
By shifting observability left into the deployment pipeline, you create self-healing deployments that protect end-users from bad code releases automatically, without manual intervention.
