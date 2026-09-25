package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

const payloadDir = "payloads"

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	err = os.MkdirAll(payloadDir, 0755)
	if err != nil {
		http.Error(w, "Failed to create dir", http.StatusInternalServerError)
		return
	}

	filename := fmt.Sprintf("payload_%d.json", time.Now().UnixNano())
	filepath := filepath.Join(payloadDir, filename)

	err = os.WriteFile(filepath, body, 0644)
	if err != nil {
		http.Error(w, "Failed to write file", http.StatusInternalServerError)
		return
	}

	fmt.Printf("Received webhook, saved to %s\n", filepath)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "success"}`))
}

func main() {
	fmt.Println("Starting Data Engineering Project: 04_webhook_listener")
	http.HandleFunc("/webhook", webhookHandler)

	fmt.Println("Listening for webhooks on port 8080...")
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		log.Fatal(err)
	}
}
