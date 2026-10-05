# Networking & Distributed Communication

Every API call, database connection, and "it works on my machine but not in prod" bug
eventually comes down to bytes moving between two machines. This chapter starts with
what those bytes actually are and how two computers agree to exchange them, then goes
as deep as an L5 interview loop expects: you are expected to know what happens on the
wire. When a distributed system misbehaves, the cause is often not the application
code but connection setup, congestion control, TLS, DNS, or load balancer behavior.
This file corrects several common simplifications; corrections are marked
**Precision note**. Sections 7–9 measure the protocol's behaviour with programs you
can run: the cost of a connection, the 40 ms Nagle stall, what each failure looks like to a
client, and head-of-line blocking under packet loss. It opens with what a network is, what its layers and devices are,
and how a packet actually gets from one program to another, and it closes with a
side-by-side breakdown of what Junior through Staff+ engineers are expected to know
about this material, just before the interview checklist.

## Foundations — What Is a Computer Network, and How Does It Work?

### Why Networks Exist

The first computers were islands. Moving data from one to another meant carrying a
tape or a stack of punched cards across the room. Two pressures ended that: expensive
machines that many people wanted to *share* (a university had one big computer and
hundreds of terminals), and people who wanted to *communicate* through their machines
(email was one of the first popular network applications). Two design decisions made
in that era still shape every packet you send:

- **Packet switching instead of circuit switching.** The telephone network reserved a
  dedicated circuit for the whole length of a call, used or not. Early computer
  networks (ARPANET, 1969) instead chopped data into small, independently addressed
  **packets** and let many conversations share the same wires, one packet at a time.
  Bursty computer traffic wastes a reserved circuit; shared links with packets don't.
  The price is that nothing is reserved: packets can be delayed, dropped, duplicated
  or reordered when links get busy. §1–§2 are about living with that.
- **A network of networks.** Instead of one giant network, the Internet connects
  thousands of independently run networks (a university, an ISP, Google) through a
  common protocol, **IP**. No one operates "the Internet" as a whole; each network
  runs its own piece and agrees on how to hand packets to its neighbours. §4's
  anycast and BGP only make sense with that picture in mind.

Everything in this file is a more precise version of one of those two moves: *share
unreliable links among many conversations*, and *agree on protocols so machines that
were built and run by different people can still talk*.

### What a Network Actually Is

A **computer network** is a set of machines (**nodes**) joined by **links** (copper,
fibre, radio) that exchange data by following shared **protocols**. A protocol is an
agreement about message format and behaviour: what the bytes of a message mean, who
speaks first, what to do when a reply doesn't arrive. The network does two jobs at
once, exactly as an OS does for one machine:

1. **Delivery** — get bytes from one program to another program on a different
   machine, across links and devices that neither program controls.
2. **Abstraction** — hide the mess underneath. Your code doesn't know whether its
   bytes travel over Wi-Fi, fibre under the Atlantic, or a satellite; it writes to a
   **socket** and reads a reliable stream of bytes back. Each layer below turns an
   unreliable service into a more useful one.

### Client and Server, Addresses and Ports

**Client and server, in one picture.** Almost everything in this file is two
programs on two machines (or two processes on one machine) talking: one **client**
that initiates a request, one **server** that listens and responds. "The network" is
everything that carries bytes between them.

**Addresses and ports.** An **IP address** identifies a machine (or a machine's
network interface) — like a street address. A **port** (a number 0–65535) identifies
*which program* on that machine a message is for — like an apartment number at that
address. A server "listens" on a port (e.g. a web server on port 443); a client
connects to `ip:port`.

**Packets: the network moves chunks, not streams.** Data doesn't travel as one
continuous stream — it's broken into **packets**, small chunks that each carry a bit
of your data plus headers saying where they're from and where they're going. Packets
for the same conversation can even take different physical routes and arrive out of
order; the protocols below exist largely to hide that from you.

### The Core Components: Layers and Devices

