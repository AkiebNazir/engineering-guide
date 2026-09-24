/* Live request flows (see sd-flow.js for the engine and data format). */
'use strict';
{ // block scope: keeps the L* layout constants out of the shared global scope

/* ======================================== CSFundamentals/02 · networking == */

/* ---- 0. What happens when you type google.com and press Enter ---------- */
const LnetWeb = lane([
  { label: 'CLIENT', nodes: [
    { id: 'browser', label: 'Browser', sub: 'HSTS list · caches', kind: 'client', icon: 'browser', row: 1 }] },
  { label: 'RECURSIVE DNS', nodes: [
    { id: 'resolver', label: 'Resolver', sub: 'ISP / 8.8.8.8', kind: 'cache', icon: 'dns', row: 0 }] },
  { label: 'AUTHORITATIVE', nodes: [
    { id: 'auth', label: 'google.com NS', sub: 'geo-aware answers', kind: 'db', icon: 'dns', row: 0 }] },
  { label: 'GOOGLE EDGE', nodes: [
    { id: 'gfe', label: 'Front End', sub: 'GFE · anycast IP', icon: 'edge', row: 1 }] },
  { label: 'BACKEND', nodes: [
    { id: 'shards', label: 'Index shards', sub: 'fan-out', kind: 'db', icon: 'search', row: 0 },
    { id: 'web', label: 'Search frontend', sub: 'merge · rank', icon: 'server', row: 1 }] },
]);
defineFlow('flow-web-request', {
  title: 'Live flow: typing google.com and pressing Enter',
  hint: 'Pick a scenario and follow one page load across DNS, TCP, TLS, the edge and the backend. The latency bar shows which round trips a first visit pays and a repeat visit skips.',
  zones: LnetWeb.zones, h: LnetWeb.h, nodes: LnetWeb.nodes,
  edges: [
    ['browser', 'resolver'], ['resolver', 'auth'], ['browser', 'gfe'],
    ['gfe', 'web'], ['web', 'shards'],
  ],
  scenarios: [
    {
      id: 'first', name: 'First visit (HTTP/2)',
      summary: 'A cold start: nothing cached, no open connection. Every layer costs at least one <b>round trip</b>, which is why a same-continent RTT of ~20-80 ms dominates.',
      steps: [
        { at: 'browser', badge: 'HSTS → https', ms: 1, title: 'Parse the URL and check local state',
          detail: 'The HSTS preload list says google.com is HTTPS-only, so the browser never tries plain http. It then checks its own DNS and HTTP caches before touching the network.' },
        { path: ['browser', 'resolver'], label: 'A? google.com', ms: 5, title: 'Browser and OS caches miss',
          detail: 'The browser cache and the OS resolver cache have nothing, so the query goes to the recursive resolver (your ISP or <code>8.8.8.8</code>), roughly a few ms away.' },
        { path: ['resolver', 'auth', 'resolver'], label: 'root → .com → google.com', ms: 30, title: 'Resolver walks the hierarchy',
          detail: 'Root points to the <code>.com</code> TLD, the TLD points to google.com\'s authoritative servers, and they return the A/AAAA record. Uncached, this costs tens of ms (≈ 30 ms here).' },
        { path: ['resolver', 'browser'], label: 'A (anycast IP)', ms: 5, title: 'IP address returned and cached',
          detail: 'Every layer caches the answer for its <b>TTL</b>. Google answers with an anycast, geo-aware address, so the same IP reaches a nearby front end wherever you are.' },
        { path: ['browser', 'gfe', 'browser'], label: 'SYN → SYN-ACK → ACK', ms: 40, title: 'TCP three-way handshake: 1 RTT',
          detail: 'Both sides agree on sequence numbers before any data moves. Anycast routing means this RTT is to a nearby Google edge, not to a distant data center (≈ 40 ms here).' },
        { path: ['browser', 'gfe', 'browser'], label: 'ClientHello(key_share)', ms: 40, title: 'TLS 1.3 handshake: 1 more RTT',
          detail: 'The key exchange rides inside the Hello messages, and the certificate comes back encrypted. TLS is terminated here at the edge, so the slow crypto round trip stays short.' },
        { path: ['browser', 'gfe'], label: 'GET / (HTTP/2)', ms: 20, title: 'The request itself',
          detail: 'HTTP/2 sends binary frames with <b>HPACK</b>-compressed headers, and many requests can share this one connection. The GFE load-balances at L4, then L7.' },
        { path: ['gfe', 'web', 'shards', 'web'], label: 'query fan-out', ms: 30, title: 'Backbone, then fan-out to the index',
          detail: 'The GFE forwards over Google\'s private backbone. The search frontend queries many index shards in parallel, then merges and ranks the results (≈ 30 ms here).' },
        { path: ['web', 'gfe', 'browser'], label: 'HTML (streamed)', tone: 'ok', ms: 20, title: 'Response streamed back',
          detail: 'The browser parses HTML as it arrives, builds the DOM and CSSOM, fetches subresources (often from cache or CDN), runs JS and paints. Note that DNS, TCP and TLS took more time than the search itself.' },
      ],
    },
    {
      id: 'repeat', name: 'Repeat visit',
      summary: 'Seconds later: the DNS answer is still within its TTL and the HTTP/2 connection is still open (<b>keep-alive</b>). Only the request itself costs a round trip.',
      steps: [
        { at: 'browser', badge: 'DNS cache hit', tone: 'ok', ms: 0, title: 'Name already resolved',
          detail: 'The cached A record has TTL left, so no DNS query is sent at all. This is why services cache DNS results rather than resolving on every request.' },
        { at: 'browser', badge: 'reuse open conn', tone: 'ok', ms: 0, title: 'No new TCP or TLS handshake',
          detail: 'The existing connection to the GFE is still open, so the two handshake round trips (≈ 80 ms on a cold start) are skipped entirely.' },
        { path: ['browser', 'gfe'], label: 'GET / (new stream)', ms: 20, title: 'Request on the reused connection',
          detail: 'HTTP/2 opens a new stream on the same connection. HPACK has already seen most of these headers, so they compress to a few bytes.' },
        { path: ['gfe', 'web', 'shards', 'web'], label: 'query fan-out', ms: 30, title: 'Same backend work',
          detail: 'Connection reuse saves network round trips, not server work: the fan-out and ranking cost the same.' },
        { path: ['web', 'gfe', 'browser'], label: 'HTML', tone: 'ok', ms: 20, title: 'Response in about one RTT plus server time',
          detail: 'Roughly 70 ms against ≈ 230 ms for the first visit. Most of a cold page load is connection setup.' },
      ],
    },
    {
      id: 'h3', name: 'HTTP/3 (QUIC)',
      summary: 'Same page over <b>QUIC</b>: transport and TLS 1.3 share one handshake, so a new connection costs 1 RTT instead of 2.',
      steps: [
        { path: ['browser', 'resolver', 'browser'], label: 'A? (cached at resolver)', ms: 5, title: 'DNS answered from the resolver cache',
          detail: 'Someone else already asked for google.com, so the recursive resolver answers from its cache in a few ms.' },
        { path: ['browser', 'gfe', 'browser'], label: 'QUIC Initial + TLS', ms: 40, title: 'One combined handshake: 1 RTT',
          detail: 'QUIC runs over UDP and carries the TLS 1.3 messages inside its own handshake, so transport and crypto setup finish together.' },
        { path: ['browser', 'gfe'], label: 'GET / (HTTP/3)', ms: 20, title: 'Request over QUIC',
          detail: 'Headers use <b>QPACK</b>. Each stream recovers from loss on its own, so one lost packet no longer stalls every other request (no transport head-of-line blocking).' },
        { path: ['gfe', 'web', 'shards', 'web'], label: 'query fan-out', ms: 30, title: 'Same backend work',
          detail: 'Behind the edge nothing changes: HTTP/3 is a client-to-edge optimisation.' },
        { path: ['web', 'gfe', 'browser'], label: 'HTML', tone: 'ok', ms: 20, title: 'Response',
          detail: 'One RTT saved against TCP + TLS. Because QUIC identifies connections by connection ID, a phone switching from Wi-Fi to cellular keeps this connection.' },
        { at: 'browser', badge: '0-RTT next time', tone: 'warn', ms: 0, title: 'Resumption can send data in 0-RTT',
          detail: 'A later visit can resume with a cached key and send the request in the first packet. That early data is <b>replayable</b>, so only idempotent requests like this GET should use it.' },
      ],
    },
  ],
});

/* ---- 5. The TLS 1.3 handshake ------------------------------------------ */
const LnetTls = lane([
  { label: 'CLIENT', nodes: [
    { id: 'client', label: 'Browser', sub: 'ephemeral X25519 key', kind: 'client', icon: 'browser', row: 0 },
    { id: 'trust', label: 'Trust store', sub: 'root CAs · CT', icon: 'shield', row: 1 }] },
  { label: 'SERVER', nodes: [
    { id: 'server', label: 'api.example.com', sub: 'cert + private key', icon: 'server', row: 0 },
    { id: 'tickets', label: 'Session tickets', sub: 'PSK for resumption', kind: 'cache', icon: 'key', row: 1 }] },
  { label: 'INTERNAL SERVICE', nodes: [
    { id: 'app', label: 'Orders service', sub: 'mTLS peer', icon: 'service', row: 0 }] },
]);
defineFlow('flow-tls13', {
  title: 'Live flow: the TLS 1.3 handshake',
  hint: 'Watch where the key exchange happens, what is already encrypted, and what proves the server owns its certificate. Switch scenarios for mutual TLS and 0-RTT resumption.',
  zones: LnetTls.zones, h: LnetTls.h, nodes: LnetTls.nodes,
  edges: [
    ['client', 'server'], ['client', 'trust'], ['server', 'tickets'], ['server', 'app'],
  ],
  scenarios: [
    {
      id: 'full', name: 'Full 1-RTT handshake',
      summary: 'A new HTTPS connection. The key exchange happens <b>inside the Hello messages</b>, so after one round trip both sides share keys and the client can send its request.',
      steps: [
        { path: ['client', 'server'], label: 'ClientHello + key_share', ms: 20, title: 'ClientHello carries a key share',
          detail: 'Supported cipher suites, a random nonce, SNI (the hostname) and the client\'s <b>ephemeral</b> (EC)DHE public key, e.g. X25519. Sending the key share up front is what saves TLS 1.2\'s extra round trip.' },
        { at: 'server', badge: 'ECDHE → handshake keys', ms: 1, title: 'Server computes the shared secret',
          detail: 'The server combines its own ephemeral private key with the client\'s share (Diffie-Hellman). Handshake keys are derived from it, so everything after ServerHello can be encrypted.' },
        { path: ['server', 'client'], label: 'ServerHello + key_share', ms: 20, title: 'ServerHello: chosen suite and server key share',
          detail: 'On receipt the client computes the same shared secret. The keys were never sent over the wire, and because they are ephemeral, a later stolen server key cannot decrypt this session (<b>forward secrecy</b>).' },
        { path: ['server', 'client'], label: '{Cert, CertVerify, Finished}', ms: 0, title: 'Encrypted server flight (same flight)',
          detail: '<code>EncryptedExtensions</code>, the certificate chain, <code>CertificateVerify</code> (a signature over the handshake transcript with the certificate\'s private key, which proves ownership) and <code>Finished</code> (a MAC over the transcript). Unlike TLS 1.2, the certificate is encrypted.' },
        { path: ['client', 'trust', 'client'], label: 'verify chain + name', ms: 2, title: 'Client validates the certificate',
          detail: 'Chain up to a trusted root CA, hostname match, validity dates and revocation policy, plus Certificate Transparency in browsers. Then it checks <code>CertificateVerify</code> against the certificate\'s public key.' },
        { path: ['client', 'server'], label: '{Finished} + GET /', ms: 20, title: 'Client Finished, with the request right behind it',
          detail: 'The client\'s <code>Finished</code> and its first application data go in the same flight, so the full handshake costs <b>1 RTT</b>.' },
        { path: ['server', 'client'], label: 'AEAD data (AES-GCM)', tone: 'ok', ms: 20, title: 'Bulk data under symmetric encryption',
          detail: 'Traffic now uses AEAD (AES-GCM or ChaCha20-Poly1305) with keys from the handshake. Public-key crypto is used only to set up; symmetric crypto is far faster for bulk data.' },
      ],
    },
    {
      id: 'mtls', name: 'mTLS service-to-service',
      summary: 'Inside the data center the API server calls another service. With <b>mutual TLS</b> both sides present certificates, so each one knows exactly which workload it is talking to.',
      steps: [
        { path: ['server', 'app'], label: 'ClientHello + key_share', ms: 0.5, title: 'The API server is now the TLS client',
          detail: 'Same Hello as before. Within one data center the round trip is well under a millisecond, so the handshake is cheap and long-lived connections are pooled anyway.' },
        { path: ['app', 'server'], label: 'ServerHello, {Cert, CertRequest…}', ms: 0.5, title: 'The service asks for a client certificate',
          detail: 'Along with its own <code>Certificate</code>, <code>CertificateVerify</code> and <code>Finished</code>, the server sends <code>CertificateRequest</code>. That one message is what turns TLS into mTLS.' },
        { path: ['server', 'app'], label: '{Cert, CertVerify, Finished}', ms: 0.5, title: 'The caller proves its identity',
          detail: 'The API server sends its own certificate and signs the transcript with its private key, exactly as a server does. A stolen certificate without the key is useless.' },
        { at: 'app', badge: 'peer = api-frontend ✓', tone: 'ok', ms: 0.1, title: 'Authorise the workload, not the IP',
          detail: 'The service reads the peer\'s identity from the certificate (for example a SPIFFE ID) and applies policy. This is standard for service-to-service auth: Google\'s ALTS internally, SPIFFE/Istio elsewhere.' },
        { path: ['server', 'app', 'server'], label: 'RPC over mTLS', tone: 'ok', ms: 1, title: 'Encrypted, authenticated RPCs',
          detail: 'Both directions are encrypted and each end knows who the other is, so a compromised host elsewhere on the network cannot impersonate either side.' },
      ],
    },
    {
      id: 'zero', name: '0-RTT resumption',
      summary: 'A returning client resumes with a <b>pre-shared key</b> from an earlier session and sends its request in the very first flight. Faster, but the early data is replayable.',
      steps: [
        { path: ['client', 'server'], label: 'ClientHello + PSK + GET', ms: 20, title: 'Early data rides in the first flight',
          detail: 'The client includes the session ticket from last time and encrypts the request with a key derived from it. No round trip has happened yet.' },
        { path: ['server', 'tickets', 'server'], label: 'look up PSK', ms: 1, title: 'Server recovers the resumption key',
          detail: 'The ticket lets the server rebuild the pre-shared key without a certificate exchange, so it can decrypt the early data immediately.' },
        { at: 'server', badge: 'replayable!', tone: 'warn', ms: 0, title: 'Why only idempotent requests',
          detail: 'An attacker who recorded that first flight can send it again, and the server would process the request twice. A GET is safe to repeat; a POST that charges a card is not, so servers reject or delay non-idempotent early data.' },
        { path: ['server', 'client'], label: 'ServerHello … Finished + response', tone: 'ok', ms: 20, title: 'Response after a single trip',
          detail: 'The handshake completes as usual (with a fresh key share for forward secrecy), and the response to the early request comes back in the same flight.' },
      ],
    },
  ],
});

/* ---- 6. DNS in more depth ----------------------------------------------- */
const LnetDns = lane([
  { label: 'YOUR HOST', nodes: [
    { id: 'app', label: 'App', sub: 'calls getaddrinfo', icon: 'app', row: 0 },
    { id: 'stub', label: 'Stub resolver', sub: 'OS cache', kind: 'cache', icon: 'cache', row: 1 }] },
  { label: 'RECURSIVE', nodes: [
    { id: 'rec', label: 'Recursive', sub: 'ISP / 8.8.8.8', kind: 'cache', icon: 'dns', row: 1 }] },
  { label: 'AUTHORITATIVE', nodes: [
    { id: 'root', label: 'Root servers', sub: 'know the TLDs', kind: 'db', icon: 'dns', row: 0 },
    { id: 'tld', label: '.com TLD', sub: 'knows the NS', kind: 'db', icon: 'dns', row: 1 },
    { id: 'auth', label: 'example.com NS', sub: 'GeoDNS', kind: 'db', icon: 'dns', row: 2 }] },
]);
defineFlow('flow-dns', {
  title: 'Live flow: resolving api.example.com',
  hint: 'Follow a cold lookup down the delegation chain, then see how caching makes it nearly free, and why a TTL makes DNS a slow failover tool.',
  zones: LnetDns.zones, h: LnetDns.h, nodes: LnetDns.nodes,
  edges: [
    ['app', 'stub'], ['stub', 'rec'], ['rec', 'root'], ['rec', 'tld'], ['rec', 'auth'],
  ],
  scenarios: [
    {
      id: 'cold', name: 'Cold lookup',
      summary: 'Nothing is cached anywhere. The recursive resolver follows <b>NS delegations</b> from the root down, then every layer caches the answer for its TTL.',
      steps: [
        { path: ['app', 'stub'], label: 'A? api.example.com', ms: 0, title: 'The app asks the OS',
          detail: 'The app calls the system resolver library. The OS cache is empty for this name.' },
        { path: ['stub', 'rec'], label: 'A? (UDP :53)', ms: 5, title: 'Stub forwards to the recursive resolver',
          detail: 'DNS uses UDP by default because a query and answer fit in one packet each; it falls back to TCP for large responses. DNS over HTTPS/TLS encrypts this hop for privacy.' },
        { path: ['rec', 'root', 'rec'], label: 'NS for .com?', ms: 10, title: 'Root refers to .com',
          detail: 'Root servers don\'t know the answer; they return an <b>NS referral</b> to the .com TLD servers. Resolvers cache this for a long time, so the root is rarely asked.' },
        { path: ['rec', 'tld', 'rec'], label: 'NS for example.com?', ms: 10, title: 'TLD refers to example.com',
          detail: 'The .com servers delegate to example.com\'s own authoritative name servers. NS records are exactly this delegation.' },
        { path: ['rec', 'auth'], label: 'A? + client subnet', ms: 8, title: 'Ask the authoritative server',
          detail: 'With <b>EDNS Client Subnet</b> the resolver passes a truncated client address, so GeoDNS can pick an answer near the user rather than near the resolver.' },
        { path: ['auth', 'rec', 'stub', 'app'], label: 'A 203.0.113.10 · TTL 60', tone: 'ok', ms: 13, title: 'Answer returned and cached at every layer',
          detail: 'The resolver and the OS keep it for up to the TTL. Uncached lookups cost tens of ms (≈ 45 ms here), which is why hot paths should never resolve per request.' },
      ],
    },
    {
      id: 'cached', name: 'Cached',
      summary: 'Another app on the same network asks for the same name inside the TTL. The recursive resolver answers from memory.',
      steps: [
        { path: ['app', 'stub'], label: 'A? api.example.com', ms: 0, title: 'The app asks the OS',
          detail: 'On a truly hot name the OS cache would answer right here; this time only the resolver has it.' },
        { path: ['stub', 'rec'], label: 'A?', ms: 3, title: 'Query reaches the recursive resolver',
          detail: 'One short UDP round trip to the ISP or public resolver.' },
        { at: 'rec', badge: 'cache hit · TTL 42 s left', tone: 'ok', ms: 0.5, title: 'No walk needed',
          detail: 'The record is still fresh, so the resolver skips root, TLD and authoritative entirely.' },
        { path: ['rec', 'stub', 'app'], label: 'A 203.0.113.10', tone: 'ok', ms: 3, title: 'A few ms in total',
          detail: 'Cached DNS is usually a few ms. Popular names are almost always cached, which is what makes DNS scale.' },
      ],
    },
    {
      id: 'failover', name: 'Failover vs TTL',
      summary: 'The region behind 203.0.113.10 fails and the operator points the record at a healthy region. Clients don\'t see the change until <b>cached copies expire</b>.',
      steps: [
        { at: 'auth', badge: 'A → 198.51.100.7', ms: 0, title: 'Operator changes the record',
          detail: 'The authoritative server now returns the healthy region. But it can\'t reach into caches that already hold the old answer.' },
        { path: ['app', 'stub', 'rec'], label: 'A?', ms: 3, title: 'A client resolves again',
          detail: 'Same query, same path as before.' },
        { at: 'rec', badge: 'old answer, TTL not expired', tone: 'warn', ms: 0.5, title: 'The cache is doing its job',
          detail: 'The resolver serves the cached record until its TTL runs out, and some resolvers and clients hold records even longer than the TTL. A short TTL speeds failover but raises resolver load and lookup latency.' },
        { path: ['rec', 'stub', 'app'], label: 'A 203.0.113.10 (dead)', tone: 'err', ms: 3, title: 'Client is sent to the failed region',
          detail: 'Connections time out until caches expire. DNS is a coarse traffic-shifting tool, not an instant failover switch.' },
        { at: 'app', badge: 'timeout · retry', tone: 'err', ms: 0, title: 'Treat DNS as a dependency',
          detail: 'Set timeouts and cache results. For fast failover, keep the IP stable (an anycast address or a load-balancer VIP) and move traffic behind it, where health checks react in seconds.' },
      ],
    },
  ],
});

/* ---- 1. TCP connection lifecycle ---------------------------------------- */
const LnetTcp = lane([
  { label: 'CLIENT SIDE', nodes: [
    { id: 'attacker', label: 'Attacker', sub: 'spoofed source IPs', kind: 'client', icon: 'alert', row: 0 },
    { id: 'client', label: 'Client', sub: 'ephemeral port', kind: 'client', icon: 'client', row: 1 }] },
  { label: 'SERVER KERNEL', nodes: [
    { id: 'backlog', label: 'SYN queue', sub: 'half-open state', kind: 'queue', icon: 'queue', row: 0 },
    { id: 'accept', label: 'Accept queue', sub: 'established conns', kind: 'queue', icon: 'queue', row: 1 },
    { id: 'rcvbuf', label: 'Receive buffer', sub: 'advertises rwnd', kind: 'queue', icon: 'memory', row: 2 }] },
  { label: 'SERVER APP', nodes: [
    { id: 'server', label: 'Server app', sub: 'listen() · accept()', icon: 'server', row: 1 }] },
]);
defineFlow('flow-tcp', {
  title: 'Live flow: a TCP connection from SYN to TIME_WAIT',
  hint: 'Follow one connection through the server kernel\'s queues, then see how SYN cookies survive a flood and why Nagle plus delayed ACKs adds ~40 ms.',
  zones: LnetTcp.zones, h: LnetTcp.h, nodes: LnetTcp.nodes,
  edges: [
    ['attacker', 'backlog'], ['client', 'backlog'], ['backlog', 'accept'],
    ['accept', 'server'], ['client', 'rcvbuf'], ['rcvbuf', 'server'],
  ],
  scenarios: [
    {
      id: 'life', name: 'Handshake, data, teardown',
      summary: 'One short connection, start to finish. Watch where the server kernel keeps state, and which side pays the <b>TIME_WAIT</b> cost at the end.',
      steps: [
        { path: ['client', 'backlog'], label: 'SYN (seq = x)', ms: 20, title: 'SYN: client picks its initial sequence number',
          detail: 'The ISN is random, so an attacker can\'t guess it and inject segments. The kernel stores a <b>half-open</b> entry in the SYN queue: this memory is what a SYN flood targets.' },
        { path: ['backlog', 'client'], label: 'SYN-ACK (seq = y, ack x+1)', ms: 20, title: 'SYN-ACK: server ISN, acknowledging the client',
          detail: 'The server sends its own ISN and acks x+1, confirming it received the client\'s SYN. Each side now knows the other\'s starting sequence number.' },
        { path: ['client', 'backlog', 'accept'], label: 'ACK (ack y+1)', ms: 0, title: 'ACK: connection established after 1 RTT',
          detail: 'The kernel matches the ACK to the half-open entry and moves the connection to the accept queue. The client can send data along with this ACK, so the handshake costs 1 RTT.' },
        { path: ['accept', 'server'], label: 'accept()', ms: 0, title: 'The application picks it up',
          detail: 'The handshake was done entirely by the kernel. <code>accept()</code> just dequeues a ready connection; if the app is too slow, the accept queue overflows.' },
        { path: ['client', 'rcvbuf', 'server'], label: 'data ≤ min(rwnd, cwnd)', ms: 20, title: 'Data: two windows limit the sender',
          detail: '<b>Flow control</b> protects the receiver: rwnd is the free space it advertises in this buffer. <b>Congestion control</b> protects the network: cwnd. The sender may have min(rwnd, cwnd) bytes unacknowledged.' },
        { path: ['client', 'rcvbuf', 'server'], label: 'FIN', ms: 20, title: 'Client closes first',
          detail: 'Teardown is FIN/ACK in each direction, because each side closes its sending half independently. The server app sees end-of-file.' },
        { path: ['server', 'rcvbuf', 'client'], label: 'ACK · FIN', ms: 20, title: 'Server acks and closes its half',
          detail: 'The server kernel acks the FIN, the app calls <code>close()</code>, and a FIN goes back. The client sends the final ACK.' },
        { at: 'client', badge: 'TIME_WAIT 2×MSL ≈ 60 s', tone: 'warn', ms: 0, title: 'The closing side waits',
          detail: 'The side that closed first holds the 4-tuple for 2×MSL (commonly 60 s on Linux) so stray segments can\'t corrupt a new connection. Thousands of short outbound connections exhaust ephemeral ports this way: use pooling and keep-alive.' },
      ],
    },
    {
      id: 'flood', name: 'SYN flood + SYN cookies',
      summary: 'An attacker sends SYNs from spoofed addresses and never completes the handshake. <b>SYN cookies</b> let the kernel keep serving real clients without storing anything.',
      steps: [
        { path: ['attacker', 'backlog'], label: '10k spoofed SYNs/s', tone: 'err', ms: 1, title: 'Half-open entries pile up',
          detail: 'Each SYN creates a half-open entry and a SYN-ACK to an address that will never answer. Entries linger until they time out, so the SYN queue fills.' },
        { at: 'backlog', badge: 'queue full → cookies on', tone: 'warn', ms: 0, title: 'Kernel switches to stateless mode',
          detail: 'Instead of dropping new SYNs, the kernel stops storing half-open state and encodes it into the ISN it sends back.' },
        { path: ['client', 'backlog'], label: 'SYN', ms: 20, title: 'A real client arrives',
          detail: 'Without cookies this SYN would be dropped and the client would back off and retry for seconds.' },
        { path: ['backlog', 'client'], label: 'SYN-ACK (seq = cookie)', ms: 20, title: 'The ISN is the state',
          detail: 'The cookie is a keyed hash of the 4-tuple and a timestamp, plus the encoded MSS. Nothing is written to memory.' },
        { path: ['client', 'backlog', 'accept'], label: 'ACK (ack cookie+1)', tone: 'ok', ms: 0, title: 'Cookie validated, connection rebuilt',
          detail: 'Only a host that really received the SYN-ACK can echo the cookie back, so spoofed sources never get this far. The kernel verifies it and places the connection in the accept queue.' },
        { path: ['accept', 'server'], label: 'accept()', tone: 'ok', ms: 0, title: 'The real client is served',
          detail: 'The flood still costs bandwidth and CPU, but it no longer exhausts memory. Some TCP options are lost in cookie mode, which is why it only switches on under pressure.' },
      ],
    },
    {
      id: 'nagle', name: 'Nagle + delayed ACK',
      summary: 'A client sends a request as two small writes (header, then body). Two reasonable optimisations interact and add <b>~40 ms</b> to every request.',
      steps: [
        { path: ['client', 'rcvbuf', 'server'], label: 'small write #1 (header)', ms: 20, title: 'First small segment goes out',
          detail: 'Nothing is unacknowledged yet, so Nagle lets it go immediately.' },
        { at: 'client', badge: 'Nagle holds write #2', tone: 'warn', ms: 0, title: 'Nagle batches small writes',
          detail: 'Nagle\'s algorithm won\'t send another small segment while earlier data is unacknowledged. It saves bandwidth on chatty links by coalescing tiny writes.' },
        { at: 'server', badge: 'delayed ACK', tone: 'warn', ms: 40, title: 'The server delays its ACK',
          detail: 'The receiver waits (≈ 40 ms) hoping to piggyback the ACK on a response. But the app can\'t respond, because half the request is still stuck on the client: each side waits for the other.' },
        { path: ['server', 'rcvbuf', 'client'], label: 'ACK (timer fired)', ms: 20, title: 'The delayed-ACK timer finally fires',
          detail: 'The stall ends only because a timer expired, adding ~40 ms to a request that should take one RTT.' },
        { path: ['client', 'rcvbuf', 'server'], label: 'write #2 (body)', ms: 20, title: 'Now the second write goes',
          detail: 'The request is finally complete and the server can reply.' },
        { at: 'client', badge: 'TCP_NODELAY', tone: 'ok', ms: 0, title: 'The fix: disable Nagle',
          detail: 'Latency-sensitive RPC stacks set <code>TCP_NODELAY</code> so small writes go out immediately. Writing the whole request in one call also avoids the stall.' },
      ],
    },
  ],
});

/* ---- 4. Layer 4 vs Layer 7 load balancing, and DSR ----------------------- */
const LnetLb = lane([
  { label: 'CLIENT', nodes: [
    { id: 'client', label: 'Client', sub: 'connects to the VIP', kind: 'client', icon: 'client', row: 1 }] },
  { label: 'BALANCERS', nodes: [
    { id: 'l4', label: 'L4 LB', sub: 'Maglev · 5-tuple hash', icon: 'lb', row: 0 },
    { id: 'l7', label: 'L7 proxy', sub: 'Envoy · GFE', icon: 'proxy', row: 2 }] },
  { label: 'BACKENDS', nodes: [
    { id: 'b1', label: 'Backend 1', sub: 'NAT mode', icon: 'server', row: 0 },
    { id: 'b2', label: 'Backend 2', sub: 'VIP on loopback', icon: 'server', row: 1 },
    { id: 'b3', label: 'Backend 3', icon: 'server', row: 2 },
    { id: 'b4', label: 'Backend 4', icon: 'server', row: 3 }] },
]);
defineFlow('flow-lb-l4-l7', {
  title: 'Live flow: L4 vs L7 load balancing',
  hint: 'Compare a packet forwarder with a proxy that reads HTTP: which one can spread gRPC requests, and how Direct Server Return keeps huge responses off the balancer.',
  zones: LnetLb.zones, h: LnetLb.h, nodes: LnetLb.nodes,
  edges: [
    ['client', 'l4'], ['client', 'l7'],
    ['l4', 'b1'], ['l4', 'b2'],
    ['l7', 'b3'], ['l7', 'b2'], ['l7', 'b4'],
    ['b2', 'client'],
  ],
  scenarios: [
    {
      id: 'l4', name: 'L4 forwarding (NAT)',
      summary: 'An L4 balancer decides on IP and port alone and forwards packets <b>without reading HTTP</b>. Very fast and protocol-agnostic, but it can\'t route by URL or header.',
      steps: [
        { path: ['client', 'l4'], label: 'SYN to VIP:443', ms: 5, title: 'Client connects to the virtual IP',
          detail: 'The VIP belongs to the balancer tier, not to any one server. The TLS inside stays opaque to the balancer.' },
        { at: 'l4', badge: 'hash(5-tuple) → Backend 1', ms: 0.1, title: 'Pick a backend from the 5-tuple',
          detail: 'Maglev uses <b>consistent hashing</b> on source/destination IP, ports and protocol, so every packet of this connection maps to the same backend, even if a balancer machine is added or removed.' },
        { path: ['l4', 'b1'], label: 'packets (NAT)', ms: 1, title: 'Packets forwarded, not parsed',
          detail: 'The balancer rewrites addresses and forwards. The backend terminates TCP and TLS itself.' },
        { path: ['b1', 'l4', 'client'], label: 'response via LB', ms: 6, title: 'The response returns through the balancer',
          detail: 'In NAT mode, replies must flow back through the LB to undo the address rewrite. For large responses this return path becomes the bottleneck (see Direct Server Return).' },
        { path: ['client', 'l4', 'b1'], label: 'every later request', tone: 'warn', ms: 6, title: 'The whole connection is pinned',
          detail: 'The L4 LB balances <b>connections</b>, not requests. Every request on this connection lands on Backend 1, however busy it gets.' },
      ],
    },
    {
      id: 'l7', name: 'L7 per-request gRPC',
      summary: 'gRPC multiplexes many requests on one long-lived HTTP/2 connection. An L7 proxy <b>terminates the connection</b> and balances each stream separately.',
      steps: [
        { path: ['client', 'l7'], label: 'TLS + HTTP/2 connection', ms: 10, title: 'One connection to the proxy',
          detail: 'The proxy terminates TCP and TLS. In practice an L4 tier often sits in front of it (the GFE does L4, then L7).' },
        { at: 'l7', badge: 'decrypt · read :path', ms: 0.5, title: 'The proxy reads HTTP',
          detail: 'It can now route on path and headers, retry, rate-limit, run a WAF and check auth. The cost is CPU and one extra hop.' },
        { path: ['l7', 'b3'], label: 'stream 1', ms: 1, title: 'Request 1 → Backend 3',
          detail: 'The proxy keeps its own pooled connections to backends and picks one per request, e.g. least outstanding requests.' },
        { path: ['l7', 'b2'], label: 'stream 3', ms: 1, title: 'Request 2 → Backend 2',
          detail: 'Same client connection, different backend. At L4 this would be impossible, because both streams share one 5-tuple.' },
        { path: ['l7', 'b4'], label: 'stream 5', ms: 1, title: 'Request 3 → Backend 4',
          detail: 'Load spreads across the fleet even though the client opened a single connection.' },
        { path: ['b4', 'l7', 'client'], label: 'responses (multiplexed)', tone: 'ok', ms: 10, title: 'Responses stream back on the one connection',
          detail: 'This is why gRPC needs L7 or <b>client-side</b> load balancing: behind a plain L4 LB one busy client pins all its traffic to one backend.' },
      ],
    },
    {
      id: 'dsr', name: 'Direct Server Return',
      summary: 'Small request in, huge response out, as with video. With <b>DSR</b> the balancer only handles the inbound direction and the backend answers the client directly.',
      steps: [
        { path: ['client', 'l4'], label: 'GET /video', ms: 5, title: 'A small request reaches the VIP',
          detail: 'Inbound traffic is tiny compared with what goes back out.' },
        { at: 'l4', badge: 'rewrite dst MAC only', ms: 0.1, title: 'Only the destination MAC changes',
          detail: 'The IP packet is untouched, so it still says "to VIP". That only works if the backend is on the same L2 segment, or reached through a tunnel.' },
        { path: ['l4', 'b2'], label: 'frame to Backend 2', ms: 1, title: 'Forwarded at layer 2',
          detail: 'Backend 2 has the VIP configured on its loopback interface, so it accepts a packet addressed to the VIP as its own.' },
        { path: ['b2', 'client'], label: '5 GB response, direct', tone: 'ok', ms: 50, title: 'The backend replies straight to the client',
          detail: 'It answers from the VIP, so the client can\'t tell. The balancer never sees the response bytes, so it scales with inbound traffic only.' },
        { at: 'l4', badge: 'no response signal', tone: 'warn', ms: 0, title: 'The trade-off',
          detail: 'Because responses bypass the LB, it can\'t use response-based health signals such as error rates or latency. It needs separate health checks.' },
      ],
    },
  ],
});
}
