package main

import (
	"net/http"
)

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// Verify Signature header here (e.g., Stripe, GitHub)
	
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Webhook received successfully"))
}

func main() {
	http.HandleFunc("/webhook", webhookHandler)
	http.ListenAndServe(":8080", nil)
}
