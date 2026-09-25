# Exercise 04: Build and Push with GitHub Actions 🐙🐳

## 🎯 Objective
Write a GitHub Actions workflow that builds a Docker image and pushes it to GitHub Container Registry (GHCR) only when code is pushed to the `main` branch.

## 📋 Prerequisites
- Basic GitHub Actions YAML syntax.
- Understanding of Docker registries and tagging.

## 📝 Instructions

1. Create a workflow file `.github/workflows/docker.yml`.
2. Name it "Docker CI".
3. Trigger it on `push` to the `main` branch.
4. Create a job called `build-push`.
5. Set `runs-on: ubuntu-latest`.
6. Add permissions for `packages: write` and `contents: read`.
7. Add steps to:
   - Checkout code using `actions/checkout@v4`.
   - Log in to GHCR (`ghcr.io`) using `docker/login-action@v3`. Use `${{ github.actor }}` for username and `${{ secrets.GITHUB_TOKEN }}` for password.
   - Extract metadata/tags using `docker/metadata-action@v5` for the image `ghcr.io/${{ github.repository }}`.
   - Build and push the image using `docker/build-push-action@v5`. Set `context: .`, `push: true`, and pass the tags and labels from the metadata step.

## 💡 Hints
- The `GITHUB_TOKEN` is automatically provided by GitHub Actions and can be used to authenticate with GHCR if `packages: write` permission is granted.
- The `metadata-action` automatically generates tags like `main`, `latest`, or semantic versions based on the trigger event.

## ✅ Expected Output / Solution

```yaml
name: Docker CI

on:
  push:
    branches:
      - main

jobs:
  build-push:
    runs-on: ubuntu-latest
    
    # Required permissions to push to GHCR
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          # Generates tags like ghcr.io/user/repo:main
          tags: |
            type=ref,event=branch
            type=sha,format=long

      - name: Build and Push Image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

## 🧠 Key Takeaway
Automating container builds ensures that every merge to `main` results in a ready-to-deploy artifact. Leveraging established GitHub Actions like `build-push-action` abstracts away complex `docker build` and `docker push` shell commands, handling authentication and tagging cleanly.
