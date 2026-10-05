// BASIC EXAMPLE: Go Inbuilt net/http
// Demonstrates native Go 1.22+ wildcard and method routing
package main

import (
	"encoding/json"
	"net/http"
	"strconv"
)

type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

var db = make(map[string]User)

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("POST /users", func(w http.ResponseWriter, r *http.Request) {
		var u User
		json.NewDecoder(r.Body).Decode(&u)
		u.ID = strconv.Itoa(len(db) + 1)
		db[u.ID] = u
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(u)
	})

	mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
		user, exists := db[r.PathValue("id")]
		if !exists {
			http.Error(w, "Not found", http.StatusNotFound)
			return
		}
		json.NewEncoder(w).Encode(user)
	})

	http.ListenAndServe(":8080", mux)
}
