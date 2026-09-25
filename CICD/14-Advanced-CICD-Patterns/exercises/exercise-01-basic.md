# Chapter 14: Advanced CI/CD Patterns

<Exercise 1: Reusable Workflow Mock 🟢>
## 🎯 Objective
Create a simple script in Go that demonstrates the concept of Pipeline as Code by defining a reusable job step.

## 📋 Prerequisites
- Basic understanding of Go.

## 📝 Instructions
1. We will build a simple generator that creates a standard build step for any given service.
2. Create a file `reusable.go`.

## 💡 Hints
- Use text/template or standard string formatting.

## ✅ Expected Output / Solution
```go
package main

import (
	"fmt"
)

// ReusableStep simulates a pipeline step structure
type ReusableStep struct {
	Name    string
	Command string
}

func GenerateBuildStep(serviceName string) ReusableStep {
	return ReusableStep{
		Name:    fmt.Sprintf("Build %s", serviceName),
		Command: fmt.Sprintf("docker build -t %s:latest ./%s", serviceName, serviceName),
	}
}

func main() {
	step := GenerateBuildStep("auth-api")
	fmt.Printf("Step Name: %s\nCommand: %s\n", step.Name, step.Command)
}
```

## 🧠 Key Takeaway
Pipeline as code allows you to create abstractions and reusable components, reducing repetition.
</Exercise 1: Reusable Workflow Mock 🟢>
