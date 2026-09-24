// REAL-WORLD EXAMPLE: gorilla/websocket (External 1)
// Demonstrates: Safe concurrency with Channels, Hub/Spoke architecture for Chat Room
package main

import (
	"log"
	"net/http"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true }, // Allow all origins for demo
}

// Global state
var clients = make(map[*websocket.Conn]bool) // Connected clients
var broadcast = make(chan []byte)           // Broadcast channel

func main() {
	http.HandleFunc("/ws", handleConnections)
	go handleMessages()

	log.Println("Gorilla WS Server started on :8080")
	http.ListenAndServe(":8080", nil)
}

func handleConnections(w http.ResponseWriter, r *http.Request) {
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer ws.Close()

	clients[ws] = true

	// Infinite loop to read messages from this client
	for {
		_, msg, err := ws.ReadMessage()
		if err != nil {
			delete(clients, ws)
			break
		}
		// Send the received message to the global broadcast channel
		broadcast <- msg
	}
}

func handleMessages() {
	for {
		// Grab the next message from the broadcast channel
		msg := <-broadcast
		
		// Send it to every connected client
		for client := range clients {
			err := client.WriteMessage(websocket.TextMessage, msg)
			if err != nil {
				client.Close()
				delete(clients, client)
			}
		}
	}
}
