# Exercise 4: Generating an SBOM with Syft 🟡

## 🎯 Objective
Generate a Software Bill of Materials (SBOM) for a container image and understand its contents.

## 📋 Prerequisites
- Docker installed
- `syft` installed (`brew install syft` or curl script)
- The image `my-secure-app:1.0` from Exercise 3.

## 📝 Instructions

1. **What is an SBOM?**
   An SBOM provides visibility into all the components inside your software artifact. It's crucial for supply chain security and responding quickly to zero-day vulnerabilities (like Log4j).

2. **Generate a basic SBOM**
   Run Syft on the image:
   ```bash
   syft my-secure-app:1.0
   ```
   *Notice the tabular output listing all Alpine packages and Go modules.*

3. **Generate a standard SBOM format**
   To be machine-readable by other tools, generate the SBOM in SPDX JSON format:
   ```bash
   syft my-secure-app:1.0 -o spdx-json > sbom.spdx.json
   ```

4. **Inspect the SBOM**
   Open `sbom.spdx.json` and explore its contents.
   Look for:
   - The OS version (Alpine).
   - Individual packages installed by the OS.
   - Go dependencies and their exact versions.

5. **Scan an SBOM with Trivy**
   Trivy can read an SBOM directly to find vulnerabilities, which is useful if you archive SBOMs and want to rescan them weeks later without rebuilding the image.
   ```bash
   trivy sbom sbom.spdx.json
   ```

## 💡 Hints
- Formats like SPDX and CycloneDX are industry standards for SBOMs.
- In a modern CI/CD pipeline, the SBOM is generated during the build and attached to the container registry alongside the image.

## ✅ Expected Output
Syft standard output:
```text
 ✔ Loaded image            my-secure-app:1.0
 ✔ Parsed image
 ✔ Cataloged packages      [17 packages]

NAME                    VERSION                TYPE
alpine-baselayout       3.4.3-r2               apk
alpine-keys             2.4-r1                 apk
busybox                 1.36.1-r15             apk
golang.org/x/text       v0.14.0                go-module
...
```

## 🧠 Key Takeaway
An SBOM is the ingredient list for your software. Generating and storing it allows you to quickly query your infrastructure to see if you are affected by newly discovered vulnerabilities.
