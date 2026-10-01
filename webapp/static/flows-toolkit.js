/* Live flows for the toolkit module (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ======================== Tool-Kit 12: service mesh sidecar mTLS request == */
const LtkBMesh = lane([
  { label: 'CALLERS', nodes: [
    { id: 'appa', label: 'frontend', sub: 'sa: frontend', icon: 'app', row: 1 },
    { id: 'rogue', label: 'batch job', sub: 'sa: batch', icon: 'worker', row: 2 }] },
  { label: 'ISTIOD · CALLER PROXY', nodes: [
    { id: 'istiod', label: 'istiod', sub: 'xDS + CA', icon: 'scheduler', row: 0 },
    { id: 'pxa', label: 'Envoy', sub: 'outbound :15001', icon: 'proxy', row: 1 }] },
  { label: 'REVIEWS SIDECARS', nodes: [
    { id: 'pxb2', label: 'Envoy', sub: 'reviews-2 :15006', icon: 'proxy', row: 0 },
    { id: 'pxb1', label: 'Envoy', sub: 'reviews-1 :15006', icon: 'proxy', row: 2 }] },
  { label: 'REVIEWS APPS', nodes: [
    { id: 'rv2', label: 'reviews-2', sub: 'plain HTTP :9080', icon: 'app', row: 0 },
    { id: 'rv1', label: 'reviews-1', sub: 'plain HTTP :9080', icon: 'app', row: 2 }] },
]);
defineFlow('flow-mesh-mtls', {
  title: 'Live flow: one call through two sidecars, with mTLS, authorization and retries',
  hint: 'Follow an allowed call end to end, then a caller the policy rejects, then a failing pod that is retried around and ejected.',
  zones: LtkBMesh.zones, h: LtkBMesh.h, nodes: LtkBMesh.nodes,
  edges: [
    ['appa', 'pxa'], ['pxa', 'pxb1'], ['pxa', 'pxb2'], ['pxb1', 'rv1'], ['pxb2', 'rv2'],
    ['istiod', 'pxa', { async: true }], ['istiod', 'pxb2', { async: true }], ['rogue', 'pxb1'],
  ],
  scenarios: [
    {
      id: 'allowed', name: 'Allowed call',
      summary: 'The frontend calls <code>http://reviews/1</code> in plain HTTP. <b>Both sidecars do the security work</b>: mTLS on the wire, identity checks at each end, and the app code knows nothing about it.',
      steps: [
        { path: ['istiod', 'pxa'], label: 'xDS + SDS cert', async: true, ms: 0, title: 'Before any request: config and certificates',
          detail: 'istiod has already pushed routes and endpoints over xDS, and signed a 24 h certificate whose SAN is <code>spiffe://cluster.local/ns/shop/sa/frontend</code>. The private key never left the pod.' },
        { path: ['appa', 'pxa'], label: 'GET /reviews/1', ms: 0.05, title: 'The app sends plain HTTP',
          detail: 'The app connects to <code>reviews:9080</code>. iptables rules in the pod redirect the connection to Envoy on port 15001, and Envoy recovers the original destination.' },
        { at: 'pxa', badge: 'route → reviews-1', ms: 0.1, title: 'Outbound Envoy picks a destination',
          detail: 'The VirtualService picks the subset (90% v1 here), the load balancer picks a healthy endpoint, and a 2 s timeout starts.' },
        { path: ['pxa', 'pxb1'], label: 'mTLS handshake', ms: 1, title: 'Mutual TLS between the sidecars',
          detail: 'Each side shows its certificate. The caller checks that it reached a <code>reviews</code> identity, and the server learns the caller is <code>sa/frontend</code>. Connections are pooled, so later requests skip this handshake.' },
        { at: 'pxb1', badge: 'AuthorizationPolicy: ALLOW', tone: 'ok', ms: 0.05, title: 'Inbound Envoy authorizes by identity',
          detail: 'The policy allows principal <code>cluster.local/ns/shop/sa/frontend</code> to call <code>GET /reviews/*</code>. The source IP is ignored because pod IPs change all the time.' },
        { path: ['pxb1', 'rv1'], label: 'plain HTTP, localhost', ms: 0.05, title: 'Handed to the app',
          detail: 'Decrypted traffic only travels over the pod\'s loopback interface. The reviews app sees an ordinary HTTP request.' },
        { path: ['rv1', 'pxb1', 'pxa', 'appa'], label: '200 OK', tone: 'ok', ms: 1.5, title: 'The response returns the same way',
          detail: 'Both proxies record metrics (<code>istio_requests_total</code>, duration) and a span each. Across the two proxy hops the added latency is usually well under a few milliseconds (≈).' },
      ],
    },
    {
      id: 'denied', name: 'Denied caller',
      summary: 'A batch job in another namespace tries to call reviews. <b>STRICT mTLS stops plain text; AuthorizationPolicy stops the wrong identity.</b>',
      steps: [
        { path: ['rogue', 'pxb1'], label: 'plain-text TCP', tone: 'err', ms: 0.5, title: 'No sidecar, no certificate',
          detail: 'The workload has no mesh certificate. With <code>PeerAuthentication</code> in STRICT mode, the inbound Envoy only accepts mTLS, so the connection is reset. In PERMISSIVE mode it would have been accepted.' },
        { at: 'rogue', badge: 'injected sidecar', ms: 0, title: 'The job joins the mesh',
          detail: 'Now it has an identity, <code>spiffe://cluster.local/ns/batch/sa/batch</code>.' },
        { path: ['rogue', 'pxb1'], label: 'mTLS ok', ms: 1, title: 'Authentication succeeds',
          detail: 'mTLS proves <em>who</em> is calling. It does not decide whether they may.' },
        { at: 'pxb1', badge: 'no rule matches', tone: 'err', ms: 0.05, title: 'Authorization fails',
          detail: 'A policy selects reviews, so anything that no ALLOW rule matches is denied. <code>sa/batch</code> is not listed.' },
        { path: ['pxb1', 'rogue'], label: '403 RBAC: access denied', tone: 'err', ms: 0.2, title: 'Denied at the destination sidecar',
          detail: 'The reviews app never sees the request. The denial shows up in the sidecar\'s access log and metrics, so a security team can alert on it.' },
      ],
    },
    {
      id: 'retry', name: 'Retry and ejection',
      summary: 'reviews-1 starts failing. <b>The caller\'s sidecar retries on another pod</b>, and outlier detection removes the bad pod for a while.',
      steps: [
        { path: ['appa', 'pxa'], label: 'GET /reviews/7', ms: 0.05, title: 'A normal call',
          detail: 'Same path as before: captured by iptables and handed to the outbound Envoy.' },
        { path: ['pxa', 'pxb1', 'rv1'], label: 'attempt 1', ms: 2, title: 'Sent to reviews-1',
          detail: 'The retry policy is <code>attempts: 2, perTryTimeout: 500ms, retryOn: 503,connect-failure</code>.' },
        { path: ['rv1', 'pxb1', 'pxa'], label: '503', tone: 'err', ms: 1, title: 'reviews-1 fails',
          detail: 'Its database pool is exhausted, so it returns 503.' },
        { at: 'pxa', badge: 'retry on another host', tone: 'warn', ms: 25, title: 'Envoy retries with backoff',
          detail: 'A GET is idempotent, so a retry is safe. Envoy waits a short jittered backoff (≈25 ms base) and avoids the host that just failed. Retrying a <code>POST /charge</code> here would risk a double charge.' },
        { path: ['pxa', 'pxb2', 'rv2'], label: 'attempt 2', ms: 3, title: 'Sent to reviews-2',
          detail: 'reviews-2 is healthy.' },
        { path: ['rv2', 'pxb2', 'pxa', 'appa'], label: '200 OK', tone: 'ok', ms: 2, title: 'The user never sees the failure',
          detail: 'The frontend gets a 200, about 30 ms later than usual. The retry is counted in the metrics, so the failure is still visible to operators.' },
        { at: 'pxb1', badge: 'ejected for 30 s', tone: 'warn', ms: 0, title: 'Outlier detection ejects reviews-1',
          detail: 'After 5 consecutive 5xx, the caller\'s Envoy stops sending to reviews-1 for 30 s, and longer each time it happens again. <code>maxEjectionPercent</code> ensures a bad pod cannot empty the whole pool.' },
      ],
    },
  ],
});

