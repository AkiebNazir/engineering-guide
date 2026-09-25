---
title: "WebSockets Theory"
description: "Master WebSockets: the <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> upgrade handshake, frame format, opcodes and close codes, message protocols, heartbeats, back-pressure, authentication, reconnection and resume, and scaling across servers, with Python and Go labs."
---

# WebSockets Theory

<div data-viz="api-ws"></div>

## What are WebSockets?
WebSockets provide a persistent, full-duplex communication channel over a single <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection. Unlike <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> (where a client must request data and wait for a response), a WebSocket connection stays open. Both the client and the server can push messages to each other independently and instantly.

They are standardised in **RFC 6455** (2011) and supported by every browser through the `WebSocket` <abbr title="Application Programming Interface">API</abbr>.

> **Analogy:** <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> is sending letters: every letter needs a stamped envelope, an address, and a reply is a separate letter. A WebSocket is a phone call: dial once (the handshake), then either side speaks at any time until someone hangs up.

### Why not just <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>?
| Technique | How it works | Problem |
| :--- | :--- | :--- |
| **Polling** | Client asks every N seconds | Wasted requests, delay up to N seconds |
| **Long polling** | Client asks, server holds the request until it has news | One request per message, header overhead, reconnect churn |
| **Server-Sent Events (<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>)** | One long <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> response streaming events **server to client** | One direction only; text only; simple and auto-reconnects |
| **WebSockets** | One upgraded connection, both directions, any data | Stateful: harder to scale, load balance and secure |

> **Key idea:** Choose WebSockets when you need **low-latency, two-way, frequent** messages (chat, multiplayer, collaborative editing, live trading). If the server only pushes updates (notifications, dashboards), **<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> is simpler**. If updates are rare, polling or Webhooks are simpler still.

## The Handshake

A WebSocket begins its life as a standard <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> `GET` request with an `Upgrade: websocket` header. If the server supports WebSockets, it responds with an `HTTP 101 Switching Protocols` status code, and the connection is upgraded from <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> to a persistent <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> WebSocket connection.

```http
GET /chat HTTP/1.1                                   HTTP/1.1 101 Switching Protocols
Host: example.com                                    Upgrade: websocket
Upgrade: websocket                                   Connection: Upgrade
Connection: Upgrade                                  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==          Sec-WebSocket-Protocol: chat.v2
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: chat.v2, chat.v1
Origin: https://app.example.com
```

| Header | Purpose |
| :--- | :--- |
| `Sec-WebSocket-Key` | 16 random bytes (base64) from the client |
| `Sec-WebSocket-Accept` | `base64(sha1(Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))`. Proves the server really speaks WebSocket (not a confused <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> server echoing headers). Python lab 1 and Go lab 1 both compute it by hand and check it against the RFC's example. |
| `Sec-WebSocket-Version` | Always `13` |
| `Sec-WebSocket-Protocol` | **Subprotocol** negotiation: the client lists versions/dialects, the server picks one. A neat way to version your message protocol. |
| `Origin` | Which web page opened the socket. **Servers must check it** (see Security). |
| `Sec-WebSocket-Extensions` | e.g. `permessage-deflate` compression |

```arch
node c "Client" at 0,0 icon=client color=slate
node s "Server" at 1,0 icon=server color=purple
c -> s : "GET /chat (Upgrade: websocket)"
s -> c : "101 Switching Protocols"
node tcp "TCP now carries WS frames, not HTTP" at 0.5,1 shape=card color=amber
c ..> tcp ..> s
c -> s : "text frame 'hello'"
s -> c : "text frame 'echo: hello'"
s -> c : "text frame (server pushes)"
c -> s : "ping frame"
s -> c : "pong frame"
c -> s : "close frame (1000)"
s -> c : "close frame (1000)"
node end "TCP connection closed" at 0.5,2 shape=card color=slate
c ..> end ..> s
```

`ws://` is plain, `wss://` runs over <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> (like https). **Always use `wss://` on the public internet.**

## Frames: What Travels on the Wire

After the upgrade, data moves in **frames**, not <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> messages.

