package main

import (
	"log"
	"net/http"
	"time"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}

type CursorPos struct {
	UserID string  `json:"userId"`
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
}

func syncCursors(w http.ResponseWriter, r *http.Request) {
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil { return }
	defer ws.Close()

	ws.SetReadDeadline(time.Now().Add(60 * time.Second))
	ws.SetPingHandler(func(string) error {
		ws.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		var pos CursorPos
		err := ws.ReadJSON(&pos)
		if err != nil { break }
		log.Printf("User %s moved to (%f, %f)", pos.UserID, pos.X, pos.Y)
		// Broadcast to other connected clients in a real app
	}
}

func main() {
	http.HandleFunc("/sync", syncCursors)
	http.ListenAndServe(":8080", nil)
}
