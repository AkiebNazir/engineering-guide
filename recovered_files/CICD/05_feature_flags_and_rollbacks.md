# Feature Flags and Rollbacks

Deploying code and releasing a feature used to be the exact same event. If you deployed bad code, the only way to "un-release" it was to rollback the deployment (which takes time and is stressful).

Modern engineering decouples **Deploy** from **Release**.

## 1. Feature Flags (Toggles)

A feature flag is an `if` statement controlled by a remote server (like LaunchDarkly, Unleash, or a simple Redis key).

```python
def process_payment(order):
    if feature_flags.is_enabled("use_new_stripe_api", user_id=order.user_id):
        return stripe_v2.charge(order)
    else:
        return stripe_v1.charge(order)
```

### The Workflow
1. You deploy the new Stripe integration to production. The flag `use_new_stripe_api` is `false`. The code is *deployed*, but not *released*.
2. You turn the flag on for internal employees only.
3. You turn the flag on for 5% of users.
4. You monitor error rates.
5. You dial it up to 100%.
6. A month later, you delete the `else` block and the flag from the codebase to prevent technical debt.

### Instant Rollbacks
If the new Stripe integration starts failing at 50% rollout, you don't need to revert a Git commit, wait for CI to build a new Docker image, and wait for Kubernetes to do a rolling update. You click a button in the Feature Flag dashboard, and within milliseconds, all servers start executing the `else` block again.

## 2. Infrastructure Rollbacks

Not everything can be feature-flagged (like a framework upgrade, or a change to the Kubernetes Ingress config). When a deployment breaks the site, you must roll it back.

### Kubernetes Rollouts
If you are using a standard K8s Deployment, K8s keeps a history of the ReplicaSets.
```bash
# See the history of deployments
kubectl rollout history deployment/my-api

# Oh no, the site is down! Instantly revert to the previous ReplicaSet
kubectl rollout undo deployment/my-api
```

### Database Rollbacks (The Hard Part)
Rolling back code is easy. Rolling back data is incredibly dangerous.

Imagine:
1. v1 of the app writes `first_name` and `last_name` to the DB.
2. v2 of the app runs a migration to combine them into `full_name`, drops the old columns, and starts writing to `full_name`.
3. v2 has a critical bug! You roll back the code to v1.
4. **Disaster**: v1 boots up, tries to read `first_name`, but the column is gone. The app crashes.

**The Rule of Forward-Only Migrations:**
Never drop a column or rename a table in the same deployment that changes the code.
1. Deploy v1.5: Code writes to both old and new columns.
2. Run migration to backfill the new column.
3. Deploy v2: Code reads/writes *only* the new column. (At this point, if you rollback to v1.5, it still works).
4. Wait a week.
5. Deploy v3: Run migration to drop the old column.