```
 byte 0            byte 1            (ext. length)   (mask key)     payload
+-+-+-+-+-------+ +-+-------------+ +-------------+ +-----------+ +---------+
|F|R|R|R| opcode| |M| payload len | | 2 or 8 bytes| | 4 bytes   | |         |
|I|S|S|S|  (4)  | |A|    (7)      | | if len>=126 | | if MASK=1 | |         |
|N|V|V|V|       | |S|             | |             | |           | |         |
| |1|2|3|       | |K|             | |             | |           | |         |
+-+-+-+-+-------+ +-+-------------+ +-------------+ +-----------+ +---------+
```

| Opcode | Meaning | Notes |
| :---: | :--- | :--- |
| `0x1` | **Text** | <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8 |
| `0x2` | **Binary** | Anything: Protobuf, images, audio |
| `0x0` | Continuation | Fragments of a large message |
| `0x8` | **Close** | Carries a 2-byte status code + optional reason |
| `0x9` | **Ping** | Peer must answer with a Pong carrying the same payload |
| `0xA` | **Pong** | |

*   **FIN** = "this is the last fragment of the message".
*   **Length**: 0-125 fits in 7 bits; 126 means "next 2 bytes hold the length"; 127 means "next 8 bytes".
*   **Masking:** every **client-to-server** frame is <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-masked with a random 4-byte key; server-to-client frames are **not**. The point is not confidentiality; it stops a malicious page from crafting bytes that a caching proxy could mistake for <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> (cache poisoning). Servers must **reject unmasked client frames**.
*   A worked byte string, the RFC's own example: the masked text frame `"Hello"` is `81 85 37 fa 21 3d 7f 9f 4d 51 58` (`0x81` = FIN + text, `0x85` = masked + length 5, then the mask key, then 5 masked bytes). Both language tracks reproduce it.
*   **Message boundaries are preserved.** Unlike raw <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr>, each `send()` is received as one message, in order. WebSocket is <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> underneath, so delivery is reliable and ordered, per connection.

### Close codes

| Code | Name | Meaning |
| :---: | :--- | :--- |
| 1000 | Normal closure | Done |
| 1001 | Going away | Server restarting / page navigating away |
| 1002 | Protocol error | Invalid frame (e.g. unmasked client frame) |
| 1003 | Unsupported data | Got binary when only text is accepted |
| 1006 | Abnormal closure | **Never sent on the wire**; reported locally when the connection dropped without a close frame |
| 1007 | Invalid payload | e.g. text that is not valid <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8 |
| 1008 | Policy violation | Generic "you broke a rule" (rate limit, auth) |
| 1009 | Message too big | Exceeds the size limit |
| 1011 | Internal error | Server error, or keepalive ping timeout |
| 1012 / 1013 | Service restart / Try again later | Hints to reconnect (1013 for overload) |
| 4000-4999 | **Application codes** | Yours: `4401` unauthenticated, `4403` forbidden |

## You Must Design the Protocol

WebSocket gives you a **pipe, not a protocol**. There are no routes, verbs, status codes or request ids unless you invent them. A solid minimum is a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> envelope:

```json
// client -> server
{ "type": "join",   "room": "go" }
{ "type": "say",    "text": "hello" }
{ "type": "call",   "id": 7, "op": "add", "args": [2, 3] }        // request with an id...
// server -> client
{ "type": "message", "room": "go", "from": "ana", "text": "hello", "seq": 42 }
{ "type": "result",  "id": 7, "result": 5 }                        // ...answered with the same id
{ "type": "error",   "code": "bad_request", "detail": "unknown type" }
```

*   Always include a `type`. Never crash on unknown types or bad <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>: reply with an `error` message and keep the connection.
*   For request/response over a socket, correlate with an **`id`** (Go lab 2).
*   Add a **`seq`** to server events if clients must not miss anything (Python lab 5).
*   Version the protocol with a **subprotocol** (`chat.v2`), or a `v` field.
*   Consider **Protobuf over binary frames** for high-volume or mobile traffic (`Protobuf/`).
*   Validate and limit everything: message size, rate, field lengths.

## Keeping Connections Healthy