/* ======================== Tool-Kit 11: Vault dynamic database credentials == */
const LtkBVault = lane([
  { label: 'APP POD', nodes: [
    { id: 'agent', label: 'Vault Agent', sub: 'login, renew, render', icon: 'worker', row: 1 },
    { id: 'app', label: 'orders app', sub: 'reads a file', icon: 'app', row: 2 }] },
  { label: 'VAULT', nodes: [
    { id: 'vauth', label: 'K8s auth', sub: 'role: orders', icon: 'auth', row: 0 },
    { id: 'dbeng', label: 'DB engine', sub: 'orders-readwrite', icon: 'key', row: 1 },
    { id: 'lease', label: 'Lease manager', sub: 'TTL 1h, max 24h', icon: 'timer', row: 2 }] },
  { label: 'BACKENDS', nodes: [
    { id: 'kapi', label: 'Kubernetes API', sub: 'TokenReview', icon: 'k8s', row: 0 },
    { id: 'pg', label: 'PostgreSQL', sub: 'orders DB', kind: 'db', row: 1 }] },
]);
defineFlow('flow-vault-lease', {
  title: 'Live flow: Vault dynamic database credentials, from login to revocation',
  hint: 'Watch a pod log in with its service account and receive a brand-new database user, keep it alive with renewals, and lose it instantly in an incident.',
  zones: LtkBVault.zones, h: LtkBVault.h, nodes: LtkBVault.nodes,
  edges: [
    ['agent', 'vauth'], ['vauth', 'kapi'], ['agent', 'dbeng'], ['dbeng', 'pg'],
    ['agent', 'app'], ['dbeng', 'lease'], ['agent', 'lease'], ['lease', 'pg'],
  ],
  scenarios: [
    {
      id: 'issue', name: 'Login and credentials',
      summary: 'No password is stored anywhere in the pod. <b>The pod proves its identity with its service account token</b>, then gets a database user created just for it.',
      steps: [
        { at: 'agent', badge: 'SA token (JWT)', ms: 0, title: 'Start from platform identity',
          detail: 'Kubernetes mounts a short-lived, audience-bound service account token in the pod. This solves "secret zero": the pod has something to prove who it is without anyone storing a password.' },
        { path: ['agent', 'vauth'], label: 'login role=orders', ms: 5, title: 'Log in to Vault',
          detail: '<code>POST /v1/auth/kubernetes/login</code> with the JWT and the Vault role name.' },
        { path: ['vauth', 'kapi', 'vauth'], label: 'TokenReview', ms: 10, title: 'Vault asks Kubernetes if the token is real',
          detail: 'The API server confirms the token is valid and belongs to <code>ns=orders, sa=orders</code>. The Vault role only accepts that exact pair.' },
        { path: ['vauth', 'agent'], label: 'Vault token + policy', tone: 'ok', ms: 1, title: 'A Vault token with a narrow policy',
          detail: 'The token can only read <code>database/creds/orders-readwrite</code> and <code>secret/data/orders/*</code>, and it has its own TTL.' },
        { path: ['agent', 'dbeng'], label: 'read creds', ms: 2, title: 'Ask for database credentials',
          detail: '<code>GET /v1/database/creds/orders-readwrite</code>' },
        { path: ['dbeng', 'pg'], label: 'CREATE ROLE v-orders-x7…', ms: 15, title: 'Vault creates a brand-new database user',
          detail: 'Vault runs the role\'s <code>creation_statements</code> as its admin user: a random name and password, <code>VALID UNTIL</code> the expiry, and only the grants this role defines.' },
        { path: ['dbeng', 'lease'], label: 'lease 1h / max 24h', ms: 1, title: 'A lease is recorded',
          detail: 'Every dynamic secret has a lease ID. When the lease ends, Vault runs the revocation statements.' },
        { path: ['dbeng', 'agent', 'app'], label: 'user + password → file', tone: 'ok', ms: 2, title: 'The app reads a file',
          detail: 'Vault Agent writes the credentials to <code>/vault/secrets/db</code> on a shared in-memory volume. The app connects as its own unique user, so <code>pg_stat_activity</code> shows exactly which pod is doing what.' },
      ],
    },
    {
      id: 'renew', name: 'Renew, then rotate',
      summary: 'Leases are kept alive by renewal until they reach the max TTL. <b>Then the credentials rotate</b>, and the app has to switch to the new ones.',
      steps: [
        { path: ['agent', 'lease'], label: 'renew (+1h)', tone: 'ok', ms: 3, title: 'Renew before expiry',
          detail: 'At about two-thirds of the TTL the agent renews the lease. The same username keeps working, and nothing changes for the app.' },
        { at: 'lease', badge: 'max TTL 24h reached', tone: 'warn', ms: 0, title: 'Renewals cannot go past max_ttl',
          detail: 'This caps how long any single credential can live, however well it is looked after.' },
        { path: ['agent', 'dbeng'], label: 'read new creds', ms: 2, title: 'Fetch a fresh credential',
          detail: 'The agent requests a new lease before the old one expires.' },
        { path: ['dbeng', 'pg'], label: 'CREATE ROLE v-orders-k2…', ms: 15, title: 'A second user exists for a while',
          detail: 'The old and new credentials overlap, which is what makes the rotation zero-downtime.' },
        { path: ['agent', 'app'], label: 're-render file', ms: 1, badgeAt: 'app', badge: 'pool reconnects', tone: 'warn', title: 'The app switches over',
          detail: 'The app has to notice the change: watch the file, reload on a signal, or let the agent restart it. If the app caches the password forever, it fails at the next expiry.' },
        { path: ['lease', 'pg'], label: 'DROP ROLE v-orders-x7…', tone: 'ok', ms: 10, title: 'The old user is removed on expiry',
          detail: 'A copy of the old credential that leaked somewhere is now worthless.' },
      ],
    },
    {
      id: 'revoke', name: 'Incident: revoke',
      summary: 'A pod is compromised and its credentials may have been copied. <b>One command invalidates every credential of the role</b>, and healthy pods simply fetch new ones.',
      steps: [
        { at: 'app', badge: 'pod compromised', tone: 'err', ms: 0, title: 'Assume the credentials are stolen',
          detail: 'An attacker read <code>/vault/secrets/db</code>. With a static password this would mean a manual rotation across every service that shares it.' },
        { at: 'lease', badge: 'lease revoke -prefix', tone: 'warn', ms: 0, title: 'The operator revokes the role\'s leases',
          detail: '<code>vault lease revoke -prefix database/creds/orders-readwrite</code>. Every audit log entry already records which pod received which lease.' },
        { path: ['lease', 'pg'], label: 'DROP ROLE (all)', tone: 'ok', ms: 30, title: 'Vault drops every user it issued',
          detail: 'The revocation statements also end their open sessions, so the stolen username and password stop working immediately.' },
        { at: 'pg', badge: 'stolen creds rejected', tone: 'ok', ms: 0, title: 'The leak is contained',
          detail: 'Nobody had to find every copy of the secret. The database no longer knows that user.' },
        { path: ['agent', 'dbeng'], label: 'read new creds', ms: 2, title: 'Healthy pods recover by themselves',
          detail: 'Their agents see the lease is gone and request new credentials. The compromised pod is deleted, and its service account can be blocked in the Vault role.' },
        { path: ['dbeng', 'pg'], label: 'CREATE ROLE (fresh)', tone: 'ok', ms: 15, title: 'Back in service',
          detail: 'Expect a short error spike while pools reconnect, which is why revocation is a deliberate incident step rather than something that runs on a timer.' },
      ],
    },
  ],
});

