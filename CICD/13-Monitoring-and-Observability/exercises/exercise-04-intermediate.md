# Exercise 4: CI/CD Pipeline Monitoring Script ⏱️

## 🎯 Objective
Write a script that tracks build duration and success rate, simulating pipeline observability.

## 📋 Prerequisites
- Go installed

## 📝 Instructions

Just as we monitor applications, we must monitor our CI/CD pipelines. Long build times or high failure rates severely impact developer productivity.

### Step 1: Write the CI/CD Wrapper
Create `pipeline_monitor.go`. This program will wrap any command (like `go test` or `npm run build`), measure its duration, record success/failure, and append the metric to a local log file.

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"
)

type BuildMetric struct {
	Timestamp string  `json:"timestamp"`
	Command   string  `json:"command"`
	Duration  float64 `json:"duration_seconds"`
	Success   bool    `json:"success"`
	ExitCode  int     `json:"exit_code"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run pipeline_monitor.go <command> [args...]")
		os.Exit(1)
	}

	commandName := os.Args[1]
	commandArgs := os.Args[2:]

	start := time.Now()
	
	// Execute the command
	cmd := exec.Command(commandName, commandArgs...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	
	err := cmd.Run()
	
	duration := time.Since(start).Seconds()
	
	metric := BuildMetric{
		Timestamp: time.Now().Format(time.RFC3339),
		Command:   fmt.Sprintf("%v %v", commandName, commandArgs),
		Duration:  duration,
		Success:   err == nil,
		ExitCode:  0,
	}

	if err != nil {
		if exitError, ok := err.(*exec.ExitError); ok {
			metric.ExitCode = exitError.ExitCode()
		} else {
			metric.ExitCode = -1
		}
	}

	recordMetric(metric)

	if !metric.Success {
		os.Exit(metric.ExitCode)
	}
}

func recordMetric(metric BuildMetric) {
	file, err := os.OpenFile("pipeline_metrics.jsonl", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Printf("Error opening metrics file: %v\n", err)
		return
	}
	defer file.Close()

	jsonLine, _ := json.Marshal(metric)
	file.WriteString(string(jsonLine) + "\n")
}
```

### Step 2: Run and Monitor
1. Try a successful command: `go run pipeline_monitor.go sleep 2`
2. Try a failing command: `go run pipeline_monitor.go ls /nonexistent`
3. Inspect the metrics file: `cat pipeline_metrics.jsonl`

## 💡 Hints
- This script uses `.jsonl` (JSON Lines). Each line is a valid JSON object. This format is heavily used for streaming logs to aggregators.

## ✅ Expected Output / Solution
`pipeline_metrics.jsonl` should contain:
```json
{"timestamp":"2023-10-25T12:00:00Z","command":"sleep [2]","duration_seconds":2.005,"success":true,"exit_code":0}
{"timestamp":"2023-10-25T12:00:03Z","command":"ls [/nonexistent]","duration_seconds":0.012,"success":false,"exit_code":1}
```

## 🧠 Key Takeaway
Pipeline telemetry allows engineering leaders to track Lead Time for Changes and pinpoint bottlenecks in the CI/CD process.
