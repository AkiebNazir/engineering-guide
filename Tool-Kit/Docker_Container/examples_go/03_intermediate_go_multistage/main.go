package main
import (
    "encoding/json"
    "net/http"
)
func main() {
    http.HandleFunc("/api/data", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "Multi-stage build complete!"})
    })
    http.ListenAndServe(":8080", nil)
}
