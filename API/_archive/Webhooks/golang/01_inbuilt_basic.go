// BASIC EXAMPLE: Go Inbuilt net/http
// Demonstrates native Go handling of Webhook payloads and HMAC verification.
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"io"
	"net/http"
)

var secret = []byte("my_super_secret_webhook_key")

func main() {
	http.HandleFunc("POST /webhook", func(w http.ResponseWriter, r *http.Request) {
		payload, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "Bad Request", http.StatusBadRequest)
			return
		}
		
		sig := r.Header.Get("X-Signature")

		mac := hmac.New(sha256.New, secret)
		mac.Write(payload)
		expected := hex.EncodeToString(mac.Sum(nil))

		if hmac.Equal([]byte(expected), []byte(sig)) {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusUnauthorized)
		}
	})
	
	http.ListenAndServe(":8080", nil)
}
