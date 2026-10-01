/* Live flows for the testing module (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ============================================== consumer-driven contracts == */
const LtqPact = lane([
  { label: 'CONSUMER CI', nodes: [
    { id: 'ctest', label: 'Pact test', sub: 'checkout-web', icon: 'code', row: 0 },
    { id: 'mock', label: 'Mock provider', sub: 'built from the pact', icon: 'server', row: 1 },
    { id: 'cgate', label: 'Deploy gate', sub: 'checkout-web', icon: 'rocket', row: 2 }] },
  { label: 'BROKER · ENVS', nodes: [
    { id: 'broker', label: 'Pact Broker', sub: 'pacts + matrix', icon: 'db', row: 1 },
    { id: 'prod', label: 'Production', sub: 'recorded versions', icon: 'cloud', row: 2 }] },
  { label: 'PROVIDER CI', nodes: [
    { id: 'verifier', label: 'Verifier', sub: 'replays requests', icon: 'check', row: 0 },
    { id: 'pgate', label: 'Deploy gate', sub: 'orders-api', icon: 'rocket', row: 2 }] },
  { label: 'PROVIDER', nodes: [
    { id: 'api', label: 'orders-api', sub: 'real code', icon: 'api', row: 0 },
    { id: 'tdb', label: 'Test DB', sub: 'provider states', icon: 'db', row: 1 }] },
]);
defineFlow('flow-pact', {
  title: 'Live flow: a consumer-driven contract, from pact test to can-i-deploy',
  hint: 'Follow a pact from the consumer\'s test to the provider\'s CI, then watch a field rename get caught, and a new field wait for the provider.',
  zones: LtqPact.zones, h: LtqPact.h, nodes: LtqPact.nodes,
  edges: [
    ['ctest', 'mock'], ['ctest', 'broker'], ['broker', 'verifier'], ['verifier', 'api'], ['verifier', 'tdb'],
    ['broker', 'cgate'], ['broker', 'pgate'], ['cgate', 'prod'], ['pgate', 'prod'],
  ],
  scenarios: [
    {
      id: 'happy', name: 'Publish, verify, deploy',
      summary: 'The consumer\'s test writes the contract, the provider\'s CI proves it against the real service, and the broker lets the consumer deploy only once that proof exists for the version in production.',
      steps: [
        { path: ['ctest', 'mock', 'ctest'], label: 'GET /orders/42', badgeAt: 'mock', badge: 'matches pact', tone: 'ok', title: 'The real client runs against a mock',
          detail: 'The test declares the interaction (<code>given("order 42 exists and is paid")</code>, the request, the response with type matchers) and runs the <b>real</b> <code>OrdersClient</code> against Pact\'s local mock provider.' },
        { at: 'ctest', badge: 'pact file written', tone: 'ok', title: 'The contract is a by-product of a passing test',
          detail: 'Only because the client really made exactly the declared calls does Pact write <code>checkout-web-orders-api.json</code>. It contains only the fields the consumer reads: <code>id</code>, <code>status</code>, <code>totalCents</code>.' },
        { path: ['ctest', 'broker'], label: 'publish @abc123', badgeAt: 'broker', badge: 'branch main', title: 'Publish, versioned by git SHA',
          detail: '<code>pact-broker publish ./pacts --consumer-app-version abc123 --branch main</code>. A git SHA, not a hand-bumped number, so the broker knows exactly which code made this pact.' },
        { path: ['broker', 'verifier'], label: 'webhook', async: true, title: 'New content triggers the provider',
          detail: 'The <code>contract_requiring_verification_published</code> webhook starts a verification build of orders-api for the provider versions that need it.' },
        { path: ['verifier', 'tdb'], label: 'set up state', badgeAt: 'tdb', badge: 'order 42 = PAID', title: 'Provider state handler',
          detail: 'The provider team\'s handler for "order 42 exists and is paid" inserts that row into the test database, so the replayed request has something to find.' },
        { path: ['verifier', 'api', 'verifier'], label: 'replay GET /orders/42', badgeAt: 'verifier', badge: 'body matches', tone: 'ok', title: 'Replay against the real provider',
          detail: 'The response has an integer <code>id</code>, a <code>status</code> matching <code>NEW|PAID|SHIPPED</code>, an integer <code>totalCents</code>, plus an extra <code>currency</code> field nobody reads, which is allowed.' },
        { path: ['verifier', 'broker'], label: 'result: pass', badgeAt: 'broker', badge: 'matrix row ✓', tone: 'ok', title: 'Publish the verification result',
          detail: 'The broker now knows that pact version X is verified by orders-api version <code>def456</code>, the version currently recorded in production.' },
        { path: ['broker', 'cgate'], label: 'can-i-deploy abc123?', badgeAt: 'cgate', badge: 'yes', tone: 'ok', title: 'The gate reads the matrix',
          detail: '<code>can-i-deploy --pacticipant checkout-web --version abc123 --to-environment production</code>: is there a successful verification against the orders-api version in production? Yes.' },
        { path: ['cgate', 'prod'], label: 'deploy + record', badgeAt: 'prod', badge: 'checkout-web@abc123', tone: 'ok', title: 'Deploy and record it',
          detail: '<code>record-deployment</code> tells the broker what runs in production now. From here on, orders-api must keep this consumer version happy.' },
      ],
    },
    {
      id: 'rename', name: 'Provider renames a field',
      summary: 'The Orders team renames <code>totalCents</code> to <code>total_cents</code>. Their own unit tests are green. The contract catches it in their CI, before merge.',
      steps: [
        { at: 'api', badge: 'PR: total_cents', tone: 'warn', title: 'A harmless-looking refactor',
          detail: 'Orders\' unit tests were updated along with the code, so they pass. Checkout\'s stub of Orders still has the old field, so Checkout\'s tests pass too.' },
        { path: ['broker', 'verifier'], label: 'fetch pacts', badgeAt: 'verifier', badge: 'main + deployed', title: 'The PR build fetches consumer pacts',
          detail: 'Consumer version selectors pick the pacts on consumers\' main branches and every consumer version deployed or released anywhere.' },
        { path: ['verifier', 'tdb'], label: 'set up state', badgeAt: 'tdb', badge: 'order 42 = PAID', title: 'Same provider state',
          detail: 'Nothing about the data changed, only the shape of the response.' },
        { path: ['verifier', 'api', 'verifier'], label: 'replay GET /orders/42', badgeAt: 'verifier', badge: 'missing totalCents', tone: 'err', title: 'Verification fails',
          detail: '<code>$ -> Actual map is missing the following keys: totalCents</code>. The failure names the consumer, the interaction, and the field.' },
        { path: ['verifier', 'broker'], label: 'result: fail', badgeAt: 'broker', badge: 'matrix row ✗', tone: 'err', title: 'The failure is recorded',
          detail: 'The PR build is red. Even if someone merged anyway, the result is in the matrix.' },
        { path: ['broker', 'pgate'], label: 'can-i-deploy?', badgeAt: 'pgate', badge: 'no', tone: 'err', title: 'The provider cannot ship it',
          detail: 'checkout-web@abc123 is in production and reads <code>totalCents</code>, so this provider version is not compatible with production.' },
        { at: 'api', badge: 'expand: send both', tone: 'ok', title: 'The safe way: expand and contract',
          detail: 'Return both <code>totalCents</code> and <code>total_cents</code>, deploy; consumers switch and deploy; once no deployed consumer reads the old field, remove it. Three deploys, in an order the broker enforces.' },
      ],
    },
    {
      id: 'newfield', name: 'Consumer needs a new field',
      summary: 'Checkout starts reading a <code>currency</code> field that Orders does not return yet. <b>Pending pacts</b> keep the provider\'s build green, and <b>can-i-deploy</b> makes the consumer wait.',
      steps: [
        { path: ['ctest', 'broker'], label: 'publish @b77 (feat)', badgeAt: 'broker', badge: 'new content', title: 'A pact with a new expectation',
          detail: 'The consumer\'s feature branch now expects <code>currency</code> matching <code>[A-Z]{3}</code>.' },
        { path: ['broker', 'verifier'], label: 'WIP pact', async: true, title: 'The provider verifies it automatically',
          detail: 'Work-in-progress pacts from other branches are included without changing the provider\'s configuration.' },
        { path: ['verifier', 'api', 'verifier'], label: 'replay', badgeAt: 'verifier', badge: 'fails, pending', tone: 'warn', title: 'Failure is reported but pending',
          detail: 'The provider\'s main branch has never verified this pact content, so it is <b>pending</b>: the consumer sees the failure, but the provider\'s build is not broken by an expectation it never agreed to.' },
        { path: ['broker', 'cgate'], label: 'can-i-deploy b77?', badgeAt: 'cgate', badge: 'no', tone: 'err', title: 'The consumer must wait',
          detail: 'No successful verification exists against the orders-api version in production, and a missing result is a no, not a yes.' },
        { path: ['verifier', 'broker'], label: 'provider adds currency', badgeAt: 'broker', badge: 'verified ✓', tone: 'ok', title: 'The provider implements it',
          detail: 'Orders adds the field, its build verifies the pact, and it publishes a passing result for its new version.' },
        { path: ['pgate', 'prod'], label: 'deploy + record', badgeAt: 'prod', badge: 'orders-api@e19', tone: 'ok', title: 'The provider ships first',
          detail: 'The provider\'s can-i-deploy is yes (it still satisfies checkout-web@abc123 in production), and <code>record-deployment</code> updates the environment.' },
        { path: ['broker', 'cgate', 'prod'], label: 'can-i-deploy → yes', badgeAt: 'prod', badge: 'checkout-web@b77', tone: 'ok', title: 'Now the consumer can ship',
          detail: 'The deploy order (provider first, then consumer) was never written down anywhere; the matrix enforced it.' },
      ],
    },
  ],
});

