# Exercise 1: Health Check Endpoints 🩺

## 🎯 Objective
Create standard Liveness (`/health`) and Readiness (`/ready`) endpoints for a web service.

## 📋 Prerequisites
- Python 3.9+ or Go installed

## 📝 Instructions

In modern CI/CD and orchestration (like Kubernetes), apps must report their health. 

### Step 1: Create a Go Application
Create a file named `main.go`.

```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

// Global state to simulate startup
var isReady bool = false

type StatusResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

func healthzHandler(w http.ResponseWriter, r *http.Request) {
	// Liveness: Always returns 200 if the server is running
	response := StatusResponse{
		Status:    "ok",
		Timestamp: time.Now().Format(time.RFC3339),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func readyzHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	if !isReady {
		// Readiness: Return 503 until application is fully initialized
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(StatusResponse{Status: "not_ready", Timestamp: time.Now().Format(time.RFC3339)})
		return
	}
	
	json.NewEncoder(w).Encode(StatusResponse{Status: "ready", Timestamp: time.Now().Format(time.RFC3339)})
}

func main() {
	http.HandleFunc("/healthz", healthzHandler)
	http.HandleFunc("/readyz", readyzHandler)

	// Simulate heavy initialization (e.g., connecting to DB)
	go func() {
		time.Sleep(10 * time.Second)
		isReady = true
		log.Println("Application is now ready!")
	}()

	log.Println("Server starting on :8080...")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### Step 2: Run and Test
1. Run the server: `go run main.go`
2. Open another terminal and test liveness:
   `curl -i http://localhost:8080/healthz` (Should return 200 OK immediately)
3. Test readiness immediately:
   `curl -i http://localhost:8080/readyz` (Should return 503 Service Unavailable)
4. Wait 10 seconds, then test readiness again:
   `curl -i http://localhost:8080/readyz` (Should return 200 OK)

## 💡 Hints
- The `/healthz` endpoint tells the system "Don't kill me, I am running."
- The `/readyz` endpoint tells the system "Send me traffic, I am ready to process it."

## ✅ Expected Output / Solution
You should see JSON responses like `{"status":"ok","timestamp":"2023-10-25T10:00:00Z"}`.

## 🧠 Key Takeaway
Separating liveness and readiness prevents traffic from being routed to an application that is still warming up or loading caches.
