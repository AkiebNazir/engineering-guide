# Continuous Deployment (CD) and Delivery

If CI is about *testing* the code automatically, CD is about *shipping* the code automatically.

## Continuous Delivery vs. Continuous Deployment

- **Continuous Delivery**: The code is always in a deployable state. The CI pipeline builds the Docker image and pushes it to the registry. But a human must manually click a "Deploy" button to push it to production.
- **Continuous Deployment**: Every commit that passes the CI pipeline is automatically deployed to production with zero human intervention.

Continuous Deployment requires immense trust in your automated test suite and robust rollback mechanisms.

## The CD Pipeline

```arch
%% caption: The CD pipeline takes the artifact produced by CI and orchestrates its rollout across environments.
route straight
node reg "Docker Registry\n(Image: v1.2)" at 0,0 icon=db color=blue
node cd "CD Tool\n(Spinnaker / Jenkins)" at 2,0 icon=package color=amber
node stg "Staging Env\n(Automated E2E)" at 0,1 icon=cloud color=slate
node prod "Production Env\n(Canary / Rollout)" at 2,1 icon=cloud color=green

reg -> cd : "Webhook\ntrigger"
cd -> stg : "Deploys & tests"
stg -> prod : "If pass,\npromote"
```

## Immutable Artifacts

A critical rule of CD: **Build once, deploy many times.**

*Bad*:
1. Push to `main`.
2. CI pulls code, builds image, runs tests, pushes image to staging.
3. Tests pass in staging.
4. CI pulls code *again*, builds image *again*, pushes to prod.
(What if a dependency changed in between step 2 and 4? You are deploying untested code to prod).

*Good*:
1. Push to `main`.
2. CI pulls code, builds image with a specific hash (e.g., `myapp:a1b2c3d`), runs tests.
3. CD deploys `myapp:a1b2c3d` to staging.
4. Tests pass.
5. CD deploys the *exact same* `myapp:a1b2c3d` image to production.

## Configuration Injection

Because you are using the exact same Docker image in Staging and Production, the image itself cannot contain the database passwords.

The CD tool (or Kubernetes) must inject the environment variables (`DB_HOST=staging-db` vs `DB_HOST=prod-db`) at runtime when the container starts.
