package main

import (
	"encoding/json"
	"log"
	"net/http"
)

func patchUserHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPatch {
		http.Error(w, "Use PATCH", http.StatusMethodNotAllowed)
		return
	}
	
	var updates map[string]interface{}
	json.NewDecoder(r.Body).Decode(&updates)
	
	// Apply only the fields present in the 'updates' map to the DB
	log.Printf("Updating fields: %v", updates)
	
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

func main() {
	http.HandleFunc("/users/1", patchUserHandler)
	http.ListenAndServe(":8080", nil)
}