/* ============================== Tool-Kit 02: Kubernetes scheduling + rollout == */
const LtkAK8s = lane([
  { label: 'YOU', nodes: [{ id: 'kubectl', label: 'kubectl', sub: 'or CI / Argo CD', kind: 'client', icon: 'cli', row: 1 }] },
  { label: 'CONTROL PLANE', nodes: [
    { id: 'ctrl', label: 'Controllers', sub: 'Deployment · RS', icon: 'process', row: 0 },
    { id: 'api', label: 'API server', sub: 'stores in etcd', icon: 'api', row: 1 },
    { id: 'sched', label: 'Scheduler', sub: 'filter · score', icon: 'scheduler', row: 2 }] },
  { label: 'NODE', nodes: [{ id: 'kubelet', label: 'kubelet', sub: 'node-b agent', icon: 'worker', row: 1 }] },
  { label: 'PODS', nodes: [
    { id: 'old', label: 'v1 Pods', sub: '3 ready', icon: 'container', row: 0 },
    { id: 'new', label: 'v2 Pod', sub: 'new ReplicaSet', icon: 'container', row: 2 }] },
  { label: 'TRAFFIC', nodes: [{ id: 'svc', label: 'Service', sub: 'EndpointSlice', icon: 'lb', row: 1 }] },
]);
defineFlow('flow-k8s-rollout', {
  title: 'Live flow: a Pod gets scheduled, then a rolling update replaces v1 with v2',
  hint: 'Every arrow into the control plane is a watch: nobody calls anybody directly. Follow one Pod from apply to traffic, then a full rolling update, then a bad image that stalls safely.',
  zones: LtkAK8s.zones, h: LtkAK8s.h, nodes: LtkAK8s.nodes,
  edges: [
    ['kubectl', 'api'], ['api', 'ctrl'], ['api', 'sched'], ['api', 'kubelet'],
    ['kubelet', 'old'], ['kubelet', 'new'], ['svc', 'old'], ['svc', 'new'],
  ],
  scenarios: [
    {
      id: 'schedule', name: 'Apply → Pod serving',
      summary: 'Scale <code>checkout</code> from 3 to 4 replicas and follow the new Pod. <b>Apply returns as soon as the desired state is stored</b>; everything after that is controllers reacting to watch events.',
      steps: [
        { path: ['kubectl', 'api'], label: 'PATCH replicas: 4', ms: 30, title: 'The desired state is written',
          detail: 'The API server authenticates the caller, checks RBAC, runs admission (mutating, then validating), validates the schema and writes the Deployment to etcd. <code>kubectl</code> gets 200 OK now, before anything runs.' },
        { path: ['api', 'ctrl', 'api'], label: 'create Pod', ms: 20, title: 'Controllers close the gap',
          detail: 'The Deployment controller sees the change and bumps its ReplicaSet to 4. The ReplicaSet controller counts 3 Pods, wants 4, and creates one Pod object with no <code>nodeName</code> yet.' },
        { path: ['api', 'sched', 'api'], label: 'bind → node-b', ms: 10, title: 'The scheduler picks a node',
          detail: '<b>Filter:</b> drop nodes whose free allocatable CPU/memory cannot fit the Pod\'s <i>requests</i>, or with taints it does not tolerate. <b>Score:</b> prefer spreading replicas across zones and nodes that already have the image. Then write the binding.' },
        { path: ['api', 'kubelet'], label: 'watch: Pod bound', ms: 5, title: 'The node\'s kubelet notices',
          detail: 'The kubelet on node-b watches for Pods bound to it. It does not wait to be told; it sees the binding appear in its watch stream.' },
        { path: ['kubelet', 'new'], label: 'pull · CRI · CNI', badgeAt: 'new', badge: 'Running, not Ready', tone: 'warn', ms: 2500, title: 'Image pulled, container started',
          detail: 'containerd pulls the image (skipped if cached), creates the Pod sandbox, the CNI plugin assigns a Pod IP, and the containers start. The ≈2.5 s is illustrative; image size dominates it.' },
        { at: 'new', badge: 'readiness passed → Ready', tone: 'ok', ms: 5000, title: 'Readiness probe passes',
          detail: 'Until the startup and readiness probes pass, the Pod receives no traffic. A slow warm-up (JIT, caches, connection pools) is exactly what readiness protects callers from.' },
        { at: 'svc', badge: 'endpoint added', tone: 'ok', ms: 200, title: 'EndpointSlice updated, traffic arrives',
          detail: 'The EndpointSlice controller adds the Pod IP; kube-proxy on every node reprograms its iptables/nftables rules. Only now does <code>http://checkout</code> reach the new Pod.' },
      ],
    },
    {
      id: 'rolling', name: 'Rolling update (surge 1, unavailable 0)',
      summary: 'A new image changes the Pod template, so the Deployment creates a <b>second ReplicaSet</b> and shifts Pods one at a time. With <code>maxSurge: 1, maxUnavailable: 0</code>, capacity never drops below 3.',
      steps: [
        { path: ['kubectl', 'api'], label: 'set image :1.9.0', ms: 30, title: 'Template changed',
          detail: 'Any change under <code>spec.template</code> (image, env, resources) triggers a rollout. Changing only <code>replicas</code> does not.' },
        { path: ['api', 'ctrl', 'api'], label: 'new RS = 1', ms: 20, title: 'Surge: one extra Pod',
          detail: 'The controller creates ReplicaSet v2 with 1 replica. Total Pods = 4, allowed by <code>maxSurge: 1</code>.' },
        { path: ['api', 'kubelet', 'new'], label: 'schedule + start', badgeAt: 'new', badge: 'starting', ms: 3000, title: 'v2 Pod scheduled and started',
          detail: 'Same path as the first scenario: scheduler binds, kubelet pulls and starts, probes run.' },
        { path: ['svc', 'new'], label: 'Ready → endpoint', badgeAt: 'new', badge: 'v2 serving', tone: 'ok', ms: 5000, title: 'Readiness gates progress',
          detail: 'The rollout does not advance until the v2 Pod is Ready. For a while v1 and v2 serve side by side, so v2 must be backward compatible with v1\'s data and API.' },
        { path: ['api', 'kubelet', 'old'], label: 'delete one v1', badgeAt: 'old', badge: 'terminating', tone: 'warn', ms: 50, title: 'Scale v1 down by one',
          detail: 'Two things now run in parallel: the endpoint is removed from every node, and the kubelet starts <code>preStop</code> then sends SIGTERM.' },
        { path: ['svc', 'old'], label: 'endpoint removed', badgeAt: 'old', badge: 'preStop sleep 5 s', ms: 5000, title: 'The endpoint race',
          detail: 'If the app exited on SIGTERM right away, nodes that have not yet updated their rules would still send it requests: 502s on every deploy. The preStop sleep lets removal propagate; then the app drains in-flight requests and exits.' },
        { at: 'ctrl', badge: 'repeat ×2 → v2 = 3, v1 = 0', tone: 'ok', ms: 16000, title: 'Repeat until done',
          detail: 'Surge one, wait for Ready, remove one, twice more. The old ReplicaSet is kept at 0 replicas (up to <code>revisionHistoryLimit</code>) so <code>kubectl rollout undo</code> is instant.' },
      ],
    },
    {
      id: 'bad', name: 'Bad release stalls safely',
      summary: 'v2 crashes on start. Because <code>maxUnavailable: 0</code>, <b>no v1 Pod is removed until a v2 Pod is Ready</b>, so users never notice. The rollout just stops.',
      steps: [
        { path: ['kubectl', 'api', 'ctrl'], label: 'set image :1.9.1', ms: 50, title: 'A broken build is rolled out',
          detail: 'Say 1.9.1 reads a config key that does not exist and exits with code 1.' },
        { path: ['api', 'kubelet', 'new'], label: 'start v2', badgeAt: 'new', badge: 'exit 1', tone: 'err', ms: 3000, title: 'The new Pod dies',
          detail: 'The container exits; the kubelet restarts it with exponential back-off (10 s, 20 s, 40 s … capped at 5 min). Status: <code>CrashLoopBackOff</code>.' },
        { at: 'old', badge: 'still 3 v1 serving', tone: 'ok', ms: 0, title: 'Capacity is untouched',
          detail: 'The controller may not remove a v1 Pod: that would make available replicas drop below 3. Readiness is the safety interlock.' },
        { at: 'ctrl', badge: 'Progressing=False', tone: 'warn', title: 'Progress deadline exceeded',
          detail: 'After <code>progressDeadlineSeconds</code> (default 600 s) the Deployment reports <code>ProgressDeadlineExceeded</code>. <code>kubectl rollout status</code> exits non-zero, so CI or Argo CD can alert and roll back.' },
        { path: ['kubectl', 'api', 'ctrl'], label: 'rollout undo', ms: 50, title: 'Roll back',
          detail: 'Undo points the Deployment at the previous ReplicaSet template. Debug with <code>kubectl logs --previous</code> on the failed Pod.' },
        { path: ['api', 'kubelet', 'new'], label: 'delete v2 Pod', badgeAt: 'new', badge: 'gone', tone: 'ok', ms: 100, title: 'Back to a clean v1',
          detail: 'The v2 ReplicaSet scales to 0. With <code>maxUnavailable: 25%</code> instead, one v1 Pod would already have been removed, and you would be serving on 2 of 3 Pods throughout.' },
      ],
    },
  ],
});

