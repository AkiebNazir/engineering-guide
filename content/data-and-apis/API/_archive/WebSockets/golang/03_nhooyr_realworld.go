// REAL-WORLD EXAMPLE: nhooyr.io/websocket (External 2)
// Demonstrates: Context cancellation, Typed JSON decoding/encoding
package main

import (
	"context"
	"log"
	"net/http"
	"time"

	"nhooyr.io/websocket"
	"nhooyr.io/websocket/wsjson"
)

type ChatMessage struct {
	User string `json:"user"`
	Text string `json:"text"`
}

func main() {
	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		// Accept the WebSocket connection
		c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
			InsecureSkipVerify: true,
		})
		if err != nil {
			log.Println(err)
			return
		}
		defer c.Close(websocket.StatusInternalError, "internal error")

		// Create a context that times out after 1 hour
		ctx, cancel := context.WithTimeout(r.Context(), time.Hour)
		defer cancel()

		for {
			var msg ChatMessage
			// Read JSON
			err = wsjson.Read(ctx, c, &msg)
			if err != nil {
				log.Println("Read Error:", err)
				break
			}
			
			log.Printf("Received: %s says %s", msg.User, msg.Text)

			// Write JSON (Echo back)
			err = wsjson.Write(ctx, c, msg)
			if err != nil {
				log.Println("Write Error:", err)
				break
			}
		}

		c.Close(websocket.StatusNormalClosure, "")
	})
	
	log.Println("Nhooyr WS Server started on :8080")
	http.ListenAndServe(":8080", nil)
}
