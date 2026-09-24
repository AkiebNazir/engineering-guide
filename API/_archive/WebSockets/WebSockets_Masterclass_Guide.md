# WebSockets: The Complete Masterclass

To master WebSockets, you must understand how they bridge the gap between the stateless, request-driven HTTP world, and the stateful, persistent TCP networking world.

## Part 1: The Core Philosophy (Why not HTTP?)

HTTP is a stateless, half-duplex protocol. The client asks, the server answers. The server **cannot** push data to the client unprompted.

Before WebSockets, engineers used terrible hacks:
1. **Short Polling**: Client runs `setInterval` and does an AJAX `GET /updates` every 1 second. (Massive server load, mostly empty responses).
2. **Long Polling**: Client makes a `GET` request. The server holds the TCP connection open indefinitely until it has data, sends it, and closes the connection. The client immediately reconnects. (High overhead establishing TCP connections).

### The WebSocket Paradigm
WebSockets provide a **full-duplex, persistent connection**.
- Client and Server can send data to each other simultaneously at any time.
- Zero HTTP header overhead per message (saving hundreds of bytes).
- Sub-millisecond latency.

---

## Part 2: The Handshake & Framing (Under the Hood)

WebSockets actually start their life as a standard HTTP/1.1 request!

**1. The Client Handshake Request:**
The browser sends a standard HTTP GET request with specific upgrade headers.
```http
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

**2. The Server Handshake Response:**
If the server supports WebSockets, it responds with a `101 Switching Protocols`.
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

**3. The Protocol Shift:**
At this exact moment, HTTP vanishes. The underlying TCP socket is kept alive, and both sides switch to talking via the **WebSocket Framing Protocol**.

Data is now sent in "Frames". A frame contains:
- **FIN Bit**: Is this the final fragment of the message?
- **OpCode**: Is this Text (0x1), Binary (0x2), Close (0x8), Ping (0x9), or Pong (0xA)?
- **Masking Key**: Data from client to server is XOR masked to prevent proxy cache poisoning.
- **Payload Data**: The actual bytes.

---

## Part 3: Production Mastery & Advanced Architecture

Writing a `ws.send()` loop is easy. Running WebSockets in production for millions of users is notoriously difficult.

### 1. The Stateful Server Problem
REST APIs are stateless; any load balancer can route request #1 to Server A, and request #2 to Server B.
WebSockets are **Stateful**. A connection is tied to a specific server's memory (RAM) and a specific OS file descriptor.

If User Alice connects to Server A, and User Bob connects to Server B, how do they chat? Server A doesn't know about Bob!

**Master Solution: Pub/Sub Backplane**
You must introduce a message broker (Redis Pub/Sub, Kafka, or RabbitMQ).
1. Alice sends a message to Server A.
2. Server A publishes the message to Redis on channel `chat_room_1`.
3. Server B is subscribed to `chat_room_1` on Redis.
4. Server B receives the message from Redis and pushes it down the WebSocket to Bob.

### 2. Connection Health (Ping / Pong)
TCP connections can silently drop (e.g., a mobile user drives into a tunnel). The OS might not notify the server that the socket is dead. You end up with "zombie connections" consuming RAM and file descriptors (Goroutines in Go).

**Master Solution: Heartbeats**
The Server must proactively send a `Ping` (OpCode 0x9) frame every ~30 seconds.
The WebSocket protocol dictates that the Client must respond automatically with a `Pong` (OpCode 0xA).
If the server doesn't receive a Pong within the timeout, it forcibly closes the TCP socket and frees the memory.

### 3. Load Balancer Configuration
Standard HTTP Load Balancers (like AWS ALB or NGINX) will aggressively kill idle connections after 60 seconds. 
If you run WebSockets, you must explicitly configure your Load Balancer's **Idle Timeout** to be longer than your Ping/Pong interval (e.g., 3600 seconds).

---

## Part 4: Building a Real-World Scalable Architecture (Go + Redis)

Here is how a Senior Engineer builds a horizontally scalable WebSocket server in Go.

```go
package main

import (
	"context"
	"log"
	"net/http"
	"github.com/go-redis/redis/v8"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{}
var rdb = redis.NewClient(&redis.Options{Addr: "localhost:6379"})

func wsHandler(w http.ResponseWriter, r *http.Request) {
	ws, _ := upgrader.Upgrade(w, r, nil)
	defer ws.Close()

	ctx := context.Background()
	pubsub := rdb.Subscribe(ctx, "global_chat")
	defer pubsub.Close()

	// Goroutine 1: Redis -> WebSocket (Sending to Client)
	go func() {
		for msg := range pubsub.Channel() {
			ws.WriteMessage(websocket.TextMessage, []byte(msg.Payload))
		}
	}()

	// Goroutine 2: WebSocket -> Redis (Receiving from Client)
	for {
		_, msg, err := ws.ReadMessage()
		if err != nil { break } // Client disconnected
		
		// Publish the message to the central Redis bus.
		// All other WebSocket servers will hear this and broadcast it to their clients!
		rdb.Publish(ctx, "global_chat", msg)
	}
}
```
*This architecture allows you to spin up 100 instances of this Go service behind an NGINX load balancer, and all clients will seamlessly communicate across instances.*
