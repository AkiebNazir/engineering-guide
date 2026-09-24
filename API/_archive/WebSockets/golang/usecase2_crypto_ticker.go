package main

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}

func handleTicker(w http.ResponseWriter, r *http.Request) {
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println(err)
		return
	}
	defer ws.Close()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()
	
	price := 50000.0

	for {
		select {
		case <-ticker.C:
			price += (rand.Float64() - 0.5) * 100
			msg := fmt.Sprintf(`{"symbol":"BTC", "price": %.2f}`, price)
			if err := ws.WriteMessage(websocket.TextMessage, []byte(msg)); err != nil {
				log.Println("Client disconnected")
				return
			}
		}
	}
}

func main() {
	http.HandleFunc("/ticker", handleTicker)
	http.ListenAndServe(":8080", nil)
}