### Heartbeats: detecting dead peers

<abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> does not tell you when the other side has silently vanished (laptop lid closed, phone left Wi-Fi, a NAT dropped its table). Without heartbeats the server holds that connection, and its memory, forever.

*   The server sends a **ping** every 20-30 s; the peer's library answers with a **pong** automatically.
*   No pong within the timeout: close (typically 1011) and free resources.
*   Measured in Python lab 4: with `ping_interval=0.2s, ping_timeout=0.3s` a frozen client was detected in 0.8 s and closed with `1011 keepalive ping timeout`; with heartbeats disabled the handler was **still blocked** after 1.5 s (a leak).
*   Pings also keep NATs and load balancers from expiring idle connections (often 60 s).
*   **Idle timeout** is different: "this client has sent no application messages for N minutes". Go lab 4 shows both.

### Back-pressure and slow consumers

Every connection has an outgoing buffer. If one client reads slowly and you keep writing, memory grows until the process dies. Rules:

1.  Give **each client a bounded outgoing queue**.
2.  Decide a policy when it is full: **drop oldest** (live prices), **drop newest**, or **disconnect** the client (when no message may be lost; it will resume, see below).
3.  **Never let the publisher wait** on a slow subscriber.

Python lab 4 (queue with drop-oldest: publisher finished 200 messages in 0.25 s regardless of the slow client, which received 33 but always the *latest*) and Go lab 3 (hub evicts the slow client with close code 1013 while 30 fast clients receive all 200 messages) both prove this.

### Flood control

A token bucket per connection (messages per second) protects the server. Persistent abusers get `1008 Policy Violation`. See Python lab 4 (10 accepted, 4 rejected with errors, then closed) and `Fundamentals/03_cross_cutting_concerns.md`.

## Reconnection and Resume

**Connections will drop**: deploys, load balancers, mobile networks, sleeping laptops. A robust client treats a drop as normal.

```arch
node c "Client" at 0,0 icon=client color=slate
node s "Server" at 1,0 icon=server color=purple
s -> c : "event seq=40"
s -> c : "event seq=41"
node drop "connection drops" at 0.5,1 shape=card color=red
c ..> drop ..> s
node replay "events 42,43,44 happen (replay buffer)" at 1.5,1 shape=card color=amber
s -> replay -> s
c -> s : "reconnect (after backoff)"
c -> s : "{'type':'resume', 'last_seq':41}"
s -> c : "42, 43, 44 (replay)"
s -> c : "45 ... (live)"
```

Ingredients:

1.  **Sequence numbers** on server events.
2.  A **replay buffer** of recent events on the server (or fetch from a durable log).
3.  A **resume handshake** carrying the client's `last_seq`.
4.  **Deduplication** on the client (`seq <= last_seq` is ignored) since replay and live may overlap.
5.  A **reset** message when the client is too far behind, so it refetches a snapshot instead of silently skipping events.
6.  **Exponential backoff with full jitter** when reconnecting, so 50,000 clients do not stampede the server the moment it returns.

Python lab 5 kills the connection 3 times during a 300-event stream and asserts every event arrives **exactly once, in order**; it also shows that without jitter 1000 clients hit the server in the same 10 ms window, versus 36 with jitter.

## Security

| Threat | Defence |
| :--- | :--- |
| **Cross-Site WebSocket Hijacking (CSWSH)**: browsers do **not** apply CORS to WebSockets and attach cookies to the handshake, so `evil.com` can open a socket to your server *as the logged-in user* | **Check `Origin`** against an allow-list; use tokens/tickets instead of ambient cookies |
| No `Authorization` header in the browser `WebSocket` <abbr title="Application Programming Interface">API</abbr> | See authentication options below |
| Eavesdropping / tampering | `wss://` (<abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>) only |
| Huge messages | Server-side max message size (1009) |
| Floods | Per-connection rate limit |
| Slowloris-style idle connections | Auth deadline, idle timeout, heartbeats |
| Injection through message content | Validate like any other input; escape when rendering |

**Authentication options** (Python lab 3 demonstrates A-C, Go lab 5 D):