/* ======================== Tool-Kit 04: Kafka consumer-group rebalance == */
const LtkAKafka = lane([
  { label: 'TOPIC orders · 4 PARTITIONS', nodes: [
    { id: 'p0', label: 'P0', sub: 'leader broker 1', icon: 'topic', row: 0 },
    { id: 'p1', label: 'P1', sub: 'leader broker 2', icon: 'topic', row: 1 },
    { id: 'p2', label: 'P2', sub: 'leader broker 3', icon: 'topic', row: 2 },
    { id: 'p3', label: 'P3', sub: 'leader broker 1', icon: 'topic', row: 3 }] },
  { label: 'GROUP payments', nodes: [
    { id: 'c1', label: 'Consumer 1', sub: 'owns P0, P1', icon: 'worker', row: 0 },
    { id: 'c3', label: 'Consumer 3', sub: 'new instance', icon: 'worker', row: 1.5 },
    { id: 'c2', label: 'Consumer 2', sub: 'owns P2, P3', icon: 'worker', row: 3 }] },
  { label: 'BROKER SIDE', nodes: [
    { id: 'coord', label: 'Coordinator', sub: 'group + offsets', icon: 'sync', row: 1.5 }] },
]);
defineFlow('flow-kafka-rebalance', {
  title: 'Live flow: a Kafka consumer group rebalances when members join or die',
  hint: 'Each partition belongs to exactly one member of the group. Watch which partitions stop while ownership moves, and where duplicates come from.',
  zones: LtkAKafka.zones, h: LtkAKafka.h, nodes: LtkAKafka.nodes,
  edges: [
    ['p0', 'c1'], ['p1', 'c1'], ['p1', 'c3'], ['p2', 'c2'], ['p3', 'c2'],
    ['c1', 'coord'], ['c3', 'coord'], ['c2', 'coord'],
  ],
  scenarios: [
    {
      id: 'join', name: 'Scale out (KIP-848)',
      summary: 'A third consumer starts. With the Kafka 4.0 consumer protocol (<code>group.protocol=consumer</code>), the coordinator moves <b>only P1</b>; P0, P2 and P3 never stop.',
      steps: [
        { path: ['c3', 'coord'], label: 'heartbeat: join, subscribe orders', ms: 5, title: 'The new member joins',
          detail: 'In the new protocol, joining is just a heartbeat that carries the subscription. No JoinGroup/SyncGroup barrier for the whole group.' },
        { at: 'coord', badge: 'epoch 7 → 8, target: P1 → C3', ms: 1, title: 'Coordinator computes the target assignment',
          detail: 'The broker-side assignor (uniform by default) balances 4 partitions over 3 members: C1 {P0}, C3 {P1}, C2 {P2, P3}. Only P1 has to move.' },
        { path: ['coord', 'c1'], label: 'revoke P1', badgeAt: 'c1', badge: 'revoking P1', tone: 'warn', ms: 5, title: 'C1 is asked to give up P1',
          detail: 'C1 learns this in its next heartbeat response. P0 keeps flowing the whole time.' },
        { path: ['c1', 'coord'], label: 'commit P1 @ 812, ack', ms: 10, title: 'C1 commits and releases',
          detail: 'C1 finishes the in-flight P1 records, commits offset 812 (the next record to read), stops fetching P1 and acknowledges the revocation. Committing here is what prevents duplicates.' },
        { path: ['coord', 'c3'], label: 'assign P1', badgeAt: 'c3', badge: 'owns P1', tone: 'ok', ms: 5, title: 'P1 goes to C3',
          detail: 'Only after C1 has released it. A partition is never owned by two members of the same group at once.' },
        { path: ['p1', 'c3'], label: 'fetch from 812', tone: 'ok', ms: 20, title: 'C3 resumes exactly where C1 stopped',
          detail: 'C3 reads the committed offset for P1 from the coordinator and fetches from 812. Total pause for P1 ≈ one heartbeat round trip plus C1\'s commit; the other three partitions were never paused.' },
      ],
    },
    {
      id: 'crash', name: 'Consumer crashes',
      summary: 'Consumer 2 is killed mid-batch. Nobody notices until its session times out, and records it processed but did not commit are <b>processed again</b>. At-least-once, by design.',
      steps: [
        { path: ['p2', 'c2'], label: 'records 500–549', badgeAt: 'c2', badge: 'processed to 530', ms: 30, title: 'C2 is working through a batch',
          detail: 'It has charged orders up to offset 530, but its last commit for P2 was 500.' },
        { at: 'c2', badge: 'killed (OOM, node lost)', tone: 'err', ms: 0, title: 'C2 dies without leaving the group',
          detail: 'A clean <code>close()</code> would leave the group immediately. A crash sends nothing.' },
        { at: 'coord', badge: 'no heartbeat for 45 s', tone: 'warn', ms: 45000, title: 'Session timeout',
          detail: 'After <code>session.timeout.ms</code> (default 45 s) the coordinator fences C2. During these 45 s, P2 and P3 have <b>no consumer</b>: their lag grows.' },
        { path: ['coord', 'c1'], label: 'assign P2', badgeAt: 'c1', badge: 'owns P0, P1, P2', ms: 5, title: 'Orphaned partitions are reassigned',
          detail: 'P2 goes to C1 and P3 to C3 (not animated). Healthy members keep their own partitions.' },
        { path: ['p2', 'c1'], label: 'fetch from 500', badgeAt: 'c1', badge: '500–530 again', tone: 'warn', ms: 40, title: 'Replay from the last commit',
          detail: 'C1 starts at committed offset 500, so orders 500–530 are processed a second time. The charge handler must be idempotent, e.g. a unique constraint on <code>event_id</code>.' },
        { at: 'c1', badge: 'lag drains', tone: 'ok', ms: 0, title: 'Recovered',
          detail: 'Shorter session timeouts detect crashes sooner but cause false alarms on GC pauses; static membership (<code>group.instance.id</code>) avoids rebalances on planned restarts.' },
      ],
    },
    {
      id: 'eager', name: 'Classic eager rebalance',
      summary: 'The old default. When C3 joins, <b>every member revokes every partition</b>, the group re-syncs, and all four partitions stop at once. This is the "stop-the-world" rebalance.',
      steps: [
        { path: ['c3', 'coord'], label: 'JoinGroup', ms: 5, title: 'A member joins',
          detail: 'The coordinator starts a new generation and tells existing members to rejoin on their next heartbeat.' },
        { path: ['coord', 'c1'], label: 'rebalance!', badgeAt: 'c1', badge: 'revoke P0, P1', tone: 'err', ms: 5, title: 'C1 drops everything',
          detail: 'With the eager protocol, members revoke <b>all</b> partitions before rejoining, even those that will come straight back.' },
        { path: ['coord', 'c2'], label: 'rebalance!', badgeAt: 'c2', badge: 'revoke P2, P3', tone: 'err', ms: 5, title: 'C2 drops everything',
          detail: 'Now no partition is being consumed. The coordinator waits for every member to send JoinGroup, bounded by the rebalance timeout.' },
        { at: 'coord', badge: 'leader assigns · SyncGroup', ms: 3000, title: 'Barrier: all members must rejoin',
          detail: 'One consumer, the group leader, runs the assignor client-side and returns the plan through SyncGroup. One slow member (a long GC, a batch still processing) holds up the whole group. The ≈3 s is illustrative.' },
        { path: ['coord', 'c3'], label: 'SyncGroup: P1', badgeAt: 'c3', badge: 'owns P1', tone: 'ok', ms: 5, title: 'New assignment delivered',
          detail: 'C1 gets P0 back, C2 gets P2 and P3 back, C3 gets P1. Three of four partitions stopped for nothing.' },
        { at: 'c1', badge: 'fix: cooperative / KIP-848', tone: 'ok', ms: 0, title: 'Why newer protocols exist',
          detail: '<code>CooperativeStickyAssignor</code> revokes only partitions that move; the KIP-848 protocol (GA in Kafka 4.0) removes the group-wide barrier entirely.' },
      ],
    },
  ],
});

}
