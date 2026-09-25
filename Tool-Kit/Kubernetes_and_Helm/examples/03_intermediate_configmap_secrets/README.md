# Intermediate: ConfigMaps & Secrets
**Goal:** Learn the 12-Factor App methodology by injecting configuration and sensitive secrets into your containers at runtime without hardcoding them.
**Key Concepts:** [ConfigMaps and Secrets](../Kubernetes_and_Helm.md#configmaps-and-secrets-configuration-management)
**Prerequisites:** A running Kubernetes cluster and `kubectl` installed.
**Step-by-Step Execution:** 
1. Create the ConfigMap, Secret, and the Deployment that consumes them:
   ```bash
   kubectl apply -f configmap.yaml -f secret.yaml -f deployment.yaml
   ```
2. Verify the resources were created:
   ```bash
   kubectl get configmaps
   kubectl get secrets
   kubectl get pods
   ```
3. Check the logs of the container to verify the injected environment variables and mounted files:
   ```bash
   kubectl logs -l app=config-test
   ```
   You should see `LOG_LEVEL`, `DB_USER`, `DB_PASS` and the contents of `app_settings.json`.
**Try it yourself:** 
1. Modify the `configmap.yaml` file to change the `LOG_LEVEL` to `info`.
2. Apply the change: `kubectl apply -f configmap.yaml`
3. Delete the running pod so a new one is spun up with the updated ConfigMap data:
   ```bash
   kubectl delete pod -l app=config-test
   ```
**Teardown:** 
```bash
kubectl delete -f deployment.yaml -f configmap.yaml -f secret.yaml
```