| | Method | Pros | Cons |
| :--- | :--- | :--- | :--- |
| A | Token in the query string `?token=...` | Trivial | Ends up in **access logs**, browser history, referrers |
| B | Token in `Sec-WebSocket-Protocol` | Not in the URL | A hack; must not echo the token back |
| C | **First message** `{"type":"auth","token":...}` with a **deadline** | Simple, flexible | The socket exists unauthenticated until proven; enforce a short timeout (code 4401) |
| D | **One-time ticket**: `POST /ws-ticket` (normal Bearer auth) returns a random, single-use, 30 s ticket; connect with `?ticket=...` | A leaked URL is useless: burned or expired | Extra round trip and a ticket store |

Refusing during the **handshake** (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> 401/403) is cheapest: no socket is ever opened.

## Scaling WebSockets

The core problem: a WebSocket is **stateful**. Client A is on server 1, client B on server 2. When A speaks, server 1 does not know B exists.

```arch
%% caption: Each node knows only its own sockets; a broker carries room messages between nodes.
node br "Broker" at 1,0 icon=topic sub="Redis pub/sub / NATS / Kafka"
node n1 "Node 1" at 0,1 icon=server
node n2 "Node 2" at 2,1 icon=server
node a "Client A" at 0,2 icon=client
node b "Client B" at 1,2 icon=client
node c "Client C" at 3,2 icon=client
a <-> n1 : "ws"
b:T <-> n2:L : "ws"
c:T <-> n2:R : "ws"
n1:T -> br:L : "publish room:go"
br:B -> n1:R : "deliver room:go"
br:R -> n2:T : "deliver room:go"
n2:B -> b:R : "fan out to local sockets"
n2:B -> c:L
```

*   Every node **publishes** to a broker and **subscribes** to the rooms its local clients joined, then fans out to its own sockets. Go lab 5 builds exactly this with a `Broker` interface, and a message from a client on node 1 reaches a client on node 2 while a client in a different room on node 2 hears nothing.
*   **One goroutine/task per connection** is fine in Go and asyncio: 100k idle connections is normal on a tuned server (mind file descriptor limits and memory per connection).
*   **The hub pattern** (Go lab 3): one goroutine owns the rooms map (no mutex), each client has a `readPump` and a `writePump`, the hub never blocks on a client. The lab's goroutine leak check caught a real shutdown bug in the first draft.
*   **Load balancer checklist:** forward `Upgrade`/`Connection`; raise idle/read timeouts far above the default 60 s; <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> at the edge; **do not rely on sticky sessions for correctness** (a reconnect may land anywhere); drain nodes on deploy.
*   **Graceful deploys:** stop accepting, send close `1001` with a hint, let clients reconnect with jitter. Go lab 4 closes 20 connections concurrently in about 5 ms.
*   **Presence** ("who is online") and **state** (last event id, room membership) belong in the broker/datastore, not in one node's memory.

## Using It: Python

```python
# server: pip install websockets
import asyncio
from websockets.asyncio.server import serve

async def echo(ws):
    async for message in ws:            # str for text frames, bytes for binary frames
        await ws.send(f"echo: {message}")

async def main():
    async with serve(echo, "127.0.0.1", 8765, ping_interval=20, ping_timeout=20, max_size=1 << 20):
        await asyncio.Future()          # run forever
asyncio.run(main())
```

```python
# client
from websockets.asyncio.client import connect

async with connect("ws://127.0.0.1:8765") as ws:
    await ws.send("hi")
    print(await ws.recv())
```

## Using It: Go

Go's standard library has no WebSocket implementation; `github.com/coder/websocket` (formerly `nhooyr.io/websocket`) is the idiomatic choice (context-aware, works inside a normal `http.Handler`). Lab 1 builds one from scratch to show how small the protocol is.

