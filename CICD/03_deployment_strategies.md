# Deployment Strategies

"Deploying" by stopping the server, copying the new binary, and starting it again results in downtime. Modern backend systems require zero-downtime deployments.

## 1. Rolling Deployment (The Default)

Instead of replacing all servers at once, replace them one by one. Kubernetes does this by default with Deployments.

1. App v1 is running on 3 instances.
2. Spin up 1 instance of App v2.
3. Wait for it to become healthy (readiness probe passes).
4. Route traffic to it.
5. Kill 1 instance of App v1.
6. Repeat until all instances are v2.

**Pros**: Zero downtime, cheap (only requires +1 instance capacity).
**Cons**: Rollbacks are slow (you have to roll *backward* one by one). Both v1 and v2 are running simultaneously, so your database schema MUST be backwards compatible.

## 2. Blue/Green Deployment

You run two identical production environments: "Blue" (currently active) and "Green" (idle).

1. Blue is serving 100% of production traffic running v1.
2. Deploy v2 to the Green environment.
3. Run smoke tests against Green.
4. Flip the load balancer to route 100% of traffic to Green instantly.
5. Blue becomes the new idle environment.

```arch
%% caption: Blue/Green allows instantaneous cutover and instantaneous rollback by simply flipping the Load Balancer.
route straight
node lb "Load Balancer" at 2,0 icon=lb color=amber
group blue "Blue Env (v1)" color=slate style=dashed
node b1 "App v1" at 0,1 in blue icon=app color=slate
group green "Green Env (v2)" color=slate style=dashed
node g1 "App v2" at 4,1 in green icon=app color=green

lb -> b1 : "0% traffic\\n(idle)"
lb -> g1 : "100% traffic\\n(active)"
```

**Pros**: Instant rollback (just flip the load balancer back to Blue).
**Cons**: Expensive (requires 2x the infrastructure).

## 3. Canary Release

You route a tiny percentage of real user traffic to the new version to see if it crashes before rolling it out to everyone.

1. Deploy v2 to a small subset of servers (the "canary").
2. Route 5% of production traffic to the canary.
3. Monitor the canary's error rate and latency (the RED metrics).
4. If errors spike, automatically route traffic away and kill the canary.
5. If errors are normal, slowly increase traffic to 10%, 50%, then 100%.

**Pros**: Safest way to deploy. Real users test the code, but the blast radius is tiny if it fails.
**Cons**: Requires advanced load balancers (like Envoy/Istio) and automated observability tools to analyze the canary's health.

## 4. Shadow Traffic (Dark Launching)

You want to test v2 with real production data, but you don't want any users to actually see v2's responses yet.

The Load Balancer sends the HTTP request to v1 (which returns the response to the user), but it *also* asynchronously duplicates the exact same HTTP request and sends it to v2. The Load Balancer throws away v2's response. You just monitor v2 to see if it crashed under the real load.

**Pros**: Zero risk to users.
**Cons**: Only works for read-heavy or idempotent operations. If the request is a `POST /purchase`, you cannot shadow it, or you will charge the user's credit card twice!