Networking is built as a stack of **layers**. Each layer offers one service to the
layer above and uses only the service of the layer below, so Wi-Fi can be swapped for
Ethernet without touching HTTP. The Internet uses the four-layer **TCP/IP model**; the
seven-layer **OSI model** is the numbering people still use in conversation ("an L4
load balancer", "an L7 proxy"), which is why both columns appear here:

| TCP/IP layer (OSI number) | Responsible for | Unit of data | Addresses by | Examples | Covered deeper in |
|---|---|---|---|---|---|
| **Application** (L5–L7) | What the bytes *mean* to programs | Message | Names, URLs | HTTP, DNS, gRPC, SMTP; TLS sits just below HTTP | §0, §3, §5, §6 |
| **Transport** (L4) | Program-to-program delivery; reliability, ordering, flow and congestion control (TCP) or none of that (UDP) | Segment (TCP) / datagram (UDP) | Port | TCP, UDP, QUIC (on top of UDP) | §1, §2, §3 |
| **Internet / Network** (L3) | Machine-to-machine delivery across many networks; routing | Packet | IP address | IPv4, IPv6, ICMP, BGP routing | This section, §4 (anycast) |
| **Link + Physical** (L2 + L1) | One hop across one physical network, and the signals on the wire or radio | Frame | MAC address | Ethernet, Wi-Fi, ARP | This section |

**Precision note:** the OSI model is a teaching and vocabulary model; the Internet was
never built on its seven layers. Real protocols blur the lines: TLS runs between TCP
and HTTP, and QUIC implements transport features (reliability, congestion control)
in user space on top of UDP. Say "L4" and "L7" freely, but don't argue about which
OSI layer TLS "really" belongs to.

The layers are software. They run on a handful of kinds of **devices**:

| Device / component | Works at | What it does | Covered deeper in |
|---|---|---|---|
| **Network interface card (NIC)** | L1–L2 | Turns frames into signals and back; every NIC has a MAC address | [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §7 |
| **Switch** | L2 | Forwards frames between machines on the *same* local network by MAC address | This section |
| **Router** | L3 | Forwards packets *between* networks by destination IP, using a routing table | This section, §4 |
| **NAT gateway** | L3/L4 | Rewrites private addresses to a shared public one (your home router does this) | This section |
| **Firewall** | L3–L7 | Allows or drops traffic by address, port, or content | [Security](../SystemDesign/building_blocks/14_security.md) |
| **DNS resolver** | L7 | Turns names into IP addresses | §6 |
| **Load balancer / reverse proxy** | L4 or L7 | Spreads connections or requests over many servers | §4 |
| **The OS network stack** | L3–L4 | Implements IP, TCP and UDP inside the kernel and exposes sockets | [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §4, §7 |

### How the Pieces Fit Together: Encapsulation

When a program sends data, each layer on the way down wraps what it was handed in
its own header — **encapsulation**. An HTTP request becomes the payload of a TCP
segment (header adds source and destination *ports*), which becomes the payload of an
IP packet (header adds source and destination *IP addresses*), which becomes the
payload of an Ethernet frame (header adds source and destination *MAC addresses* for
this one hop). Every device only reads the layers it needs: a switch reads the frame
header, a router reads the IP header, and only the two end machines unwrap all the
way up to HTTP.

```arch
%% caption: Each layer wraps the one above in its own header; switches read only the frame, routers read up to IP, and only the two end hosts unwrap all the way to HTTP.
grid 170x100
group ha "Sending host" color=blue icon=desktop
node a7 "HTTP request" at 0,0 in ha sub="application message"
node a4 "TCP segment" at 0,1 in ha sub="+ ports, seq numbers"
node a3 "IP packet" at 0,2 in ha sub="+ source/dest IP"
node a2 "Ethernet frame" at 0,3 in ha sub="+ MAC addresses"
node sw "Switch" at 1,3 icon=network sub="reads MAC only"
group rt "Router" color=purple icon=network
node r3 "Routing decision" at 2,2 in rt sub="longest-prefix match on dest IP"
node r2 "Link layer" at 2,3 in rt sub="strip old frame, build new one"
group hb "Receiving host" color=green icon=server
node b7 "HTTP request" at 3,0 in hb sub="handed to the server program"
node b4 "TCP segment" at 3,1 in hb sub="port picks the socket"
node b3 "IP packet" at 3,2 in hb sub="dest IP is mine"
node b2 "Ethernet frame" at 3,3 in hb sub="dest MAC is mine"
a7 -> a4 -> a3 -> a2
a2 -> sw : "frame"
sw -> r2 : "frame"
r2 -> r3
r3 -> b2 : "new frame"
b2 -> b3 -> b4 -> b7
```

Headers cost bytes, which is where two numbers you'll meet later come from: a
standard Ethernet frame carries at most 1500 bytes of payload (the **MTU**); after a
20-byte IPv4 header and a 20-byte TCP header, 1460 bytes remain for your data (the
**MSS**, maximum segment size). A 1 MB response is therefore about 700 segments, and
§2's congestion window is counted in those segments.

### How a Packet Finds Its Way: Routing, ARP and NAT

- **Subnets and CIDR.** An IPv4 address is 32 bits, written as four numbers
  (`192.168.1.20`). `192.168.1.0/24` means "every address whose first 24 bits match":
  one local network (a **subnet**) of 256 addresses. Machines on the same subnet talk
  directly through a switch; anything else goes to the **default gateway**, a router.
- **Routing.** Each router holds a **routing table** of prefixes and next hops, and
  forwards each packet to the entry with the **longest matching prefix**. Inside one
  organisation, routes are computed by interior protocols (OSPF, IS-IS); *between*
  the independently run networks of the Internet (autonomous systems), routes are
  exchanged with **BGP**, which is policy-driven (who pays whom), not shortest-path.
- **ARP.** IP addresses name machines; Ethernet delivers to MAC addresses. **ARP**
  asks the local network "who has 192.168.1.1?" and caches the MAC that answers, so
  the sender knows which frame header to write for the next hop. (IPv6 uses Neighbor
  Discovery for the same job.)
- **NAT.** IPv4 has only about 4.3 billion addresses, which ran out years ago. Most
  devices use **private** ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  and a **NAT** router rewrites their source address and port to one shared public
  address, keeping a table to map replies back. This is why a server can't simply
  open a connection *to* your laptop, and why peer-to-peer apps need NAT traversal.
- **IPv6** fixes the shortage with 128-bit addresses (`2001:db8::1`) and removes the
  need for NAT, though most networks still run both side by side.

### TCP vs. UDP — the Two Transport Building Blocks

- **TCP** is a *reliable, ordered, connected* stream: before any data moves, both
  sides agree to talk (a **handshake**, §1); every packet is acknowledged, lost
  packets are retransmitted, and your application reads bytes in the exact order they
  were sent. This reliability costs setup time and a little overhead on every
  packet — the cost §2's congestion control is all about managing.
- **UDP** is *fire-and-forget*: send a packet, no handshake, no guarantee it arrives
  or arrives in order. Cheaper and faster to start, but your application must handle
  loss and reordering itself if it cares. QUIC (§3, the protocol behind HTTP/3) is
  built on UDP specifically to get TCP-like reliability without TCP's TCP-specific
  head-of-line blocking problem.

| Property | TCP | UDP |
|---|---|---|
| Connection setup | Yes, a 3-way handshake (1 RTT) | None |
| Delivery | Reliable: acknowledged and retransmitted | Best effort: may be lost |
| Ordering | In order, as one byte stream | Each datagram independent; may reorder |
| Message boundaries | None: a stream (two `send()`s may arrive in one `recv()`) | Preserved: one datagram in, one out |
| Flow and congestion control | Built in | None (the application's job) |
| Typical uses | HTTP/1.1 and HTTP/2, gRPC, databases, SSH | DNS, video calls, games, QUIC/HTTP/3 |

**Precision note:** "TCP is slow, UDP is fast" is too simple. On a healthy network a
long-lived TCP connection moves bulk data at line rate. UDP's real advantages are no
handshake, no head-of-line blocking between independent messages, and the freedom to
build your own reliability (which is exactly what QUIC does).

### HTTP, TLS and DNS in One Paragraph Each

**HTTP, in one exchange.** HTTP is a text-shaped (in HTTP/1.1) *request/response*
protocol that normally runs on top of TCP: the client sends a request (a method like
`GET`/`POST`, a path, headers, maybe a body); the server sends back a response (a
status code like `200`/`404`/`500`, headers, a body). Nearly every web API you've
used is "HTTP request/response, with JSON as the body." §3 covers how this evolved
across three major versions.

**Encryption, in one sentence.** **TLS** (what makes `http://` into `https://`) wraps
that same request/response exchange in encryption, after its own handshake (§5)
negotiates a shared secret key that only the two endpoints know.

**DNS, in one sentence.** You rarely connect to a raw IP address — you connect to a
name (`google.com`), and **DNS** (§6) is the system that turns that name into an IP
address before the TCP handshake can even begin.

### Sockets: Where the Network Meets Your Program

A **socket** is the operating system's handle for one end of a conversation. A TCP
connection is identified by its **4-tuple** (source IP, source port, destination IP,
destination port), which is how one server port can hold 100,000 connections at once:
each has a different client IP or port. The server side calls `bind` (claim a port),
`listen` (ask the kernel to queue incoming connections) and `accept` (take one that
already finished its handshake); the client calls `connect`. After that both sides
just `send` and `recv` bytes. This is runnable as-is with Python's standard library:

```python
import socket
import threading

def serve_once(listener: socket.socket) -> None:
    conn, peer = listener.accept()        # returns once the kernel finished a 3-way handshake
    with conn:
        data = conn.recv(1024)            # read whatever bytes have arrived (a stream, not messages)
        conn.sendall(b"echo: " + data)    # write() returns once bytes are in the kernel send buffer

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # AF_INET = IPv4, SOCK_STREAM = TCP
listener.bind(("127.0.0.1", 0))           # port 0: let the OS pick a free port
listener.listen()                         # now the kernel queues incoming connections
host, port = listener.getsockname()
server = threading.Thread(target=serve_once, args=(listener,))
server.start()

with socket.create_connection((host, port)) as client:   # connect(): the SYN / SYN-ACK / ACK happens here
    print("client", client.getsockname(), "-> server", client.getpeername())
    client.sendall(b"hello")
    print(client.recv(1024).decode())

server.join()
listener.close()

# UDP for contrast: no listen/accept/connection — each sendto() is one independent datagram.
rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx.bind(("127.0.0.1", 0))
tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tx.sendto(b"ping", rx.getsockname())
data, sender = rx.recvfrom(1024)
print("udp got", data, "from", sender)
tx.close(); rx.close()
```

The client's port in the first printed line is an **ephemeral port** the OS picked
for it; §1's TIME_WAIT discussion is about running out of exactly those. Everything
that makes this scale to 100,000 connections (non-blocking sockets, `epoll`) is in
[Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §4.

### Latency, Bandwidth and Throughput

- **Latency** is how long one bit takes to get there; **RTT** (round-trip time) is
  there and back. It is bounded by physics: light in fibre covers roughly 200 km per
  millisecond, so New York to London (about 5,600 km) can never be faster than about
  28 ms one way, about 56 ms round trip; real paths are longer (typically 70+ ms RTT).
- **Bandwidth** is how many bits per second a link can carry; **throughput** is what
  you actually achieve, which is often limited by latency rather than bandwidth.
- **Bandwidth-delay product (BDP)** = bandwidth × RTT: how much data must be "in
  flight" to keep the pipe full. It connects the two ideas and is the reason TCP's
  window sizes (§1–§2) matter so much on long paths.

For a small request, latency dominates: saving one round trip on a 100 ms path saves
more time than doubling bandwidth. That is why every protocol improvement in §3 and
§5 (TLS 1.3, QUIC, 0-RTT) is framed as "RTTs saved".

**Try it: spend a latency budget.** Set the budget to 100 ms and read off how many operations of each kind fit: hundreds of same-datacenter round trips, not one trip across an ocean. That asymmetry is why moving the data closer (CDNs, regional replicas) and making fewer round trips (connection reuse, TLS 1.3, QUIC) beat buying more bandwidth.

<div class="lab" data-viz="cs-latency"></div>

### Design Philosophies Behind the Internet

| Principle | What it says | Where you see it |
|---|---|---|
| **Best effort** | The network (IP) promises only to *try*; loss, delay and reordering are normal | Why TCP exists (§1), why retries need idempotency |
| **End-to-end principle** | Put reliability and intelligence in the endpoints, keep the middle simple | TCP and TLS run only on the two hosts; routers just forward |
| **Layering** | Each layer hides the one below behind a narrow interface | HTTP runs unchanged over Wi-Fi, fibre, or 5G |
| **Stateless core, stateful edges** | Routers keep no per-conversation state; hosts, NATs, proxies and load balancers do | Why a NAT or L7 proxy failure drops connections while a router failure just reroutes |
| **Robustness principle** ("be conservative in what you send, liberal in what you accept") | Tolerate imperfect peers | Historically helpful; RFC 9413 (2023) argues it also let bugs ossify, which is why QUIC encrypts almost all of its headers |

**Precision note:** "the middle stays simple" is an ideal, not today's reality.
Middleboxes (NATs, firewalls, load balancers, corporate proxies) inspect and rewrite
traffic, and many drop anything unfamiliar. That **ossification** is why TCP
extensions are hard to deploy and why QUIC was built on UDP in user space.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| IP address | Identifies a machine on the network |
| Port | Identifies which program on that machine |
| Packet | A chunk of data plus routing headers; the unit the network actually moves |
| Protocol | An agreement about message format and behaviour |
| Layer (L3 / L4 / L7) | Network (IP), transport (TCP/UDP), application (HTTP) |
| MAC address | A NIC's hardware address, used for one hop on a local network |
| Router / switch | Forwards between networks by IP / within one network by MAC |
| NAT | Rewrites private addresses to a shared public one |
| MTU / MSS | Largest frame payload (usually 1500 B) / largest TCP payload (usually 1460 B) |
| RTT (round-trip time) | Time for a packet to reach the other side and its reply to come back |
| Bandwidth-delay product | Bandwidth × RTT: bytes in flight needed to fill the path |
| Handshake | Messages exchanged before data flows, to agree on connection parameters |
| Socket | A local endpoint (IP + port + protocol) your program reads/writes through |
| 4-tuple | Source IP, source port, destination IP, destination port: identifies a TCP connection |

With the layers, the devices and that vocabulary in place, the rest of this chapter
is the precise, L5-depth version of each piece. Section 0 below is the classic "walk
me through what happens when..." interview answer, using every layer above in
sequence.

## 0. What Happens When You Type `google.com` and Press Enter

The most-asked networking question. Walk it layer by layer and stop to go deeper wherever the interviewer pushes.

```text
1. Browser  : parse URL, check HSTS preload (force https), check caches
2. DNS      : browser cache → OS resolver cache → recursive resolver (ISP / 8.8.8.8)
              recursive resolver → root → .com TLD → google.com authoritative → A/AAAA
              (answers cached per TTL; Google uses anycast + geo-aware answers)
3. TCP      : SYN → SYN-ACK → ACK       (1 RTT)      — or QUIC for HTTP/3
4. TLS 1.3  : ClientHello(key_share) → ServerHello(key_share) + encrypted cert
              + CertificateVerify + Finished → client Finished   (1 RTT)
5. HTTP     : GET / over HTTP/2 (or HTTP/3); headers compressed (HPACK/QPACK)
6. Edge     : anycast IP lands at a nearby Google front end (GFE); L4 then L7
              load balancing; TLS terminated at the edge; request forwarded
              over Google's backbone to a backend
7. Backend  : search frontends fan out to many index shards, merge, rank
8. Response : HTML streamed back; browser parses, builds DOM/CSSOM, fetches
              subresources (often from cache/CDN), runs JS, paints
```

Numbers to mention: DNS usually a few ms when cached, tens of ms uncached; a same-continent RTT is ~20-80 ms; TCP+TLS 1.3 costs 2 RTTs on a new connection, HTTP/3 (QUIC) combines them into 1 RTT, and resumed QUIC sessions can send data in 0-RTT.

### Where Each Step Fails, and What You'd See

A strong answer doesn't just list the steps; it knows how each one breaks, because
that is what the follow-up questions (and real incidents) are about:

| Step | Typical failure | Symptom a user or dashboard shows |
|---|---|---|
| DNS | Resolver down, expired record, bad TTL during a migration | "Server not found", or traffic still going to an old IP long after a change |
| TCP connect | Server not listening, firewall drops the SYN, SYN backlog full | "Connection refused" (RST came back) vs. a connect *timeout* (nothing came back) |
| TLS | Expired or wrong-host certificate, clock skew on the client, no shared cipher | Browser certificate warning; handshake failures spike in edge metrics |
| HTTP | Backend overloaded, bad deploy, LB has no healthy backends | 5xx: 502/503/504 from the proxy vs. 500 from the application |
| Network path | Packet loss, congestion, a BGP change | High tail latency, retransmissions, one region affected |

"Connection refused" versus "connection timed out" is a favourite follow-up: refused
means a machine answered with a TCP reset (nothing listening on that port); a timeout
means nothing answered at all (a firewall silently dropping, a dead host, or a
routing problem).

<div class="lab" data-viz="flow-web-request"></div>

## 1. TCP Fundamentals Before Congestion Control

### Connection lifecycle
- **Three-way handshake:** `SYN` (client ISN) → `SYN-ACK` (server ISN, ack client) → `ACK`. The server holds half-open state after SYN, which is what a **SYN flood** exhausts; **SYN cookies** encode that state into the ISN so no memory is held.
- **Teardown:** `FIN`/`ACK` in each direction. The side that closes first enters **TIME_WAIT** for 2×MSL (commonly 60 s on Linux) so delayed segments from the old connection can't corrupt a new one with the same 4-tuple. A proxy that opens many short outbound connections can run out of ephemeral ports because of TIME_WAIT: use connection pooling / keep-alive.
- **Flow control vs congestion control:** *flow control* protects the RECEIVER (the advertised receive window says how much it can buffer); *congestion control* protects the NETWORK (the congestion window, cwnd). The sender may transmit min(rwnd, cwnd).
- **Nagle's algorithm + delayed ACKs** can add ~40 ms latency to small request/response writes. Latency-sensitive RPC stacks set `TCP_NODELAY`.

### Reliability Mechanics: Sequence Numbers, ACKs, Retransmission

How does TCP turn an unreliable packet service into a reliable byte stream?

- **Sequence numbers** number every *byte* of the stream (starting from a random
  initial sequence number, the ISN, chosen in the handshake). The receiver uses them
  to put segments back in order and drop duplicates.
- **Cumulative ACKs:** the receiver acknowledges "I have every byte up to N". With
  **SACK** (selective acknowledgement, on by default in modern stacks) it can also say
  "and I have these later ranges", so the sender resends only the holes.
- **Retransmission timeout (RTO):** the sender keeps a smoothed estimate of the RTT
  and its variance; if no ACK arrives within the RTO, it resends. Linux's minimum RTO
  is 200 ms, which is why one lost packet can cost a latency-sensitive request far
  more than one RTT.
- **Fast retransmit:** three duplicate ACKs ("still waiting for byte N") signal a
  single loss before the timer fires, so the sender resends immediately. Tail losses
  (the last packets of a response, which produce no duplicate ACKs) are the hard case;
  Linux uses tail loss probes and RACK-TLP to recover them faster.

### TCP States You'll See in `ss` or `netstat`

| State | Meaning | When it's a problem |
|---|---|---|
| `LISTEN` | Server socket waiting for connections | Missing: the service isn't bound to that port |
| `SYN_SENT` / `SYN_RECV` | Handshake in progress | Many `SYN_RECV`: a SYN flood or a full accept queue |
| `ESTABLISHED` | Connection open | Growing without bound: a connection leak |
| `CLOSE_WAIT` | Peer closed; *your* program hasn't called `close()` yet | Piling up: an application bug that leaks sockets |
| `TIME_WAIT` | You closed first; waiting 2×MSL | Tens of thousands on a proxy: ephemeral port exhaustion, use pooling |

`CLOSE_WAIT` piling up is almost always your bug, not the network's: the other side
said goodbye and your code never closed its end.

<div class="lab" data-viz="flow-tcp"></div>

## 2. TCP Congestion Control (CUBIC vs. BBR)

TCP uses a **Congestion Window (cwnd)** to decide how much unacknowledged data can be in flight.

```arch
%% caption: CUBIC cuts its window whenever it sees loss; BBR measures bandwidth and RTT and paces to that model instead.
grid 200x100
group cubic "CUBIC: loss-based" color=orange icon=warn
node c1 "Slow Start" at 0,0 in cubic sub="exponential growth from initial window"
node c2 "Congestion Avoidance" at 0,1 in cubic sub="cubic growth"
node c3 "Packet loss detected!" at 0,2 in cubic color=red
group bbr "BBR: model-based" color=green icon=gauge
node b1 "Probe bandwidth" at 1.5,0 in bbr
node b2 "Measure min RTT" at 1.5,1 in bbr
node b3 "Build pipe model" at 1.5,2 in bbr
c1 -> c2 -> c3
c3:L -> c2:L : "multiplicative decrease ×0.7"
b1 -> b2 -> b3
b3:R -> b1:R : "pace sending rate to the model"
```

<div class="lab" data-viz="tcp-bbr"></div>

### The Classic Loss-Based Family: Reno and CUBIC
*   **Slow Start:** cwnd starts at the **initial window** and roughly doubles every RTT until a threshold or loss. **Precision note:** the initial window is not 1 packet on modern stacks; Linux has used **10 segments** (IW10, RFC 6928) for over a decade. That is why small responses (~14 KB) fit in the first flight.
*   **Congestion Avoidance:** Reno grows cwnd linearly (+1 MSS per RTT); **CUBIC** (the Linux default) grows along a cubic curve centered on the window size where the last loss happened, which recovers faster on high-bandwidth links.
*   **On loss:** Reno halves cwnd. **Precision note:** CUBIC's multiplicative decrease uses β = 0.7, i.e. it cuts the window by 30%, not 50%.
*   **The weakness:** loss-based algorithms treat *any* loss as congestion. On long, high-bandwidth paths with random (non-congestion) loss, such as cellular or intercontinental links, they back off unnecessarily. On routers with huge buffers they fill buffers before seeing loss, causing **bufferbloat** latency.

### Google BBR (Model-Based)
*   **BBR** = Bottleneck Bandwidth and Round-trip propagation time.
*   It estimates the path's **bottleneck bandwidth** (max recent delivery rate) and **minimum RTT** (propagation delay), and paces sending to roughly that rate, periodically probing for more bandwidth and draining queues to re-measure min RTT.
*   **Precision note:** BBR aims to operate near the optimal point (full bandwidth, minimal queueing). It does not "perfectly" avoid overflowing buffers. BBRv1 was criticized for high retransmission rates and unfairness to CUBIC flows in shallow buffers; **BBRv2/v3** added loss and ECN signals to address this.
*   **L5 Insight:** BBR is a **sender-side** change (no client update needed). Google reported large throughput and latency improvements for YouTube and Google.com traffic, especially on lossy long-distance paths. It's a strong answer for "improve a global upload/download service" — framed as "measure; BBR often helps on lossy high-RTT paths," not as a guaranteed win.

### The Bandwidth-Delay Product, Worked

Why does congestion control matter so much more on long paths? To keep a link busy,
the sender must have a full **bandwidth-delay product** of data unacknowledged at
once, and slow start needs several round trips to grow the window that large. The
script below (standard library only, runnable as-is) computes both, then isolates the
effect of CUBIC's gentler back-off in a deliberately simplified model:

```python
import math

MSS = 1460            # bytes of payload per TCP segment on a 1500-byte-MTU Ethernet path
IW = 10               # Linux initial congestion window (IW10, RFC 6928)

def bdp_bytes(bandwidth_bps: float, rtt_s: float) -> float:
    """Bandwidth-delay product: how many bytes must be in flight to fill the pipe."""
    return bandwidth_bps / 8 * rtt_s

def slow_start_rtts(target_segments: float) -> int:
    """RTTs of slow start (cwnd doubles each RTT) to grow from IW to the target."""
    return max(0, math.ceil(math.log2(target_segments / IW)))

for name, bw, rtt in [("same-region", 1e9, 0.002),
                      ("cross-country", 1e9, 0.070),
                      ("intercontinental", 1e9, 0.150)]:
    bdp = bdp_bytes(bw, rtt)
    segs = bdp / MSS
    rounds = slow_start_rtts(segs)
    print(f"{name:17s} RTT={rtt*1000:5.0f} ms  BDP={bdp/1e6:6.2f} MB "
          f"(~{segs:6.0f} segments)  slow start needs ~{rounds:2d} RTTs = {rounds*rtt*1000:5.0f} ms")

# Toy congestion-avoidance comparison: +1 segment per RTT, loss every time cwnd hits 100.
for name, beta in [("Reno  (x0.5)", 0.5), ("CUBIC-style decrease (x0.7)", 0.7)]:
    cwnd, sent = 50.0, 0.0
    for _ in range(200):
        sent += cwnd
        cwnd = cwnd * beta if cwnd >= 100 else cwnd + 1
    print(f"{name:28s} average cwnd over 200 RTTs = {sent/200:5.1f} segments")
```

Output:

```text
same-region       RTT=    2 ms  BDP=  0.25 MB (~   171 segments)  slow start needs ~ 5 RTTs =    10 ms
cross-country     RTT=   70 ms  BDP=  8.75 MB (~  5993 segments)  slow start needs ~10 RTTs =   700 ms
intercontinental  RTT=  150 ms  BDP= 18.75 MB (~ 12842 segments)  slow start needs ~11 RTTs =  1650 ms
Reno  (x0.5)                 average cwnd over 200 RTTs =  74.5 segments
CUBIC-style decrease (x0.7)  average cwnd over 200 RTTs =  82.1 segments
```

Three lessons an interviewer is fishing for: a new connection on a long path spends
its first second or more *below* full speed, so **reuse connections** (keep-alive,
pooling, HTTP/2 multiplexing) instead of opening new ones; a single loss on a
high-BDP path is expensive, which is why the size of the back-off (β) and BBR's
model-based approach matter; and the receive window and socket buffers must be at
least the BDP, or the receiver, not the network, caps throughput. (The toy model
keeps linear growth for both and changes only β; real CUBIC also grows along a cubic
curve, which widens the gap on high-BDP paths.)

**Try it: fill the pipe.** Start with a window of 4 packets on a 100 Mbps link with a 100 ms RTT: the sender fires four packets, then sits idle for a whole round trip waiting for ACKs, and uses under 1% of the link. Raise the window towards the bandwidth-delay product and the gaps close. Add 3% loss and watch duplicate ACKs stall the window until the missing packet is retransmitted, which is exactly the event loss-based congestion control reacts to.

<div class="lab" data-viz="cs-tcp-window"></div>

## 3. The HTTP Evolution

```arch
%% caption: HTTP/1.1 serializes requests; HTTP/2 multiplexes streams but one TCP loss stalls them all; HTTP/3 gives each stream its own recovery.
grid 150x80
group h1 "HTTP/1.1" color=slate
node a "Request 1" at 0,0 in h1
node b "Request 2" at 2,0 in h1
group h2 "HTTP/2 (TCP)" color=amber
node c "Stream A" at 0,1 in h2
node d "Stream B" at 2,1 in h2
node e "Single TCP conn" at 1,2 in h2 color=amber
node f "Head-of-Line Block" at 1,3 in h2 color=red
group h3 "HTTP/3 (QUIC over UDP)" color=green
node g "Stream A" at 0,4 in h3
node h "Stream B" at 2,4 in h3
node i "Independent UDP streams" at 1,5 in h3 color=green
node j "No HoL blocking" at 1,6 in h3 color=green
a -> b : "wait for response 1"
c -> e
d -> e
e -> f : "TCP loss blocks ALL"
g -> i
h -> i
i -> j : "loss in A doesn't block B"
```

### HTTP/1.1 (Application-Level Head-of-Line Blocking)
*   Text-based. Keep-Alive reuses a TCP connection, but responses on one connection are serialized: request 2 waits for response 1. (Pipelining existed but was broken by proxies and disabled by browsers.)
*   *Workaround:* browsers open ~6 connections per origin; sites used domain sharding and sprite sheets.

### HTTP/2 (Multiplexing, TCP Head-of-Line Blocking)
*   Binary framing. Many concurrent streams share **one** TCP connection; headers compressed with HPACK. gRPC runs on HTTP/2.
*   *The flaw:* TCP delivers bytes in order. If one packet is lost, **all** streams wait for its retransmission even if their own data arrived. On lossy networks HTTP/2 over one connection can be slower than HTTP/1.1 over six.

### HTTP/3 (QUIC)
*   Runs over **UDP**, with reliability, ordering (per stream), and congestion control implemented in user space.
*   Loss on stream A no longer blocks stream B: transport head-of-line blocking is gone.
*   **Handshake:** QUIC integrates TLS 1.3 into its transport handshake, so a **new** connection is established in **1 RTT** (vs 2 RTTs for TCP + TLS 1.3). **Precision note:** **0-RTT** only applies when **resuming** a previous session with a cached key; 0-RTT data is replayable, so only idempotent requests should use it.
*   **Connection migration:** connections are identified by connection IDs, not the IP/port 4-tuple, so a phone switching from Wi-Fi to cellular keeps its connection.

### HTTP Semantics Interviewers Probe

The versions above change *how* bytes move; the semantics stay the same, and API
design questions lean on them constantly:

| Method | Safe (no side effects) | Idempotent (repeat = same result) | Typical use |
|---|---|---|---|
| `GET`, `HEAD` | Yes | Yes | Read a resource |
| `PUT` | No | Yes | Replace a resource at a known URL |
| `DELETE` | No | Yes | Remove a resource (a repeat finds it already gone) |
| `POST` | No | **No** | Create, or any non-idempotent action; make retries safe with an idempotency key |
| `PATCH` | No | Not guaranteed | Partial update |

- **Status code classes:** `2xx` success, `3xx` redirect (`301` permanent, `304` not
  modified), `4xx` the *client's* fault (`400`, `401` unauthenticated, `403`
  forbidden, `404`, `409` conflict, `429` rate limited), `5xx` the *server's* fault
  (`500`, `502` bad gateway, `503` unavailable, `504` gateway timeout). Retrying a
  `4xx` unchanged is pointless; retrying a `503` with backoff is reasonable.
- **Caching:** `Cache-Control` (`max-age`, `no-store`, `private`) says who may cache
  and for how long; `ETag` plus `If-None-Match` lets a client revalidate and get a
  bodiless `304` if nothing changed. CDNs are built on exactly these headers.
- **Connection reuse:** HTTP/1.1 keeps connections open by default (keep-alive);
  HTTP/2 and HTTP/3 multiplex many requests over one, which is why the BDP lesson
  above favours them.

### Real-time delivery options (see [Real-Time Communication and Collaboration](../SystemDesign/building_blocks/22_realtime_and_collaboration.md))
| Mechanism | Direction | Notes |
|---|---|---|
| Short polling | client pulls | Simple, wasteful |
| Long polling | client pulls, server holds until data | Works everywhere; one request per message |
| Server-Sent Events | server → client over HTTP | Auto-reconnect, text only, one direction |
| WebSocket | full duplex after HTTP Upgrade | Chat, games, collaboration; needs sticky connection handling on LBs |

## 4. Advanced Load Balancing Architectures

```arch
%% caption: An L4 balancer forwards packets, an L7 one terminates TLS and reads HTTP; with Direct Server Return the backend answers the client itself.
node client "Client" at 1,0 icon=client
node lb "Load Balancer" at 1,1 icon=lb
node b1 "Backend 1" at 0,2 icon=server sub="L4: NAT, forward packets"
node b2 "Backend 2" at 2,2 icon=server sub="L7: terminate TLS, read HTTP"
group dsr "DSR: Direct Server Return" color=purple icon=network
node client2 "Client" at 0,3 in dsr icon=client
node lb2 "LB" at 2,3 in dsr icon=lb sub="forward only"
node b3 "Backend 3" at 2,4 in dsr icon=server
client -> lb : "request"
lb -> b1 : "L4"
lb -> b2 : "L7"
client2 -> lb2
lb2 -> b3 : "modify MAC only"
b3 -> client2 : "5GB response DIRECTLY to client" thick
```

### Layer 4 (Transport) vs. Layer 7 (Application)
*   **L4 load balancer:** Decides on IP/port (5-tuple). Forwards packets (NAT, encapsulation, or MAC rewrite) without reading HTTP. Very fast, protocol-agnostic, can't route by URL/header. Google's **Maglev** is a software L4 LB using consistent hashing so connections survive LB changes.
*   **L7 load balancer / reverse proxy:** Terminates TCP and TLS, reads HTTP, opens its own connection (usually pooled) to the backend. Enables path/header routing, retries, rate limiting, WAF, auth, gRPC per-request balancing. Costs CPU and adds a hop. Envoy, Nginx, Google Front End (GFE).
*   **Why L7 matters for gRPC:** HTTP/2 multiplexes many requests on one long-lived connection, so an L4 balancer pins all of a client's requests to one backend. Balance per request at L7, or use client-side load balancing.

<div class="lab" data-viz="flow-lb-l4-l7"></div>

### Direct Server Return (DSR)
In NAT-mode L4 balancing, responses flow back through the LB, which can bottleneck on large responses.
*   **DSR:** The LB rewrites only the destination MAC and forwards the packet; the backend has the service IP (VIP) configured on a loopback interface and replies **directly** to the client. The LB sees only inbound traffic. Trade-off: the LB can't see responses (no response-based health signals) and backends must be on the same L2 segment (or use tunneling).

### Balancing algorithms
| Algorithm | Good for | Caveat |
|---|---|---|
| Round robin | Uniform requests | Ignores load differences |
| Least connections / least outstanding requests | Variable request cost | Needs live counters |
| Power of two random choices | Large fleets | Near-least-loaded with O(1) work, avoids herding |
| Consistent hashing / Maglev / rendezvous | Affinity (caches, sessions) | Hot keys still hot |
| Weighted | Heterogeneous hardware, canaries | Weights must be maintained |

### Anycast Routing
How does `8.8.8.8` answer quickly from most places?
*   Many sites around the world announce the **same IP prefix** via **BGP**. Routers send packets to the topologically nearest announcement (by BGP policy, not strictly geographic distance).
*   Gives network-level global load distribution and DDoS absorption (attack traffic is spread across sites). Works best for short-lived or stateless flows like DNS; long TCP flows can break if routing changes mid-connection, which is why Google terminates at an anycast edge and then routes internally.

### Health Checks, Connection Draining and Retries

A load balancer is only as good as its picture of which backends are healthy:

- **Active health checks** probe each backend (a TCP connect or an HTTP `/healthz`)
  every few seconds and eject it after several failures. **Passive** checks (outlier
  detection, as in Envoy) eject a backend that is returning errors on real traffic.
  A health endpoint should check the process can serve, not every dependency: if it
  fails whenever the shared database is slow, *every* backend fails at once and the
  load balancer has nothing left to send to.
- **Connection draining:** before removing a backend (a deploy, a scale-down), stop
  sending it *new* connections and let in-flight requests finish within a grace
  period. Without draining, every deploy shows up as a burst of errors.
- **Retries belong in one layer, with a budget.** If the client, the L7 proxy and the
  service each retry three times, one failing call becomes up to 27 attempts on the
  struggling backend (a retry storm). Retry only idempotent requests, with
  exponential backoff and jitter, and cap retries as a percentage of traffic. See
  [Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md).

## 5. The TLS 1.3 Handshake

If asked how HTTPS works, don't just say "it encrypts data." **Precision note:** in TLS 1.3 the key exchange happens *in* the Hello messages and the certificate is sent **encrypted**; older explanations describe TLS 1.2.

1.  **ClientHello:** supported cipher suites, a random nonce, and a **key_share** (the client's ephemeral (EC)DHE public key, e.g. X25519), plus SNI (the hostname).
2.  **ServerHello:** chosen cipher suite, server nonce, and the server's **key_share**. Both sides now compute the same shared secret via Diffie-Hellman; handshake keys are derived from it. Everything after this point is encrypted.
3.  **Encrypted server messages:** `EncryptedExtensions`, `Certificate` (chain), `CertificateVerify` (a **signature** over the handshake transcript with the certificate's private key — this proves the server owns the certificate), and `Finished` (MAC over the transcript).
4.  **Client verification:** check the certificate chain up to a trusted root CA, check the hostname matches, check validity and revocation policy (and Certificate Transparency in browsers), verify `CertificateVerify`, then send its own `Finished`.
5.  **Application data:** symmetric AEAD encryption (AES-GCM or ChaCha20-Poly1305) with keys derived from the handshake. Symmetric crypto is used for bulk data because it's far faster than public-key operations.

Properties to name: **forward secrecy** (ephemeral keys — a stolen server private key can't decrypt past traffic), **1-RTT full handshake**, optional **0-RTT resumption** (replayable), **mTLS** (client also presents a certificate; standard for service-to-service auth, e.g. Google's ALTS internally, SPIFFE/Istio elsewhere).

### Certificates and the Chain of Trust

Encryption alone isn't enough: you also need to know you're encrypting to the *real*
`google.com`, not an attacker in the middle. That is the job of certificates.

- **Asymmetric (public-key) cryptography** gives each server a key pair: a private key
  it keeps secret and a public key anyone may have. A signature made with the private
  key can be verified with the public key. It is slow, so TLS uses it only to
  authenticate and agree keys; **symmetric** encryption (one shared key, fast) carries
  the actual data.
- A **certificate** binds a public key to a name ("this key belongs to
  `*.google.com`"), signed by a **certificate authority (CA)**. The server sends a
  chain: its own (leaf) certificate, signed by an intermediate CA, signed by a root CA
  that your OS or browser already trusts.
- The client walks the chain to a trusted root, checks names and expiry, and then
  checks `CertificateVerify` (step 3 above) to confirm the server actually *holds* the
  private key and isn't just replaying someone else's certificate.
- Certificates expire on purpose. The CA/Browser Forum is shrinking the maximum
  lifetime of public TLS certificates in stages: 398 days until March 2026, 200 days
  since then, 100 days from March 2027 and 47 days from March 2029. That makes
  automated renewal (ACME, as used by Let's Encrypt) mandatory in practice. An expired certificate is still one of the most common causes of
  self-inflicted outages.

### What Changed from TLS 1.2

| | TLS 1.2 | TLS 1.3 |
|---|---|---|
| Full handshake | 2 RTTs | 1 RTT |
| Resumption | 1 RTT | 1 RTT, or 0-RTT with replay risk |
| Key exchange | RSA key transport *or* (EC)DHE | (EC)DHE only, so forward secrecy is always on |
| Certificate on the wire | In plaintext | Encrypted |
| Cipher suites | Many, including weak legacy ones (CBC modes, RC4, SHA-1) | Five AEAD suites |

<div class="lab" data-viz="flow-tls13"></div>

## 6. DNS in More Depth

| Record | Purpose |
|---|---|
| A / AAAA | IPv4 / IPv6 address |
| CNAME | Alias to another name (not allowed at the zone apex) |
| MX | Mail servers |
| NS | Delegation to authoritative servers |
| TXT | Verification, SPF/DKIM |
| SRV | Service host + port |

- **TTL trade-off:** short TTLs allow fast failover and traffic shifting but increase resolver load and latency; long TTLs are cheap but slow to change. Resolvers and clients don't always honor TTLs exactly.
- **GeoDNS / latency-based DNS:** return different answers by resolver location (EDNS Client Subnet improves accuracy).
- **DNS is a dependency:** cache results, set timeouts, and don't resolve per request in hot paths.
- **UDP by default, TCP for large responses;** DNS over HTTPS/TLS for privacy.

### How a Lookup Actually Resolves

- **Stub resolver → recursive resolver:** your machine's resolver asks one
  **recursive** resolver (your ISP's, `8.8.8.8`, `1.1.1.1`, or a corporate one) to do
  all the work and return a final answer.
- **Iterative queries from the recursive resolver:** it asks a root server "where is
  `.com`?", gets a referral to the `.com` TLD servers, asks them "where is
  `google.com`?", gets a referral to Google's authoritative servers (with **glue
  records**, their IPs, to avoid a chicken-and-egg lookup), and finally gets the A or
  AAAA record.
- **Caching at every layer:** browser, OS, and recursive resolver all cache answers
  for the record's TTL, so the root and TLD servers are rarely asked. Failed lookups
  (`NXDOMAIN`) are cached too (**negative caching**), so a record created *after*
  someone looked for it can stay invisible to them for a while.
- **Why migrations use short TTLs:** lower the TTL (say, to 60 s) a day *before*
  changing an IP, so caches already hold short-lived answers when you switch; raise
  it again afterwards.

<div class="lab" data-viz="flow-dns"></div>

## 7. The Cost of a Request, Measured

Sections 1–3 describe connections, Nagle's algorithm and streams in words. This program measures
all three over loopback, where the network itself is almost free, so only the protocol's own costs
show. Run it with `python3 rtt.py`:

```python
"""Three things that decide the cost of a request over TCP, measured on loopback
(so the network itself costs almost nothing and only the protocol shows):
1. opening a new connection for every request vs reusing one;
2. a request written in two pieces, with and without TCP_NODELAY
   (Nagle's algorithm meets delayed ACKs);
3. how the same bytes arrive: TCP delivers a stream, not messages."""
import socket, threading, time

def server(sock):
    while True:
        c, _ = sock.accept()
        c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        threading.Thread(target=serve, args=(c,), daemon=True).start()

def serve(c):
    buf = b""
    while True:
        d = c.recv(4096)
        if not d:
            return c.close()
        buf += d
        while b"\n" in buf:                          # one request per line
            line, buf = buf.split(b"\n", 1)
            c.sendall(b"ok\n")

srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(128)
threading.Thread(target=server, args=(srv,), daemon=True).start()
addr = srv.getsockname()

def recv_line(s):
    d = b""
    while not d.endswith(b"\n"):
        d += s.recv(64)

def timed(fn, n):
    t = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t) / n * 1e6

def new_conn():
    s = socket.create_connection(addr)
    s.sendall(b"GET\n"); recv_line(s); s.close()

keep = socket.create_connection(addr)
keep.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
def reuse():
    keep.sendall(b"GET\n"); recv_line(keep)

print("1. Per request")
print(f"   new connection each time   {timed(new_conn, 2000):7.1f} µs")
print(f"   reused connection          {timed(reuse, 2000):7.1f} µs")

def two_writes(nodelay):
    s = socket.create_connection(addr)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, nodelay)
    def req():
        s.sendall(b"GET /x HTTP/1.1 ")                # header...
        s.sendall(b"body\n")                         # ...then body, as two writes
        recv_line(s)
    return timed(req, 50)

print("\n2. Request sent as two small writes")
print(f"   default (Nagle on)         {two_writes(0):9.1f} µs")
print(f"   TCP_NODELAY                {two_writes(1):9.1f} µs")

print("\n3. TCP delivers bytes, not messages")
lst = socket.socket(); lst.bind(("127.0.0.1", 0)); lst.listen()
a = socket.create_connection(lst.getsockname())
b, _ = lst.accept()
for m in (b"first", b"second", b"third"):
    a.sendall(m)                                     # three separate sends...
time.sleep(0.05)
print(f"   3 sends, then one recv(4096) returns {b.recv(4096)!r}")
big = b"x" * 4_000_000
threading.Thread(target=a.sendall, args=(big,), daemon=True).start()
sizes, got = [], 0
while got < len(big):
    n = len(b.recv(1 << 20))
    sizes.append(n); got += n
print(f"   one 4 MB send arrives as {len(sizes)} recv() results, "
      f"from {min(sizes):,} to {max(sizes):,} bytes")
```

```text
1. Per request
   new connection each time     492.4 µs
   reused connection             63.7 µs

2. Request sent as two small writes
   default (Nagle on)           43174.7 µs
   TCP_NODELAY                     94.3 µs

3. TCP delivers bytes, not messages
   3 sends, then one recv(4096) returns b'firstsecondthird'
   one 4 MB send arrives as 16 recv() results, from 65,536 to 1,048,576 bytes
```

**New connections are expensive even with no distance to cover.** Setting up a connection per
request cost several times as much as reusing one here: the handshake, the kernel creating socket
state on both sides, and the server accepting and dispatching it. Over a real network the handshake
also costs a full round trip, plus two more for TLS 1.2 or one for TLS 1.3 (§5). That is why every
HTTP client keeps a connection pool, why HTTP/1.1 made keep-alive the default, and why a
misconfigured client that opens a connection per call can run a service out of ephemeral ports
(each closed connection sits in `TIME_WAIT` for about a minute on the side that closed it, §1).

**Two small writes cost 40 ms.** The request was sent as two `send()` calls. Nagle's algorithm
holds the second small write until the first is acknowledged; the receiver's delayed-ACK timer holds
that acknowledgement, hoping to piggyback it on a response that can't be sent until the rest of the
request arrives. Both sides wait for each other until the delayed-ACK timer (about 40 ms on Linux)
fires. With `TCP_NODELAY` the same exchange takes microseconds. The fixes are to build each message in
one buffer and write it once, or set `TCP_NODELAY`, which most RPC frameworks and databases do by
default. A request latency that clusters near 40 ms, or 200 ms on some systems, is the signature.

**TCP is a byte stream, not a message stream.** Three `send()` calls arrived as one `recv()`, and one
4 MB `send()` arrived in about a dozen pieces of different sizes. Nothing in TCP marks where one
application message ends. Every protocol on top of TCP therefore defines its own **framing**: HTTP/1.1
uses headers ending in a blank line and `Content-Length` or chunked encoding, HTTP/2 and gRPC use
length-prefixed frames, and Redis uses a length-prefixed text protocol. Code that assumes one `recv()`
returns one message works in testing, where messages are small and the network is idle, and fails in
production.

## 8. What Failures Look Like From the Client

A client doesn't see "the server is down"; it sees an error type after some amount of time, and
the two together are all it has to decide whether to retry. This program produces each case on
purpose. Run it with `python3 failures.py`:

```python
"""What each network failure looks like to the client, on loopback. The error
type and how long it takes to appear are what your timeouts and retry logic
actually see."""
import socket, struct, threading, time


def attempt(label, fn, timeout=0.5):
    s = socket.socket()
    s.settimeout(timeout)
    t = time.perf_counter()
    try:
        result = fn(s) or "ok"
    except Exception as e:
        result = type(e).__name__
    print(f"  {label:44} {result:24} after {(time.perf_counter() - t) * 1000:7.1f} ms")
    s.close()


def listener(backlog=16):
    l = socket.socket(); l.bind(("127.0.0.1", 0)); l.listen(backlog)
    return l, l.getsockname()

# A port nobody listens on
tmp = socket.socket(); tmp.bind(("127.0.0.1", 0)); closed = tmp.getsockname(); tmp.close()

# A server that accepts and then never answers
silent, silent_addr = listener()
threading.Thread(target=lambda: [silent.accept() for _ in range(10)], daemon=True).start()

# A server that accepts, reads the request, then resets the connection
def resetter(l):
    while True:
        c, _ = l.accept()
        c.recv(100)
        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        c.close()                                     # linger 0: send RST, not FIN
reset_srv, reset_addr = listener()
threading.Thread(target=resetter, args=(reset_srv,), daemon=True).start()

# A server that accepts, reads, then closes politely without answering
def closer(l):
    while True:
        c, _ = l.accept(); c.recv(100); c.close()
close_srv, close_addr = listener()
threading.Thread(target=closer, args=(close_srv,), daemon=True).start()

def request(addr):
    def go(s):
        s.connect(addr); s.sendall(b"GET\n")
        data = s.recv(100)
        return "EOF: recv returned b''" if data == b"" else repr(data)
    return go

print(f"  {'what happened':44} {'what the client got':24} {'when':>16}")
attempt("nothing listening on the port", lambda s: s.connect(closed))
attempt("server accepted, never replied", request(silent_addr))
attempt("server read the request, then reset", request(reset_addr))
attempt("server read the request, then closed", request(close_addr))

# The kernel completes handshakes for a process that never calls accept()
stuck, stuck_addr = listener(backlog=2)
print("\n  a server that is alive but never calls accept() (backlog 2):")
for i in range(1, 6):
    attempt(f"connection {i}", lambda s: s.connect(stuck_addr))
```

```text
  what happened                                what the client got                  when
  nothing listening on the port                ConnectionRefusedError   after     0.1 ms
  server accepted, never replied               TimeoutError             after   500.7 ms
  server read the request, then reset          ConnectionResetError     after     0.3 ms
  server read the request, then closed         EOF: recv returned b''   after     0.2 ms

  a server that is alive but never calls accept() (backlog 2):
  connection 1                                 ok                       after     0.0 ms
  connection 2                                 ok                       after     0.0 ms
  connection 3                                 ok                       after     0.0 ms
  connection 4                                 TimeoutError             after   500.6 ms
  connection 5                                 TimeoutError             after   500.7 ms
```

| What the client sees | What it means | What to do |
|---|---|---|
| `ConnectionRefused`, immediately | The host is up but nothing listens on that port (the host sent a RST) | Fail fast; try another replica; the process is down or starting |
| Timeout while connecting | Packets are dropped: host down, firewall, wrong address, or the listen backlog is full | Needs a short connect timeout (hundreds of ms inside a datacenter), then another replica |
| Timeout while waiting for a response | The server accepted the request and is slow, stuck, or overloaded | The request may have been executed; retry only if the operation is idempotent |
| `ConnectionReset` | The server (or a middlebox) aborted the connection | The request may have been executed; same rule as above |
| EOF (`recv` returns nothing) | The server closed the connection normally, often an idle keep-alive connection closing just as the client reused it | Safe to retry on a new connection if nothing was sent, or if the request is idempotent |

Two lessons are worth stating in an interview:

- **Use separate connect and read timeouts.** A connect should succeed within about one round trip;
  a read may legitimately take as long as the slowest request. A single timeout is either too long
  to detect dead hosts or too short for slow requests.
- **"Connected" doesn't mean "served".** The kernel completes the three-way handshake and queues
  the connection *before* the application calls `accept()`. A server that is alive but stuck
  (a deadlock, a long GC pause, a full thread pool) still accepts connections until its backlog fills;
  above, three connections succeeded against a process that never accepted any, and only the fourth
  timed out. Health checks must therefore make a real request, not just open a TCP connection, and
  `ss -lnt` showing `Recv-Q` near the backlog size is the symptom of an application that isn't calling
  `accept()` fast enough.

## 9. Head-of-Line Blocking, Simulated

§3 claims HTTP/2 over TCP still suffers head-of-line blocking, and HTTP/3 over QUIC doesn't. This
simulation shows the size of the effect for a typical page: nine small resources and one large
image multiplexed on one connection, at increasing packet loss. Run it with `python3 hol.py`:

```python
"""Head-of-line blocking. A page loads 9 small resources (CSS, scripts, icons:
6 packets each) and one large image (240 packets) over one connection. Packets
are interleaved round-robin across the resources still sending, one per
millisecond. RTT 50 ms; a lost packet is noticed and resent about one RTT later.
  HTTP/2 over TCP:  TCP hands bytes to the app strictly in order, so one lost
                    packet holds back every stream behind it.
  HTTP/3 over QUIC: ordering is per stream, so a loss holds back only its own stream."""
import random, statistics

RTT = 50.0
SIZES = [6] * 9 + [240]


def schedule():
    left, order = list(SIZES), []
    while any(left):
        for s in range(len(SIZES)):
            if left[s]:
                order.append(s); left[s] -= 1
    return order                                          # stream of each packet, in send order


ORDER = schedule()


def trial(loss, rng):
    tcp, quic, upto = [0.0] * len(SIZES), [0.0] * len(SIZES), 0.0
    for i, s in enumerate(ORDER):
        t = i + RTT / 2                                   # sent at i ms, arrives half an RTT later
        while rng.random() < loss:
            t += RTT                                      # lost: resent about one RTT later
        upto = max(upto, t)                               # TCP delivers only in order
        tcp[s] = upto
        quic[s] = max(quic[s], t)
    return tcp, quic


def p(xs, q):
    return sorted(xs)[int(q * len(xs))]


rng = random.Random(1)
print("Time until each of the 9 small resources is usable (the image needs about 320 ms either way)")
print(f"  {'loss':>5} {'TCP mean':>9} {'TCP p95':>8} {'QUIC mean':>10} {'QUIC p95':>9}")
for loss in (0.0, 0.005, 0.01, 0.02, 0.05):
    tcp_small, quic_small = [], []
    for _ in range(4000):
        tcp, quic = trial(loss, rng)
        tcp_small += tcp[:9]; quic_small += quic[:9]
    print(f"  {loss:5.1%} {statistics.mean(tcp_small):6.0f} ms {p(tcp_small, .95):5.0f} ms "
          f"{statistics.mean(quic_small):7.0f} ms {p(quic_small, .95):6.0f} ms")
```

```text
Time until each of the 9 small resources is usable (the image needs about 320 ms either way)
   loss  TCP mean  TCP p95  QUIC mean  QUIC p95
   0.0%     79 ms    83 ms      79 ms     83 ms
   0.5%     85 ms   120 ms      80 ms     83 ms
   1.0%     90 ms   125 ms      81 ms     83 ms
   2.0%     99 ms   129 ms      82 ms    109 ms
   5.0%    117 ms   163 ms      87 ms    127 ms
```

With no loss the two are identical: multiplexing works. With loss, TCP delivers bytes only in
order, so a packet lost from the image holds back the CSS and scripts sent after it until the
retransmission arrives, about one round trip later. At 1% loss the slowest 5% of small resources
take about 50% longer over TCP, while QUIC loses only a little, because each stream waits only
for its own lost packets. This is why HTTP/3 helps most on lossy mobile and long-distance
connections and hardly at all on a clean datacenter network. Two caveats keep the comparison
honest: QUIC runs in user space and costs more CPU per byte than kernel TCP, and some networks
throttle or block UDP, so clients must fall back to HTTP/2.

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side. The mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it as a syllabus (read down a column) or as a
self-assessment (find the cell that matches where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Layers, addressing & devices** (Foundations) | Knows IP address vs. port, client vs. server, and that data moves as packets | Can explain the TCP/IP layers, encapsulation, and what a router, switch and NAT each do | Uses the layer model to localise a failure ("refused" vs. "timeout", L4 vs. L7) and reasons about MTU/MSS and 4-tuples | Designs network topology and addressing for a platform: private ranges, NAT egress limits, IPv6 migration, ossification risks |
| **The request walkthrough** (§0) | Lists DNS → TCP → HTTP in order | Adds TLS, caching and load balancing in the right places | Goes deep on any layer on demand, with RTT counts and the failure mode of each step | Connects the walkthrough to edge architecture: anycast, TLS termination, backbone routing, and what each costs globally |
| **TCP internals** (§1) | Knows TCP is reliable and UDP isn't | Explains the three-way handshake and what an ACK is | Explains TIME_WAIT, SYN cookies, flow vs. congestion control, RTO/fast retransmit, Nagle and `TCP_NODELAY`, and reads `ss` output | Diagnoses fleet-wide issues (ephemeral port exhaustion, retransmit spikes, accept-queue overflow) from metrics and sets kernel and pool policy |
| **Congestion control** (§2) | Aware the network can be congested | Knows slow start exists and that loss slows TCP down | Compares CUBIC and BBR precisely (IW10, β = 0.7, BBR's model) and explains the bandwidth-delay product | Decides whether to roll out BBR for a service, with a measurement plan and fairness concerns |
| **HTTP versions & semantics** (§3) | Knows methods and status codes | Knows HTTP/2 multiplexes and HTTP/3 uses QUIC; knows which methods are idempotent | Explains head-of-line blocking at each version, QUIC 1-RTT vs. 0-RTT replay, and caching headers | Chooses protocols for a product (gRPC vs. REST, WebSocket vs. SSE, HTTP/3 rollout) with their operational consequences |
| **Load balancing** (§4) | Knows a load balancer spreads traffic | Knows round robin vs. least connections, and health checks | Explains L4 vs. L7, DSR, Maglev-style consistent hashing, why gRPC needs per-request balancing, and retry storms | Designs global traffic management: anycast, failover between regions, retry budgets, and overload behaviour |
| **TLS & DNS** (§5–§6) | Knows HTTPS encrypts and DNS maps names to IPs | Knows certificates, CAs and DNS record types | Describes the TLS 1.3 handshake exactly (CertificateVerify, forward secrecy) and DNS resolution with TTL trade-offs | Owns certificate automation and DNS-based traffic strategy for a platform, and plans a migration so that caches never break it |
| **Measured behaviour** (§7–§9) | Knows opening a connection costs time | Reuses connections; knows TCP is a byte stream that needs framing | Recognises the 40 ms Nagle/delayed-ACK stall, maps refused/timeout/reset/EOF to retry decisions, sets separate connect and read timeouts, and quantifies head-of-line blocking | Sets fleet-wide client defaults (pools, timeouts, `TCP_NODELAY`, health-check depth) and decides where HTTP/3 pays off from loss measurements |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column, which the numbered sections (0–9) deliver in
full. The Foundations section alone takes you to roughly the "Mid-Level" column. The
"Staff+" column is judgment that mostly comes from operating real systems at scale;
this file gives you the vocabulary to have that conversation, not a substitute for
having had it.

## Interview checklist

- [ ] I can name the TCP/IP layers, what each is responsible for, and what a switch, router and NAT each do.
- [ ] I can explain encapsulation and where the 1500-byte MTU and 1460-byte MSS come from.
- [ ] I can explain what a socket is, what identifies a TCP connection (the 4-tuple), and compare TCP with UDP beyond "reliable vs. fast".
- [ ] I can walk through "type google.com" from HSTS to paint, going deep on any layer, and say how each step fails.
- [ ] I can explain TIME_WAIT, SYN cookies, flow vs congestion control, and Nagle.
- [ ] I can explain sequence numbers, ACKs, RTO and fast retransmit, and what `CLOSE_WAIT` piling up means.
- [ ] I can compare CUBIC and BBR precisely (IW10, β = 0.7, BBR's model) and compute a bandwidth-delay product.
- [ ] I can explain HTTP/2 vs HTTP/3 head-of-line blocking and QUIC 1-RTT vs 0-RTT.
- [ ] I can say which HTTP methods are safe and idempotent and which status codes are worth retrying.
- [ ] I can explain L4 vs L7, DSR, and why gRPC needs per-request balancing.
- [ ] I can describe the TLS 1.3 handshake correctly, including CertificateVerify and forward secrecy, and explain the certificate chain.
- [ ] I can explain recursive vs. iterative DNS resolution and why migrations lower TTLs first.
- [ ] I can explain, with numbers, why connection reuse matters and where a 40 ms stall on small writes comes from.
- [ ] I can explain why TCP needs application-level framing and how HTTP/1.1, HTTP/2 and gRPC frame messages.
- [ ] I can map refused, connect timeout, read timeout, reset and EOF to their causes and to a retry decision.
- [ ] I can explain why a TCP connection can succeed to a server that is stuck, and what that means for health checks.
- [ ] I can quantify head-of-line blocking over TCP vs QUIC under packet loss.

Related: [Networking](../SystemDesign/building_blocks/02_networking.md), [Scaling and Load Balancing](../SystemDesign/building_blocks/13_scaling_and_load_balancing.md), [Real-Time Communication and Collaboration](../SystemDesign/building_blocks/22_realtime_and_collaboration.md); GoEngineering topic 34.