/* =================================================== chaos experiment == */
const LtqChaos = lane([
  { label: 'CLIENTS', nodes: [{ id: 'users', label: 'Users', sub: 'real traffic', kind: 'client', row: 1 }] },
  { label: 'SERVICE', nodes: [{ id: 'svc', label: 'Product API', sub: 'timeouts + fallback', icon: 'service', row: 1 }] },
  { label: 'DEPENDENCIES', nodes: [
    { id: 'cache', label: 'Redis', sub: 'cache-aside', kind: 'cache', row: 0 },
    { id: 'db', label: 'Database', sub: 'source of truth', kind: 'db', row: 2 }] },
  { label: 'CHAOS · OBSERVE', nodes: [
    { id: 'chaos', label: 'Chaos controller', sub: 'NetworkChaos', icon: 'flag', row: 0 },
    { id: 'slo', label: 'SLO monitor', sub: 'errors · p99', icon: 'monitor', row: 2 }] },
]);
defineFlow('flow-chaos', {
  title: 'Live flow: a chaos experiment with a hypothesis, a blast radius and an abort switch',
  hint: 'Inject cache latency and watch the fallback hold the steady state, then break the cache harder and watch the abort condition stop the experiment.',
  zones: LtqChaos.zones, h: LtqChaos.h, nodes: LtqChaos.nodes,
  edges: [['users', 'svc'], ['svc', 'cache'], ['svc', 'db'], ['chaos', 'cache'], ['slo', 'chaos']],
  scenarios: [
    {
      id: 'holds', name: 'Hypothesis holds',
      summary: 'Hypothesis: <b>if Redis responds 300 ms slower, the API times out after 50 ms and reads the database, so the error rate stays under 1% and p99 under 400 ms.</b> Numbers are illustrative.',
      steps: [
        { at: 'slo', badge: 'errors 0.1% · p99 180 ms', tone: 'ok', title: 'Measure the steady state first',
          detail: 'A business-level signal (successful product-page loads) and its normal range. Without a baseline you cannot tell whether the experiment changed anything.' },
        { path: ['chaos', 'cache'], label: '+300 ms, 1 of 3 pods', badgeAt: 'cache', badge: 'latency injected', tone: 'warn', title: 'Inject the fault, with a small blast radius',
          detail: 'A Chaos Mesh <code>NetworkChaos</code> delay on one Redis-client pod\'s traffic, for 10 minutes. The abort condition is armed: error rate over 1% for 1 minute.' },
        { path: ['users', 'svc', 'cache'], label: 'GET /products/9', badgeAt: 'svc', badge: 'timeout at 50 ms', tone: 'warn', title: 'The cache is slow',
          detail: 'The client timeout on the cache call is 50 ms, far below the injected 300 ms, so the request does not hang.' },
        { path: ['svc', 'db', 'svc'], label: 'fallback read', badgeAt: 'db', badge: '+20 ms', title: 'Fall back to the source of truth',
          detail: 'The service reads the database instead. A circuit breaker stops trying the slow cache for a while, so most requests skip the 50 ms wait entirely.' },
        { path: ['svc', 'users'], label: '200 OK', tone: 'ok', title: 'Users are served, a little slower',
          detail: 'Latency rises; errors do not.' },
        { at: 'slo', badge: 'errors 0.1% · p99 240 ms', tone: 'ok', title: 'The steady state held',
          detail: 'The hypothesis survived. Confidence in the fallback is now based on evidence, not on a code review. Next step: widen the blast radius, or automate the experiment in CI.' },
        { path: ['chaos', 'cache'], label: 'duration over: remove', badgeAt: 'cache', badge: 'restored', tone: 'ok', title: 'The fault is removed',
          detail: 'Experiments always end by removing the fault, whether they pass, fail or are aborted.' },
      ],
    },
    {
      id: 'abort', name: 'Weakness found: abort',
      summary: 'Same experiment, but Redis is made <b>unreachable</b>, and it turns out one code path has no timeout at all. The abort condition stops the experiment before users notice much.',
      steps: [
        { at: 'slo', badge: 'errors 0.1% · p99 180 ms', tone: 'ok', title: 'Steady state',
          detail: 'Same baseline and hypothesis: losing the cache should cost latency, not errors.' },
        { path: ['chaos', 'cache'], label: 'drop packets, 1 of 3 pods', badgeAt: 'cache', badge: 'unreachable', tone: 'err', title: 'Inject a harder fault',
          detail: 'Packets to Redis from one pod are dropped. Connection attempts now hang until the TCP connect timeout.' },
        { path: ['users', 'svc', 'cache'], label: 'GET /products/9', badgeAt: 'svc', badge: 'blocked, no timeout', tone: 'err', title: 'A missing timeout',
          detail: 'The product page uses a client with a 50 ms timeout, but the price-lookup path uses an older client with <b>no timeout</b>. Worker threads pile up waiting.' },
        { path: ['svc', 'users'], label: '503 / timeouts', tone: 'err', title: 'Errors reach users on that pod',
          detail: 'With workers exhausted, the pod rejects new requests. One pod in three, so roughly a third of traffic is affected.' },
        { at: 'slo', badge: 'errors 4% > 1%', tone: 'err', title: 'The abort condition trips',
          detail: 'Error rate above the 1% threshold for a minute. This is a stop condition defined before the experiment started, not a judgement call made under pressure.' },
        { path: ['slo', 'chaos'], label: 'ABORT', badgeAt: 'chaos', badge: 'rolling back', tone: 'err', title: 'Stop the experiment automatically',
          detail: 'The controller is told to stop (AWS FIS stop conditions work the same way, wired to CloudWatch alarms).' },
        { path: ['chaos', 'cache'], label: 'remove fault', badgeAt: 'cache', badge: 'restored', tone: 'ok', title: 'The fault is removed',
          detail: 'Redis is reachable again; the stuck connections fail and free the workers.' },
        { at: 'slo', badge: 'errors 0.1%', tone: 'ok', title: 'Recovered, and a real finding',
          detail: 'The experiment "failed", which is the useful outcome: add a timeout and a circuit breaker to the price-lookup client, then rerun the same experiment to prove the fix.' },
      ],
    },
  ],
});

}
