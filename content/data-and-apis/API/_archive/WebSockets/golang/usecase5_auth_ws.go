package main

import (
	"log"
	"net/http"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}

func authMiddleware(w http.ResponseWriter, r *http.Request) {
	tokenString := r.URL.Query().Get("token")
	
	if tokenString != "valid-jwt-token" {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("Unauthorized"))
		return
	}

	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println(err)
		return
	}
	defer ws.Close()
	
	ws.WriteMessage(websocket.TextMessage, []byte("Welcome, authenticated user!"))
	
	for {
		if _, _, err := ws.ReadMessage(); err != nil {
			break
		}
	}
}

func main() {
	http.HandleFunc("/ws", authMiddleware)
	http.ListenAndServe(":8080", nil)
}
