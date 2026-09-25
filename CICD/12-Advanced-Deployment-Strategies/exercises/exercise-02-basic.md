# Exercise 2: Implementing a Health Check Endpoint in Go 🟢

## 🎯 Objective
Create a simple web service in Go that exposes a `/healthz` endpoint, which is a fundamental requirement for automated deployments (like Kubernetes rolling updates).

## 📋 Prerequisites
- Go installed

## 📝 Instructions

1. Create a file named `main.go`.
2. Implement a standard HTTP server.
3. Add a `/healthz` endpoint that checks an internal "isReady" variable.

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

var isReady = false

type HealthResponse struct {
	Status string `json:"status"`
	Uptime string `json:"uptime"`
}

var startTime time.Time

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	uptime := time.Since(startTime).String()
	response := HealthResponse{Uptime: uptime}

	if isReady {
		w.WriteHeader(http.StatusOK)
		response.Status = "UP"
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
		response.Status = "STARTING"
	}

	json.NewEncoder(w).Encode(response)
}

func main() {
	startTime = time.Now()
	
	// Simulate app startup time (e.g. connecting to DB)
	go func() {
		time.Sleep(3 * time.Second)
		isReady = true
		fmt.Println("Application is now READY.")
	}()

	http.HandleFunc("/healthz", healthHandler)
	
	fmt.Println("Server starting on :8080...")
	http.ListenAndServe(":8080", nil)
}
```

## 💡 Hints
- Run the app using `go run main.go`.
- In a separate terminal, curl the endpoint: `curl http://localhost:8080/healthz`.

## ✅ Expected Output
If you curl immediately:
```json
{"status":"STARTING","uptime":"1.2s"}
```
(Status code 503)

If you curl after 3 seconds:
```json
{"status":"UP","uptime":"4.5s"}
```
(Status code 200)

## 🧠 Key Takeaway
Load balancers and orchestrators rely on HTTP status codes from health endpoints to know if a newly deployed instance is ready to receive traffic.
