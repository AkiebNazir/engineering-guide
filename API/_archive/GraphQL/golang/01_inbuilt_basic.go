// BASIC EXAMPLE: Go Inbuilt net/http
// Demonstrates how a GraphQL server receives queries via HTTP POST.
package main

import (
	"encoding/json"
	"net/http"
	"strings"
)

func main() {
	http.HandleFunc("POST /graphql", func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			Query string `json:"query"`
		}
		json.NewDecoder(r.Body).Decode(&req)

		w.Header().Set("Content-Type", "application/json")
		
		// Simulated Parsing
		if strings.Contains(req.Query, "getUser") {
			w.Write([]byte(`{"data": {"getUser": {"name": "Alice"}}}`))
		} else {
			w.Write([]byte(`{"errors": [{"message": "Unknown query"}]}`))
		}
	})
	http.ListenAndServe(":8080", nil)
}
