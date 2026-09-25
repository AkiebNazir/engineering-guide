# Exercise 3: Deployment with Automated Rollback 🔙

## 🎯 Objective
Create a Go program that simulates a deployment process. It will "deploy" a version, run a simulated smoke test, and automatically roll back if the smoke test fails.

## 📋 Prerequisites
- Go installed

## 📝 Instructions
1. Create a file named `deployer.go`.
2. Accept a version string from the user.
3. Simulate deploying by printing out the action.
4. Simulate a smoke test that randomly fails (or fails based on a specific input version like `vbad`).
5. Implement a `rollback()` function that restores the previous state if the smoke test fails.
6. The program should exit with code `1` if it had to roll back.

## 💡 Hints
- Use `os.Args` to read CLI arguments.
- Abstract the "deployment state" as a simple global or struct string variable holding the current version.

## ✅ Expected Output / Solution

```go
// deployer.go
package main

import (
	"fmt"
	"os"
)

var currentVersion = "v1.0.0"

func deploy(version string) error {
	fmt.Printf("📦 Deploying version %s (Overwriting %s)...\n", version, currentVersion)
	// Simulate deployment by updating state
	return nil
}

func smokeTest(version string) error {
	fmt.Printf("💨 Running smoke test for %s...\n", version)
	if version == "v-broken" {
		return fmt.Errorf("smoke test failed: 500 Internal Server Error")
	}
	fmt.Println("✅ Smoke test passed!")
	return nil
}

func rollback(previousVersion string) {
	fmt.Printf("🔙 Rolling back to previous version: %s...\n", previousVersion)
	currentVersion = previousVersion
	fmt.Println("✅ Rollback complete.")
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run deployer.go <version>")
		os.Exit(1)
	}

	targetVersion := os.Args[1]
	previousVersion := currentVersion

	// Step 1: Deploy
	err := deploy(targetVersion)
	if err != nil {
		fmt.Println("Deploy failed immediately.")
		os.Exit(1)
	}
	currentVersion = targetVersion

	// Step 2: Smoke Test
	err = smokeTest(targetVersion)
	if err != nil {
		fmt.Printf("❌ Error: %v\n", err)
		
		// Step 3: Rollback on failure
		rollback(previousVersion)
		os.Exit(1)
	}

	fmt.Printf("🎉 Deployment of %s successful! System is stable.\n", currentVersion)
}
```

## 🧠 Key Takeaway
Automated rollbacks are the safety net of Continuous Deployment. By tightly coupling the deployment, the smoke test, and the rollback procedure, you remove the human panic when a bad release goes out.
