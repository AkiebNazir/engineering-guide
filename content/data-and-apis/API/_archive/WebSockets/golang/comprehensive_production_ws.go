package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true }, // Allow CORS in prod appropriately
}

// Client represents a connected WebSocket user
type Client struct {
	ID   string
	Conn *websocket.Conn
	Send chan []byte
}

// Hub manages active clients and broadcast channels (rooms)
type Hub struct {
	sync.RWMutex
	Rooms map[string]map[*Client]bool
}

var globalHub = &Hub{
	Rooms: make(map[string]map[*Client]bool),
}

// Request Payload Format
type WsMessage struct {
	Action  string `json:"action"`
	Room    string `json:"room"`
	Message string `json:"message"`
}

// Middleware: Authenticate WebSocket upgrade via token query param
func AuthMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		if token != "secret-jwt" {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	}
}

// writePump handles sending data to the client (with ping/pong healthchecks)
func (c *Client) writePump() {
	ticker := time.NewTicker(50 * time.Second) // Ping every 50s
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case msg, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			c.Conn.WriteMessage(websocket.TextMessage, msg)
		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// readPump handles reading data from the client
func (c *Client) readPump() {
	defer c.Conn.Close()
	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error { c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second)); return nil })

	for {
		_, payload, err := c.Conn.ReadMessage()
		if err != nil {
			log.Println("Client Disconnected:", c.ID)
			break
		}

		// Message Router
		var req WsMessage
		if err := json.Unmarshal(payload, &req); err == nil {
			switch req.Action {
			case "join_room":
				globalHub.Lock()
				if globalHub.Rooms[req.Room] == nil {
					globalHub.Rooms[req.Room] = make(map[*Client]bool)
				}
				globalHub.Rooms[req.Room][c] = true
				globalHub.Unlock()
				c.Send <- []byte("Joined room: " + req.Room)

			case "send_message":
				globalHub.RLock()
				roomClients := globalHub.Rooms[req.Room]
				for client := range roomClients {
					if client != c { // Don't echo to sender
						client.Send <- []byte(req.Message)
					}
				}
				globalHub.RUnlock()
			}
		}
	}
}

func ServeWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}

	client := &Client{
		ID:   "usr_" + r.URL.Query().Get("token"),
		Conn: conn,
		Send: make(chan []byte, 256),
	}

	go client.writePump()
	go client.readPump()
}

func main() {
	http.HandleFunc("/ws", AuthMiddleware(ServeWS))
	log.Println("WebSocket Server started on :8080/ws")
	http.ListenAndServe(":8080", nil)
}
