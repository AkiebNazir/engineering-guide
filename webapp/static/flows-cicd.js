/* Live flows for the cicd module (see sd-flow.js for the engine and data format). */
'use strict';
{

/* ================================================ canary with analysis == */
const LciCanary = lane([
  { label: 'USERS', nodes: [{ id: 'users', label: 'Users', sub: 'production traffic', kind: 'client', row: 1 }] },
  { label: 'ROUTING · CONTROL', nodes: [
    { id: 'ctrl', label: 'Argo Rollouts', sub: 'rollout controller', icon: 'k8s', row: 0 },
    { id: 'router', label: 'Mesh router', sub: 'weighted routes', icon: 'mesh', row: 1 }] },
  { label: 'VERSIONS', nodes: [
    { id: 'stable', label: 'Stable v1', sub: '9 pods', icon: 'app', row: 1 },
    { id: 'canary', label: 'Canary v2', sub: 'new ReplicaSet', icon: 'app', row: 2 }] },
  { label: 'ANALYSIS', nodes: [
    { id: 'analysis', label: 'AnalysisRun', sub: 'every 1 min', icon: 'gauge', row: 0 },
    { id: 'prom', label: 'Prometheus', sub: 'success rate', icon: 'prometheus', row: 1 }] },
]);
defineFlow('flow-canary-analysis', {
  title: 'Live flow: a canary promoted, aborted, or paused by automated analysis',
  hint: 'Follow one Argo Rollouts canary: traffic weights change step by step while an AnalysisRun queries Prometheus and decides.',
  zones: LciCanary.zones, h: LciCanary.h, nodes: LciCanary.nodes,
  edges: [
    ['users', 'router'], ['router', 'stable'], ['router', 'canary'], ['ctrl', 'router'],
    ['stable', 'prom', { async: true }], ['canary', 'prom', { async: true }],
    ['prom', 'analysis'], ['analysis', 'ctrl'],
  ],
  scenarios: [
    {
      id: 'promote', name: 'Healthy: promoted',
      summary: 'A new image digest lands in Git. The controller creates a canary, moves traffic in steps (5% → 25% → 50% → 100%), and the analysis passes at every step.',
      steps: [
        { at: 'ctrl', badge: 'new pod template', title: 'A new version appears',
          detail: 'Argo CD synced a Rollout whose image digest changed. Instead of a rolling update, Argo Rollouts starts the <b>canary strategy</b> defined in the Rollout.' },
        { path: ['ctrl', 'router'], label: 'setWeight: 5', badgeAt: 'canary', badge: 'v2 pods ready', title: 'Step 1: 5% of traffic',
          detail: 'The controller scales up the canary ReplicaSet and, once it is ready, edits the Istio VirtualService weights to 95 / 5. Pod counts no longer decide the split.' },
        { path: ['users', 'router', 'canary'], label: '5% of requests', title: 'Real users reach v2',
          detail: 'One request in twenty goes to v2. The blast radius of a bad version is now 5% of users for a few minutes.' },
        { path: ['canary', 'prom'], label: 'request metrics', async: true, title: 'Both versions report metrics',
          detail: 'The mesh sidecars export request counts and response codes per destination, so v2 can be measured separately from v1.' },
        { path: ['analysis', 'prom', 'analysis'], label: 'success rate?', badgeAt: 'analysis', badge: '99.8% ≥ 99% ✓', tone: 'ok', ms: 60000, title: 'Measure every minute',
          detail: 'The AnalysisRun runs the PromQL query from the AnalysisTemplate. <code>successCondition: result[0] >= 0.99</code> holds, so each measurement is Successful.' },
        { path: ['ctrl', 'router'], label: 'setWeight: 25 → 50', ms: 1200000, title: 'Pause, then widen',
          detail: 'After each <code>pause: {duration: 10m}</code> the controller raises the weight. The analysis keeps running in the background the whole time.' },
        { at: 'stable', badge: 'v2 is the new stable', tone: 'ok', title: 'Promotion',
          detail: 'After the last step the canary becomes stable: 100% of traffic, the old ReplicaSet scaled down. Nobody pressed a button.' },
      ],
    },
    {
      id: 'abort', name: 'Regression: aborted',
      summary: 'The new version returns errors for some requests. The analysis fails three measurements in a row and the controller aborts the rollout on its own.',
      steps: [
        { path: ['ctrl', 'router'], label: 'setWeight: 5', badgeAt: 'canary', badge: 'v2 pods ready', title: 'Canary starts at 5%',
          detail: 'Readiness probes pass: the pods start and answer <code>/readyz</code>. A rolling update would carry on from here.' },
        { path: ['users', 'router', 'canary'], label: '5% of requests', badgeAt: 'canary', badge: '4% are 5xx', tone: 'warn', title: 'Some requests fail',
          detail: 'A bug only shows with real data: 4% of v2 responses are errors. Stable v1 is still at 0.1%.' },
        { path: ['analysis', 'prom', 'analysis'], label: 'success rate?', badgeAt: 'analysis', badge: '96% · failure 1', tone: 'warn', ms: 60000, title: 'First failed measurement',
          detail: '<code>failureCondition: result[0] < 0.97</code> matches. With <code>failureLimit: 2</code>, two failures are tolerated to absorb noise.' },
        { path: ['analysis', 'prom', 'analysis'], label: 'again, twice', badgeAt: 'analysis', badge: 'failure 3 > limit', tone: 'err', ms: 120000, title: 'Failure limit exceeded',
          detail: 'The third failed measurement marks the AnalysisRun <b>Failed</b>.' },
        { path: ['analysis', 'ctrl'], label: 'Failed', tone: 'err', title: 'The controller aborts',
          detail: 'A failed analysis triggers an abort of the Rollout. No human had to be watching a dashboard.' },
        { path: ['ctrl', 'router'], label: 'weight 0 → stable', badgeAt: 'canary', badge: 'scaled down', tone: 'ok', title: 'Traffic returns to v1 in seconds',
          detail: 'The weights go back to 100 / 0 and the canary pods are removed. Total exposure: 5% of users for about three minutes.' },
        { at: 'ctrl', badge: 'Rollout Degraded', tone: 'warn', title: 'The fix is a Git change',
          detail: 'Git still says v2, so the Rollout stays Degraded until someone reverts the commit or ships a fix. That keeps Git and the cluster honest.' },
      ],
    },
    {
      id: 'inconclusive', name: 'Too little data: paused',
      summary: 'A quiet service sends the canary about one request per second. The metric lands between the pass and fail thresholds, and the controller stops to ask a human.',
      steps: [
        { path: ['ctrl', 'router'], label: 'setWeight: 5', title: 'Canary starts at 5%',
          detail: 'The service handles about 20 requests per second, so the canary gets about 1 per second.' },
        { path: ['users', 'router', 'canary'], label: '≈1 req/s', badgeAt: 'canary', badge: '1 error in 60', title: 'One unlucky error',
          detail: 'In a one-minute window the canary served about 60 requests. A single error makes its success rate 98.3%.' },
        { path: ['analysis', 'prom', 'analysis'], label: 'success rate?', badgeAt: 'analysis', badge: '98.3%: inconclusive', tone: 'warn', ms: 60000, title: 'Neither pass nor fail',
          detail: 'The value is below <code>successCondition</code> (0.99) but above <code>failureCondition</code> (0.97), so the measurement is <b>Inconclusive</b>.' },
        { path: ['analysis', 'ctrl'], label: 'Inconclusive', tone: 'warn', title: 'The rollout pauses',
          detail: 'An inconclusive analysis pauses the Rollout at its current weight. It is not promoted and not aborted.' },
        { at: 'ctrl', badge: 'waiting for a human', tone: 'warn', title: 'Promote or abort by hand',
          detail: 'Someone runs <code>kubectl argo rollouts promote</code> or <code>abort</code>. For low-traffic services, use longer steps, a larger first weight or synthetic traffic, so the analysis has enough data to decide.' },
      ],
    },
  ],
});

/* ================================================ GitOps reconcile loop == */
const LciGitops = lane([
  { label: 'PEOPLE · CI', nodes: [
    { id: 'dev', label: 'Developer', sub: 'PR to config repo', kind: 'client', row: 0 },
    { id: 'ci', label: 'CI pipeline', sub: 'bumps image digest', icon: 'workflow', row: 1 },
    { id: 'ops', label: 'Operator', sub: 'kubectl by hand', icon: 'admin', row: 2 }] },
  { label: 'GIT', nodes: [{ id: 'git', label: 'Config repo', sub: 'desired state', icon: 'git', row: 1 }] },
  { label: 'ARGO CD', nodes: [
    { id: 'repo', label: 'repo-server', sub: 'renders manifests', icon: 'layers', row: 0 },
    { id: 'appctl', label: 'App controller', sub: 'diff, sync, health', icon: 'sync', row: 1 }] },
  { label: 'CLUSTER', nodes: [
    { id: 'kapi', label: 'Kubernetes API', sub: 'live state', icon: 'k8s', row: 1 },
    { id: 'pods', label: 'Pods', sub: 'checkout-api', icon: 'container', row: 2 }] },
]);
defineFlow('flow-gitops-reconcile', {
  title: 'Live flow: the GitOps reconcile loop, from commit to healthy',
  hint: 'Watch Argo CD notice a commit, render it, diff it against the cluster and sync; then watch it undo a manual change, and a bad release get reverted through Git.',
  zones: LciGitops.zones, h: LciGitops.h, nodes: LciGitops.nodes,
  edges: [
    ['dev', 'git'], ['ci', 'git'], ['git', 'appctl'], ['appctl', 'repo'], ['repo', 'git'],
    ['appctl', 'kapi'], ['kapi', 'pods'], ['ops', 'kapi'],
  ],
  scenarios: [
    {
      id: 'deploy', name: 'New image: commit to healthy',
      summary: 'CI never touches the cluster. It commits a new digest to Git, and Argo CD does the rest.',
      steps: [
        { path: ['ci', 'git'], label: 'commit: image@sha256:9f2c', badgeAt: 'git', badge: 'commit a1b2', title: 'CI writes to Git, not to the cluster',
          detail: 'The last CI step updates the production overlay (<code>kustomize edit set image …@sha256:9f2c…</code>) and merges it. CI holds a Git token only, never cluster credentials.' },
        { path: ['git', 'appctl'], label: 'webhook: refresh', ms: 1000, title: 'Argo CD finds out',
          detail: 'A Git webhook to argocd-server triggers a refresh at once. Without one, the next poll picks it up, about every 3 minutes by default.' },
        { path: ['appctl', 'repo', 'git', 'repo'], label: 'render commit a1b2', ms: 2000, title: 'Render the desired state',
          detail: 'The repo-server fetches the commit and runs Kustomize (or Helm) to produce plain manifests. The result is cached by commit SHA.' },
        { path: ['repo', 'appctl'], label: 'manifests', badgeAt: 'appctl', badge: 'OutOfSync: image differs', tone: 'warn', title: 'Diff against live state',
          detail: 'The controller compares the rendered Deployment with its watch cache of the live object. The image differs, so the app is <b>OutOfSync</b>.' },
        { path: ['appctl', 'kapi'], label: 'sync: apply Deployment', ms: 500, title: 'Automated sync applies it',
          detail: 'With <code>syncPolicy.automated</code> on, the controller applies the change: PreSync hooks, then resources wave by wave, then PostSync hooks.' },
        { path: ['kapi', 'pods'], label: 'rolling update', badgeAt: 'pods', badge: 'Progressing', ms: 60000, title: 'Kubernetes rolls the pods',
          detail: 'The Deployment controller in the cluster replaces pods using readiness probes and <code>maxSurge</code>. Argo CD reports <b>Progressing</b> meanwhile.' },
        { at: 'appctl', badge: 'Synced · Healthy', tone: 'ok', title: 'Converged',
          detail: 'Live matches Git and every resource is healthy. The Application history records which commit was synced and when.' },
      ],
    },
    {
      id: 'drift', name: 'Drift: manual edit reverted',
      summary: 'Someone changes production by hand. With self-heal on, Argo CD puts it back. The durable way to make that change is a pull request.',
      steps: [
        { path: ['ops', 'kapi'], label: 'kubectl scale --replicas=10', badgeAt: 'pods', badge: '10 replicas', tone: 'warn', title: 'A change outside Git',
          detail: 'During a traffic spike an operator scales the Deployment by hand. Git still says <code>replicas: 6</code>.' },
        { path: ['kapi', 'appctl'], label: 'watch event', badgeAt: 'appctl', badge: 'OutOfSync: replicas', tone: 'warn', ms: 100, title: 'Detected immediately',
          detail: 'The controller watches live objects, so it sees the change at once, with no poll needed. Live state no longer matches Git.' },
        { path: ['appctl', 'kapi', 'pods'], label: 'selfHeal: re-apply Git', badgeAt: 'pods', badge: 'back to 6', tone: 'ok', ms: 5000, title: 'Self-heal reverts it',
          detail: 'With <code>selfHeal: true</code> the controller re-applies the Git version within seconds. <b>Without self-heal</b> it only reports OutOfSync and waits.' },
        { path: ['dev', 'git'], label: 'PR: replicas 6 → 10', badgeAt: 'git', badge: 'reviewed + merged', tone: 'ok', title: 'The change that lasts goes through Git',
          detail: 'If more replicas are really needed, the fix is a PR, or better an HPA with <code>/spec/replicas</code> in <code>ignoreDifferences</code> so Argo CD and the autoscaler do not fight.' },
      ],
    },
    {
      id: 'revert', name: 'Bad release: revert in Git',
      summary: 'The sync succeeds but the new pods crash. The app is Synced and Degraded, and the rollback is a git revert.',
      steps: [
        { path: ['dev', 'git'], label: 'merge: new env var', badgeAt: 'git', badge: 'commit c3d4', title: 'A config change merges',
          detail: 'A PR renames an environment variable the app reads at startup. Reviewers miss that the code still expects the old name.' },
        { path: ['git', 'appctl', 'kapi'], label: 'refresh, diff, sync', ms: 3000, title: 'Argo CD syncs it',
          detail: 'Same loop as a normal deploy: render, diff, apply.' },
        { path: ['kapi', 'pods'], label: 'new pods start', badgeAt: 'pods', badge: 'CrashLoopBackOff', tone: 'err', ms: 30000, title: 'The new pods crash',
          detail: 'The new ReplicaSet never becomes ready. <code>maxUnavailable: 0</code> keeps the old pods serving, so users are not affected yet.' },
        { at: 'appctl', badge: 'Synced · Degraded', tone: 'err', title: 'Synced is not the same as healthy',
          detail: 'The cluster matches Git, and what Git describes is broken. <code>kubectl rollout undo</code> would be reverted by self-heal, so the lever is Git.' },
        { path: ['dev', 'git'], label: 'git revert c3d4', badgeAt: 'git', badge: 'commit e5f6', title: 'Revert the commit',
          detail: 'The history now shows the bad change and its reversal, and every cluster that tracks this path will converge on it.' },
        { path: ['git', 'appctl', 'kapi', 'pods'], label: 'sync previous config', badgeAt: 'pods', badge: 'Healthy', tone: 'ok', ms: 30000, title: 'Converged on the good state',
          detail: 'The crashing ReplicaSet is replaced and the app returns to <b>Synced · Healthy</b>. The follow-up is a test that would have caught the rename.' },
      ],
    },
  ],
});

}