```go
func handler(w http.ResponseWriter, r *http.Request) {
	c, err := websocket.Accept(w, r, &websocket.AcceptOptions{
		Subprotocols:   []string{"chat.v1"},
		OriginPatterns: []string{"app.example.com"},
	})
	if err != nil {
		return
	}
	defer c.CloseNow()
	c.SetReadLimit(64 << 10)

	for {
		ctx, cancel := context.WithTimeout(r.Context(), time.Minute)
		typ, data, err := c.Read(ctx)
		cancel()
		if err != nil {
			return // closed, timed out, or too big: the library already sent the right close frame
		}
		c.Write(r.Context(), typ, append([]byte("echo: "), data...))
	}
}
```

Rules that bite:

*   **One reader and one writer at a time** per connection: concurrent `Write` calls must be serialised (a per-client writer goroutine fed by a channel).
*   Control frames (ping/pong/close) are handled **while `Read` is running**. A client that never calls `Read` will not answer pings.
*   Always pass a context with a timeout; always `defer CloseNow()`.

## WebSockets vs the Alternatives

| | WebSockets | <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> streaming | Long polling | Webhooks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Direction | Both | Server to client | Both | Simulated | Server to server |
| Browser support | Native | Native | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>-Web (limited) | Native | n/a |
| Data | Text + binary | Text | Protobuf | Any | <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> |
| Auto-reconnect | You build it | Built in (`Last-Event-ID`) | You build it | You build it | Sender retries |
| Proxy/<abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr> friendliness | Needs config | Plain <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> | <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/2 needed | Plain <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> | Plain <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> |
| Best for | Chat, games, collab | Feeds, notifications | Service-to-service | Legacy | Cross-company events |

## Real-World Scenario & Architecture

**Scenario:** A real-time chat application where a user sends a message, and the server instantly broadcasts it to all other connected clients without them needing to refresh or poll.

```arch
node c1 "Client 1" at 0,0 icon=client color=slate
node s "Server" at 1,0 icon=server color=purple
node c2 "Client 2" at 2,0 icon=client color=blue
c1 -> s : "GET /chat (Upgrade)"
s -> c1 : "101 Switching Protocols"
c2 -> s : "GET /chat (Upgrade)"
s -> c2 : "101 Switching Protocols"
c1 -> s : "[WS] 'Hello everyone!'"
s -> c2 : "[WS] 'Client 1 says: Hello...'"
```

## Common Pitfalls

1.  **No `Origin` check** (CSWSH).
2.  **No heartbeats**, so dead connections leak until the process runs out of memory.
3.  **Unbounded per-client buffers**: one slow client takes down the server.
4.  **Not cleaning up** on disconnect (`finally` in Python, `defer` in Go): rooms and maps grow forever.
5.  **Trusting message content**: no <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> validation, no size or rate limits.
6.  **A token in the URL** that ends up in logs (use tickets).
7.  **Assuming delivery across reconnects**: <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> guarantees order per connection, not across connections. Use `seq` + resume.
8.  **Reconnecting without jitter**, causing a stampede after every outage.
9.  **Balancers with a 60 s idle timeout** killing quiet sockets: heartbeat more often.
10. **Using WebSockets where <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> or plain <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> would do**, taking on statefulness you did not need.

## Check Yourself

> ❓ **Question 1:** Why must a browser client's frames be masked, and does masking provide security against eavesdroppers?
>
> ❓ **Question 2:** A user's laptop lid closes mid-session. From the server's point of view, when and how does it find out?
>
> ❓ **Question 3:** `evil.com` runs JavaScript that opens `wss://yourapp.com/socket`. The user is logged in with a cookie. What happens without an Origin check, and does CORS help?
>
> ❓ **Question 4:** You run three chat servers behind a load balancer. Alice is on server 1 and Bob on server 2. How do they talk to each other?
>
> ❓ **Question 5:** A client reconnects after 10 seconds. How do you guarantee it misses no events and receives none twice?

**Answers**

