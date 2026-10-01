package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

func fetchFeed() {
	client := &http.Client{Timeout: 10 * time.Second}
	req, _ := http.NewRequest("GET", "https://jsonplaceholder.typicode.com/posts?_limit=10&_start=0", nil)
	
	resp, err := client.Do(req)
	if err != nil {
		log.Println("Request failed")
		return
	}
	defer resp.Body.Close()
	
	var result []map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	log.Printf("Fetched %d paginated posts.\n", len(result))
}

func main() {
	fetchFeed()
}
