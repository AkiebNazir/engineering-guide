# Exercise 3: Cross-Compiling Go Binaries with GoReleaser 🟡

## 🎯 Objective
Learn how to use GoReleaser to automatically cross-compile a Go application for multiple operating systems and architectures, creating multiple artifacts from a single build process.

## 📋 Prerequisites
* Go 1.21+ installed
* Git installed
* GoReleaser installed (e.g., via Homebrew: `brew install goreleaser` or download from GitHub)

## 📝 Instructions

### Step 1: Initialize a Git Repository
GoReleaser requires a Git repository with a semantic version tag to function properly.

```bash
mkdir go-cli-tool
cd go-cli-tool
git init
go mod init github.com/myuser/go-cli-tool
```

### Step 2: Write the Go CLI Application
Create a simple `main.go` that prints its version.

```go
package main

import (
	"fmt"
)

var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

func main() {
	fmt.Printf("My Go CLI Tool\n")
	fmt.Printf("Version: %s\n", version)
	fmt.Printf("Commit: %s\n", commit)
	fmt.Printf("Built at: %s\n", date)
}
```

### Step 3: Configure GoReleaser
Create a file named `.goreleaser.yml` in the root of the project.

```yaml
version: 2
project_name: go-cli-tool
builds:
  - env:
      - CGO_ENABLED=0
    goos:
      - linux
      - windows
      - darwin
    goarch:
      - amd64
      - arm64
    ldflags:
      - -s -w -X main.version={{.Version}} -X main.commit={{.Commit}} -X main.date={{.Date}}
archives:
  - format: tar.gz
    name_template: >-
      {{ .ProjectName }}_
      {{- title .Os }}_
      {{- if eq .Arch "amd64" }}x86_64
      {{- else }}{{ .Arch }}{{ end }}
    format_overrides:
      - goos: windows
        format: zip
checksum:
  name_template: 'checksums.txt'
```

### Step 4: Commit and Tag
GoReleaser looks for a Git tag to determine the version of the artifacts.

```bash
git add .
git commit -m "Initial commit"
git tag -a v1.0.0 -m "Release v1.0.0"
```

### Step 5: Run GoReleaser locally (Snapshot mode)
Normally, GoReleaser publishes to GitHub. We will run it in `--snapshot` mode to test the build locally without actually publishing.

```bash
goreleaser release --snapshot --clean
```

### Step 6: Inspect the Output
List the contents of the generated `dist/` directory.

```bash
ls dist/
```

Test one of the generated binaries (assuming you are on a Mac or Linux machine matching the architecture):
```bash
./dist/go-cli-tool_darwin_arm64/go-cli-tool
```

## 💡 Hints
* `ldflags` in the `.goreleaser.yml` automatically injects the Git commit hash and version tag directly into the Go binary at compile time.
* The `archives` section instructs GoReleaser to zip Windows binaries but tar.gz Linux/Mac binaries, matching OS conventions.

## ✅ Expected Output
```text
$ ls dist/
checksums.txt
go-cli-tool_Darwin_arm64.tar.gz
go-cli-tool_Darwin_x86_64.tar.gz
go-cli-tool_Linux_arm64.tar.gz
go-cli-tool_Linux_x86_64.tar.gz
go-cli-tool_Windows_arm64.zip
go-cli-tool_Windows_x86_64.zip
... (and extracted folders)

$ ./dist/go-cli-tool_darwin_arm64/go-cli-tool
My Go CLI Tool
Version: v1.0.0-next
Commit: <your-git-sha>
Built at: <timestamp>
```

## 🧠 Key Takeaway
GoReleaser automates the tedious process of building matrices of artifacts (OS x Arch), packaging them, generating checksums, and stamping them with version metadata. This is the industry standard for releasing Go binaries.