1.  Masking stops a malicious page from crafting bytes that an intermediary proxy could interpret as an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> request (cache poisoning). It is **not** encryption: the key is sent with each frame. Confidentiality comes from `wss://`.
2.  Only through a **heartbeat**: a ping with no pong within the timeout. Without it, <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> may never report the loss and the connection leaks. (An abrupt close also shows up as code 1006 locally.)
3.  The browser opens the socket and attaches the user's cookie, so `evil.com` talks to your <abbr title="Application Programming Interface">API</abbr> as that user (CSWSH). **CORS does not apply to WebSockets**, so it does not help. Check `Origin` on the handshake and prefer tickets/tokens over ambient cookies.
4.  A **message broker** (Redis pub/sub, NATS, Kafka). Each server publishes local messages and subscribes to the rooms its own clients are in, delivering to its local sockets.
5.  Sequence numbers, a server-side replay buffer, a `resume{last_seq}` handshake, and client-side dedupe on `seq`. If the client is older than the buffer, send `reset` and make it refetch a snapshot.

## Hands-On Labs

Every lab is one file that runs on its own and prints what happens. Labs 1-2 teach the basics; labs 3-5 are advanced. **Python and Go cover different ground**, so do both.

Setup from the `API/` folder: `pip install -r requirements.txt`.

| # | Python (`WebSockets/labs/python/`) | You learn |
| :---: | :--- | :--- |
| 1 | `01_handshake_echo_and_frames.py` | The 101 handshake over a raw socket, `Sec-WebSocket-Accept`, a hand-built masked frame (RFC vector), an echo server and client, close codes |
| 2 | `02_chat_rooms_broadcast.py` | A <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> message protocol, rooms, broadcast, error replies for bad input, cleanup when clients vanish |
| 3 | `03_auth_origin_and_limits.py` | Origin allow-list, three auth methods compared (query, subprotocol, first message + deadline), max message size, close codes |
| 4 | `04_heartbeat_backpressure_rate_limit.py` | Dead peer detection measured, bounded per-client queues with drop-oldest, per-connection token bucket |
| 5 | `05_reconnect_and_resume.py` | Sequence numbers, replay buffer, resume handshake, dedupe, reset, backoff with jitter, exactly-once across 3 forced disconnects |

| # | Go (`WebSockets/labs/golang/`) | You learn |
| :---: | :--- | :--- |
| 1 | `01_handshake_and_frames_by_hand` | A WebSocket server from scratch: `http.Hijacker`, accept key, frame reader/writer, masking rules, and interop with a real library |
| 2 | `02_coder_websocket_json_rpc` | `websocket.Accept`, `wsjson`, request/response by `id`, subprotocol negotiation, read limits, close statuses |
| 3 | `03_hub_pattern_chat` | The hub + read/write pumps pattern, slow-client eviction, goroutine leak check, `-race` clean |
| 4 | `04_heartbeat_deadlines_graceful_close` | Ping-based dead peer detection, idle timeouts, concurrent graceful shutdown with close 1001 |
| 5 | `05_scaling_pubsub_and_tickets` | Multi-node fan-out through a `Broker` interface, one-time tickets, Origin check, load-balancer checklist |

```bash
python WebSockets/labs/python/05_reconnect_and_resume.py
go run -race ./WebSockets/labs/golang/03_hub_pattern_chat
```

## Exercises

1.  Add typing indicators to Python lab 2 (`{"type":"typing"}` broadcast, auto-expiring after 3 s).
2.  Replace the in-memory broker in Go lab 5 with Redis (`PUBLISH` / `SUBSCRIBE`) and run two processes.
3.  Add `seq` + `resume` (Python lab 5) to the Go hub so slow clients are **resumed** instead of only evicted.
4.  Build a tiny browser page (`new WebSocket("ws://localhost:8765")`) against Python lab 2 and watch the frames in the browser's Network tab.
5.  Put nginx in front of a lab server with `proxy_read_timeout 30s;` and reproduce the "idle connection killed by the balancer" pitfall, then fix it with heartbeats.
6.  Send Protobuf (`Protobuf/labs/`) instead of <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> in binary frames, and compare bytes sent.

## Where To Go Next

*   **`GraphQL/`**: subscriptions are GraphQL's WebSocket layer.
*   **`gRPC/`**: bidirectional streaming with typed contracts, deadlines and back-pressure built in.
*   **`Webhooks/`**: when the receiver is another server, not a browser.
*   **`Fundamentals/04_choosing_the_right_api.md`**: decision tree and interview questions.
