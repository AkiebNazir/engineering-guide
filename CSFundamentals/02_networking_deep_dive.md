# Networking & Distributed Communication

Every API call, database connection, and "it works on my machine but not in prod" bug
eventually comes down to bytes moving between two machines. This file starts with
what those bytes actually are and how two computers agree to exchange them, then goes
as deep as an L5 interview loop expects: you are expected to know what happens on the
wire. When a distributed system misbehaves, the cause is often not the application
code but connection setup, congestion control, TLS, DNS, or load balancer behavior.
This file corrects several common simplifications; corrections are marked
**Precision note**.

## Foundations — Start Here If You're New to Networking

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

**TCP vs. UDP — the two building blocks almost everything else uses.**
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

**Vocabulary you'll meet below, in one table:**

| Term | One-line meaning |
|---|---|
| IP address | Identifies a machine on the network |
| Port | Identifies which program on that machine |
| Packet | A chunk of data plus routing headers; the unit the network actually moves |
| RTT (round-trip time) | Time for a packet to reach the other side and its reply to come back |
| Handshake | Messages exchanged before data flows, to agree on connection parameters |
| Socket | A local endpoint (IP + port + protocol) your program reads/writes through |

Section 0 below is the classic "walk me through what happens when..." interview
answer, using every layer above in sequence — read it once you're comfortable with
this vocabulary.

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

<div class="lab" data-viz="flow-web-request"></div>

## 1. TCP Fundamentals Before Congestion Control

### Connection lifecycle
- **Three-way handshake:** `SYN` (client ISN) → `SYN-ACK` (server ISN, ack client) → `ACK`. The server holds half-open state after SYN, which is what a **SYN flood** exhausts; **SYN cookies** encode that state into the ISN so no memory is held.
- **Teardown:** `FIN`/`ACK` in each direction. The side that closes first enters **TIME_WAIT** for 2×MSL (commonly 60 s on Linux) so delayed segments from the old connection can't corrupt a new one with the same 4-tuple. A proxy that opens many short outbound connections can run out of ephemeral ports because of TIME_WAIT: use connection pooling / keep-alive.
- **Flow control vs congestion control:** *flow control* protects the RECEIVER (the advertised receive window says how much it can buffer); *congestion control* protects the NETWORK (the congestion window, cwnd). The sender may transmit min(rwnd, cwnd).
- **Nagle's algorithm + delayed ACKs** can add ~40 ms latency to small request/response writes. Latency-sensitive RPC stacks set `TCP_NODELAY`.

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

### Real-time delivery options (see `SystemDesign/building_blocks/22_realtime_and_collaboration.md`)
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

## 5. The TLS 1.3 Handshake

If asked how HTTPS works, don't just say "it encrypts data." **Precision note:** in TLS 1.3 the key exchange happens *in* the Hello messages and the certificate is sent **encrypted**; older explanations describe TLS 1.2.

1.  **ClientHello:** supported cipher suites, a random nonce, and a **key_share** (the client's ephemeral (EC)DHE public key, e.g. X25519), plus SNI (the hostname).
2.  **ServerHello:** chosen cipher suite, server nonce, and the server's **key_share**. Both sides now compute the same shared secret via Diffie-Hellman; handshake keys are derived from it. Everything after this point is encrypted.
3.  **Encrypted server messages:** `EncryptedExtensions`, `Certificate` (chain), `CertificateVerify` (a **signature** over the handshake transcript with the certificate's private key — this proves the server owns the certificate), and `Finished` (MAC over the transcript).
4.  **Client verification:** check the certificate chain up to a trusted root CA, check the hostname matches, check validity and revocation policy (and Certificate Transparency in browsers), verify `CertificateVerify`, then send its own `Finished`.
5.  **Application data:** symmetric AEAD encryption (AES-GCM or ChaCha20-Poly1305) with keys derived from the handshake. Symmetric crypto is used for bulk data because it's far faster than public-key operations.

Properties to name: **forward secrecy** (ephemeral keys — a stolen server private key can't decrypt past traffic), **1-RTT full handshake**, optional **0-RTT resumption** (replayable), **mTLS** (client also presents a certificate; standard for service-to-service auth, e.g. Google's ALTS internally, SPIFFE/Istio elsewhere).

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

<div class="lab" data-viz="flow-dns"></div>

## Interview checklist

- [ ] I can walk through "type google.com" from HSTS to paint, going deep on any layer.
- [ ] I can explain TIME_WAIT, SYN cookies, flow vs congestion control, and Nagle.
- [ ] I can compare CUBIC and BBR precisely (IW10, β = 0.7, BBR's model).
- [ ] I can explain HTTP/2 vs HTTP/3 head-of-line blocking and QUIC 1-RTT vs 0-RTT.
- [ ] I can explain L4 vs L7, DSR, and why gRPC needs per-request balancing.
- [ ] I can describe the TLS 1.3 handshake correctly, including CertificateVerify and forward secrecy.

Related: `SystemDesign/building_blocks/02_networking.md`, `13_scaling_and_load_balancing.md`, `22_realtime_and_collaboration.md`; GoEngineering topic 34.
