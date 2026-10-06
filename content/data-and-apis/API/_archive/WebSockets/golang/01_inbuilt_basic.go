// BASIC EXAMPLE: Go Inbuilt net/http Hijacker
// Demonstrates how Go allows you to "hijack" the underlying TCP connection from an HTTP request
package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		hj, ok := w.(http.Hijacker)
		if !ok {
			http.Error(w, "webserver doesn't support hijacking", http.StatusInternalServerError)
			return
		}
		
		conn, bufrw, err := hj.Hijack()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer conn.Close()

		// Write HTTP 101 manually (simplified handshake)
		bufrw.WriteString("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n")
		bufrw.Flush()

		fmt.Println("Connection hijacked successfully!")
	})
	http.ListenAndServe(":8080", nil)
}
