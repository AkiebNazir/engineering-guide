# Exercise 4: DORA Metrics Collection 🟡

## 🎯 Objective
Create a service that ingests deployment webhooks and calculates "Lead Time for Changes", a key DORA metric.

## 📋 Prerequisites
- Go programming.

## 📝 Instructions

1. Create a new Go module: `go mod init dorametrics`
2. Create `main.go`:
   ```go
   package main
   
   import (
   	"encoding/json"
   	"fmt"
   	"log"
   	"net/http"
   	"time"
   )
   
   type WebhookPayload struct {
   	Repository string    `json:"repository"`
   	CommitID   string    `json:"commit_id"`
   	CommitTime time.Time `json:"commit_time"`
   	DeployTime time.Time `json:"deploy_time"`
   	Status     string    `json:"status"`
   }
   
   func handleWebhook(w http.ResponseWriter, r *http.Request) {
   	if r.Method != http.MethodPost {
   		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
   		return
   	}
   
   	var payload WebhookPayload
   	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
   		http.Error(w, "Bad request", http.StatusBadRequest)
   		return
   	}
   
   	if payload.Status == "success" {
   		leadTime := payload.DeployTime.Sub(payload.CommitTime)
   		
   		fmt.Printf("✅ Deployment Successful!\n")
   		fmt.Printf("Repository: %s\n", payload.Repository)
   		fmt.Printf("Commit: %s\n", payload.CommitID)
   		fmt.Printf("Lead Time for Change: %.2f minutes\n", leadTime.Minutes())
   		
   		// In a real scenario, push this metric to Datadog/Prometheus
   	}
   
   	w.WriteHeader(http.StatusOK)
   }
   
   func main() {
   	http.HandleFunc("/deploy-webhook", handleWebhook)
   	fmt.Println("DORA Metrics collector running on :8080")
   	log.Fatal(http.ListenAndServe(":8080", nil))
   }
   ```

3. Run the server: `go run main.go`
4. In another terminal, simulate a webhook using `curl`:
   ```bash
   curl -X POST http://localhost:8080/deploy-webhook \
   -H "Content-Type: application/json" \
   -d '{
     "repository": "frontend-app",
     "commit_id": "abc123def",
     "commit_time": "2026-09-25T14:00:00Z",
     "deploy_time": "2026-09-25T14:45:00Z",
     "status": "success"
   }'
   ```

## 💡 Hints
- Lead Time for Changes measures the time from when code is committed to when it successfully runs in production.
- You calculate it by subtracting Commit Time from Deployment Time.

## ✅ Expected Output / Solution
The server will log:
```
✅ Deployment Successful!
Repository: frontend-app
Commit: abc123def
Lead Time for Change: 45.00 minutes
```

## 🧠 Key Takeaway
Collecting DORA metrics requires instrumenting your CI/CD pipelines to emit events. By centralizing this data collection, engineering leaders can identify bottlenecks in the software delivery lifecycle.
