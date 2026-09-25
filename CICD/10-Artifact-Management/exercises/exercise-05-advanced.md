# Exercise 5: Enterprise Artifact Pipeline with GitHub Actions and Cosign 🔴

## 🎯 Objective
Design a complete, enterprise-grade GitHub Actions pipeline that builds a Docker image, pushes it to GitHub Container Registry (GHCR), tags it appropriately based on the event (PR vs. Main branch), and cryptographically signs the artifact using Cosign (Keyless signing).

## 📋 Prerequisites
* Understanding of GitHub Actions
* Understanding of OIDC (OpenID Connect) concepts

## 📝 Instructions

Since this is an advanced scenario, you will not execute this locally. Instead, your task is to write the `pipeline.yml` file that satisfies the enterprise requirements, which you could commit to a real GitHub repository.

### Requirements:
1. **Trigger**: Run on pull requests to `main`, and pushes to `main` or tags (`v*`).
2. **Registry**: Push to `ghcr.io`.
3. **Tagging Logic**:
   - PRs: Tag with `pr-<number>`.
   - Main branch: Tag with `sha-<hash>` and `latest`.
   - Tags: Tag with the SemVer tag (`v1.0.0`).
4. **Caching**: Use Docker build caching via GitHub Actions cache.
5. **Security (Signing)**: Use `sigstore/cosign` to sign the image in OIDC keyless mode, but *only* if pushing to `main` or a tag (not for PRs).

### Step 1: Write the GitHub Actions Workflow

Create `.github/workflows/enterprise-artifact.yml`:

```yaml
name: Enterprise Artifact Build & Sign

on:
  push:
    branches: [ "main" ]
    tags: [ 'v*.*.*' ]
  pull_request:
    branches: [ "main" ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-push-sign:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write # CRITICAL: Required for OIDC keyless signing with Cosign

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install Cosign
        if: github.event_name != 'pull_request'
        uses: sigstore/cosign-installer@v3.4.0
        with:
          cosign-release: 'v2.2.3'

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log into registry ${{ env.REGISTRY }}
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=pr
            type=sha,format=long,prefix=sha-
            type=semver,pattern={{version}}
            type=raw,value=latest,enable=${{ github.ref == format('refs/heads/{0}', 'main') }}

      - name: Build and push Docker image
        id: build-and-push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Sign the published Docker image
        if: ${{ github.event_name != 'pull_request' }}
        env:
          # Get the digest of the pushed image from the build step
          TAGS: ${{ steps.meta.outputs.tags }}
          DIGEST: ${{ steps.build-and-push.outputs.digest }}
        # The keyless signing process uses the GitHub Actions OIDC token
        run: echo "${TAGS}" | xargs -I {} cosign sign --yes {}@${DIGEST}
```

## 💡 Hints
* `id-token: write` is the magic permission that allows GitHub Actions to request a short-lived OIDC token. Cosign uses this token to prove to the Sigstore transparency log that "This specific GitHub Actions workflow on this specific repository signed this image."
* `docker/metadata-action` handles all the complex logic of deciding what tags apply based on the GitHub event (PR vs Push).
* We sign the `DIGEST` (`@sha256:...`) rather than the tag, because tags are mutable, but digests are immutable.

## ✅ Expected Output / Solution
When pushed to a real repo, this workflow will:
1. Build a Docker image using fast layer caching (`type=gha`).
2. Push it to `ghcr.io/youruser/yourrepo:sha-1234567`.
3. Create a cryptographic signature and attach it to the registry next to the image.
4. Anyone downloading your image can run `cosign verify ghcr.io/youruser/yourrepo:sha-1234567 --certificate-identity "https://github.com/youruser/yourrepo/.github/workflows/enterprise-artifact.yml@refs/heads/main" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"` to cryptographically prove the image was built by your CI server and not tampered with.

## 🧠 Key Takeaway
Enterprise artifact management isn't just about storing files. It involves automated caching, intelligent metadata tagging, and zero-trust security practices like keyless artifact signing to secure the software supply chain.
