package main

import (
	"encoding/json"
	"net/http"
)

type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func userHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		// Simulate DB Fetch
		user := User{ID: "123", Name: "Alice"}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(user)
	} else if r.Method == http.MethodPost {
		var newUser User
		json.NewDecoder(r.Body).Decode(&newUser)
		w.WriteHeader(http.StatusCreated) // 201
		json.NewEncoder(w).Encode(map[string]string{"status": "created"})
	}
}

func main() {
	http.HandleFunc("/users", userHandler)
	http.ListenAndServe(":8080", nil)
}
