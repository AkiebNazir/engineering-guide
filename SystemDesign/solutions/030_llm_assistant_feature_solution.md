# 030 — LLM-Powered Assistant Feature: Full System Design Solution

## Goal and contract

A streaming assistant that is fast to first token, grounded in the user's own permitted mail, safe against malicious email content, and **predictable in cost**. The model is treated as an expensive, sometimes-slow dependency: every request passes quota, safety, and routing decisions before a GPU is involved, and the product still works (with degraded features) when the model tier is saturated.

## Estimates

- **Requests**: 50M users × 6 = 300M requests/day ≈ 3,500/s average; with a daytime peak factor of ~3 → **~10K requests/s**.
- **Tokens**: prefill 3,000 tokens and decode 250 tokens per request → at peak, ~30M prompt tokens/s and ~2.5M output tokens/s.
- **GPU capacity (order of magnitude)**: suppose one GPU serving a mid-size model with continuous batching produces ~2,000–4,000 output tokens/s across its batch and prefills ~20K–50K tokens/s. Decode alone needs 2.5M ÷ 2,000–4,000 = ~600–1,250 GPUs at peak; prefill needs 30M ÷ 20K–50K = ~600–1,500. Prompts carry 12× more tokens, but a GPU processes them roughly 10× faster than it decodes, so the two cost about the same: **~2,000 GPUs at peak before any optimisation**. Prompt tokens are still the lever we control (retrieval, prefix caching), because output length is bounded by the task.
- **Concurrent streams and memory**: by Little's law, 10K requests/s × ~5 s = 50K concurrent decodes. To finish 250 tokens within 5 s after a ~0.6 s first token, each stream needs ≥ 250 ÷ 4.4 ≈ 57 tokens/s, which caps a GPU's batch near 50 streams (50 × 57 ≈ 2,850 tokens/s, inside the 2,000–4,000 range): 50K ÷ 50 = **1,000 GPUs**, matching the throughput view. KV cache is the memory limit: for an 8B-class model with grouped-query attention (assumption: 32 layers × 8 KV heads × 128 dim × 2 × 2 bytes) it is ~131 KB per token, so 3,250 tokens ≈ 0.43 GB per sequence and 50 sequences ≈ 21 GB beside 16 GB of weights on an 80 GB GPU. A 70B-class model needs several GPUs per replica.
- **Time to first token, p95 < 1 s** (assumed slices, ms): gateway and quota 10, retrieval with ACL filter 100, input guard 50, prompt assembly 20, queue ≤ 100, prefill of 3,000 tokens ~200 (100 alone at ~30K tokens/s, plus contention), first decode step 30, network 50 = **~560**, leaving ~440 for tails.
- **After optimisation**: prefix caching removes ~1,000 of 3,000 prompt tokens, so prefill GPUs fall from 1,000 to ~670; routing 70% of traffic to a model 5× cheaper scales cost by 0.3 + 0.7 × 0.2 = 0.44. So 1,670 × 0.44 ≈ **730 GPU-equivalents**, about 950 with 30% headroom.
- **So**: reducing prompt tokens (retrieval instead of whole threads, prefix caching) and routing easy requests to smaller models are the biggest cost levers — bigger than micro-optimising the decode path.

## API

```text
POST /v1/assist           {task: summarize|draft|ask, thread_id?, question?, tone?}
  → text/event-stream:  event: token   data: {"t":"The"}
                         event: citation data: {"message_id": "...", "snippet": "..."}
                         event: done    data: {"usage": {"prompt": 2830, "output": 212}, "model": "small"}
                         event: error   data: {"code": "quota_exceeded", "retry_after": 3600}
```

Server-sent events suit this one-directional stream; the client cancels by closing the connection, which must also cancel generation on the GPU to free capacity.

## Architecture

```arch
%% caption: Cheap checks and context assembly happen before the GPU; the model tier only sees trimmed, permission-checked context.
node ui "Mail client" at 1,0 icon=email shape=pill
node guard_out "Output guard" at 0,1 icon=shield sub="policy + PII checks"
node gw "AI gateway" at 1,1 icon=gateway sub="auth, quotas, rate limits"
node orch "Orchestrator" at 1,2 icon=workflow sub="template, cache, citations"
node router "Model router" at 1,3 icon=sitemap
group gpu "Model tier: GPUs" color=teal icon=llm
node small "Small model pool" at 0,3 in gpu icon=model
node large "Large model pool" at 0,4 in gpu icon=llm
group pre "Checks + context" color=blue icon=shield
node guard_in "Input guard" at 2,0 in pre icon=shield sub="injection + abuse"
node policy "Org policy + consent" at 2,1 in pre icon=auth
node ret "Mailbox retrieval" at 2,2 in pre icon=search sub="per-user, ACL-filtered"
group st "Stores" color=slate icon=db
node cache "Response + prefix cache" at 2,3 in st icon=cache
node logs "Usage, eval, cost" at 2,4 in st icon=logs sub="eval samples"
ui -> gw : "<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>"
gw -> orch
orch:R -> guard_in:L
orch:R -> policy:L
orch -> ret
orch:R -> cache:L
orch:R -> logs:L
orch -> router
router -> small
router:B -> large:R
small -> guard_out
large:L -> guard_out:L
guard_out -> gw
```

1. **AI gateway**: authenticates, checks the org/admin enablement flag, enforces quotas and rate limits, opens the stream.
2. **Orchestrator**: builds the prompt from a versioned template, the task, and context; decides cache hits; calls the router; post-processes citations.
3. **Mailbox retrieval** for "ask" tasks: a per-user search index over the mailbox (keyword + embedding hybrid search), filtered by the user's access at query time, returning a few relevant messages instead of the whole mailbox.
4. **Model serving pools** run behind the router with continuous batching.
5. **Guards** before and after the model.

## Serving capacity and GPUs

- **Continuous batching with paged KV cache** (vLLM/TGI-style) keeps GPUs saturated: new requests join the running batch as others finish, which gives several times the throughput of static batching at similar latency.
- **Separate prefill and decode capacity** when prompts are long: prefill is compute-heavy, decode is memory-bandwidth-heavy; disaggregating them lets each pool be sized and batched for its workload and protects time-to-first-token from long decodes.
- **Prefix caching**: the system prompt, safety preamble, and tool instructions (often 1,000+ tokens) are identical for every request of a task type; caching their KV state removes that prefill cost. Order prompts as `static instructions → thread context → question` so the shared prefix is as long as possible.
- **Model routing**: summaries of short threads and simple drafts go to a small model; long threads, complex questions, and retries after low-confidence answers go to the large model. Even routing 70% of traffic to a model 5× cheaper roughly halves cost.
- **Context trimming**: quoted replies and signatures are stripped from threads; long threads are summarised hierarchically (summaries of older messages cached per thread and reused).
- **Peaks**: queue with a short deadline in front of the pools; when queue time exceeds the time-to-first-token budget, shed low-priority work first (background pre-computation, free-tier requests), fall back to the small model, or return "try again shortly" rather than letting every request time out. Pre-compute summaries for long unread threads during off-peak hours.
- **Caching responses**: "summarise this thread" for an unchanged thread is cached per user and thread version; semantic caching of free-form answers is *not* used across users (privacy) and only with strict thresholds within a user.

## Quotas, rate limits and cost

- **Token-based quotas** per user and per organisation per day/month by plan, enforced at the gateway with a counter store (reserve estimated tokens at start, reconcile with actual usage at the end).
- **Rate limits** per user per minute (token bucket) to stop runaway scripts and protect shared capacity; per-org concurrency limits for large tenants.
- **Caps**: maximum prompt tokens per task (truncate or summarise context), `max_tokens` on output.
- **Cost as a metric**: cost per request and per feature, broken down by model, prefill vs decode, and cache hit rates, reviewed like latency.

## Safety, prompt injection and privacy

- **Prompt injection**: email content is untrusted input. Mark it clearly as data in the prompt, instruct the model never to follow instructions inside it, run an injection classifier on retrieved content, and — most importantly — give the assistant **no dangerous capabilities by default**: it drafts text but never sends mail or changes settings without explicit user confirmation.
- **Output guard**: policy classifiers (harassment, unsafe content), PII and data-leak checks (does the answer contain content from messages not in the retrieved set?), and citation verification.
- **Privacy**: retrieval enforces the user's permissions at query time; prompts and outputs are not used for training without consent; logs are redacted, access-controlled, and retained briefly; enterprise data stays in region per contract.

## Evaluation and quality

- An offline evaluation set per task (thread summaries with reference points, Q&A with known answers) scored by automated graders and periodic human review, run on every prompt-template or model change.
- Online: thumbs up/down, edit distance between drafted and sent replies, citation click-through, and task abandonment.
- Rollouts via shadow traffic and A/B experiments, with automatic rollback on quality or safety regressions.

## Fallbacks

| Situation | Behaviour |
|---|---|
| Large model pool saturated | Route to the small model with a lower-quality badge, or queue with a short deadline. |
| All model pools down | Hide the assistant entry points; mail works normally. Never block core email. |
| Retrieval index stale or down | Answer only from the open thread; tell the user search-based answers are unavailable. |
| Guard service down | Fail closed for free-form answers (no unguarded output); allow cached, previously checked summaries. |
| Quota exhausted | Clear error with reset time; admins see usage dashboards. |

## Observability and interview close

Measure: time to first token and tokens/s by model and task, queue time, GPU utilisation and batch size, prefix-cache hit rate, prompt and output tokens per request, cost per request, quota rejections, guard block rates, injection detections, fallback rates, and quality/eval scores per model and template version.

Trade-off to state: "I route most traffic to a small model and trim context aggressively, which cuts cost several-fold and keeps time to first token low, at the risk of weaker answers on hard threads. I contain that risk by escalating to the large model on long or complex requests and on low confidence. If quality gaps showed up in the evals, I'd raise the escalation rate before making the large model the default, because the default drives almost all of the cost."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Enterprise data must stay in region, so each region needs its own retrieval index and GPU pool, and the fixed GPU budget splits into smaller pools with less statistical multiplexing. Overflow to another region is allowed only for tenants without residency constraints (an extra ~100 ms fits the 560 ms budget). Regional pools are sized for their own peaks, which differ by time zone. If a region's pool fails, fall back to its small-model standby or hide the feature there.
2. **"What changes at 10× and 100×?"** At 10× (100K requests/s) the optimised fleet is about 7,300 GPU-equivalents, which is a procurement and power problem more than an architecture one. Prefix and response caches, distilled small models for ~90% of traffic, quantisation and speculative decoding each buy a hedged 1.5–2×, so I would push routing first. At 100× the per-request cost cannot hold: change the product (shorter contexts, on-device models for simple tasks, tighter quotas).
3. **"What if permissions must be exact, with no stale ACL?"** An index-side ACL copy can lag a revocation, so re-check the retrieved candidates (about 20 message IDs) against the mailbox source of truth before they enter the prompt, which costs one batch call of roughly 10–20 ms. Re-verify each cited message before streaming its citation. A strict output-safety variant buffers the first 20–40 tokens (~0.5 s) for the guard, which eats into the 1 s time-to-first-token budget.
4. **"What does it cost?"** At an assumed $2 per GPU-hour, 733 GPUs × 24 h = $35K a day, or $0.117 per 1,000 requests, against $0.32 unoptimised (2,000 GPUs). Six requests a day is about $0.02 per user per month. GPUs are provisioned for peak (3× average), so scheduling off-peak precompute of summaries fills the troughs. The levers in order are routing, prefix caching, context trimming, then quantisation.
5. **"How do you handle abuse?"** Email is untrusted input, so mark it as data, run an injection classifier, and give the assistant no send or settings tools without user confirmation. Strip remote images and links from rendered output, since a model can be induced to leak data through a URL. Rate-limit per user and cap prompt and output tokens, and detect templated mass drafts that look like phishing. Multiple accounts to dodge quotas are handled per organisation and per device.
6. **"Why route to a small model? Just use the best one."** All-large is about 2.3× the cost of the routed design (1,670 versus 733 GPU-equivalents), and the default drives nearly all of the spend. If the evals show the small model within a few points on summaries and drafts, it is the default, with escalation on long threads or low confidence. If the interviewer wants quality first, start with large as default in a beta, measure, then route. The router itself must be cheap (rules first, a tiny classifier later, under 10 ms).
7. **"How do you evaluate a prompt change before shipping?"** Treat it like code. Run it against a golden set per task (say 1,000 cases, with slices for long threads and languages) and an injection red-team set, using graders calibrated against human labels. Check the token, latency and cost deltas, because a longer prompt costs GPUs. Then shadow it on live traffic without showing users, A/B at 1%, 5%, 50% with guardrails on thumbs, edit distance and safety-block rate, and roll back automatically. Templates are versioned, and the model version is pinned.
8. **"What if the model provider or GPU pool has an outage?"** The assistant must never take mail down: circuit-break on queue time, hide the entry points, serve cached summaries, and fail over to a warm small-model pool or a second provider that passes the same privacy review. Replica cold starts take tens of seconds to minutes (weights load plus warm-up), so autoscale on queue depth with spare warm capacity, not on utilisation, and rehearse this in game days.

## Common mistakes

1. **Sizing only output tokens.** Prefill is about half the GPU bill, and KV-cache memory caps the batch. Size both.
2. **Serving one request at a time, or with static batches.** GPUs idle while sequences finish. Use continuous batching with paged KV cache.
3. **Not cancelling generation when the client disconnects.** The GPU keeps decoding for nobody. Propagate the <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> close to the scheduler.
4. **Stuffing whole threads or mailboxes into the prompt.** Cost and injection surface both grow. Retrieve a few messages and trim quotes and signatures.
5. **Enforcing permissions only in the index, or after generation.** A revoked or unauthorised message can already be in the prompt. Check the source of truth before assembly.
6. **A semantic response cache shared across users.** A near-match can return another user's private answer. Cache per user and thread version only.
7. **An unbounded queue in front of the pools.** Latency grows until every request times out. Bound the queue by time-to-first-token and shed low-priority work.

## Going from L5 to L6

- **Migration and rollout.** Roll by capability and cohort: summarise first (lowest risk), then drafting, then free-form ask, with per-org enable flags for staged enterprise rollout. Keep two model versions live so a regression is a routing change, and pin model and prompt versions together.
- **Cost model.** Report cost per 1,000 requests and per user per month (about $0.12 and $0.02 under the assumptions above), and rank the levers: routing, prefix cache, trimming, quantisation, off-peak precompute.
- **Ownership and blast radius.** Serving, orchestration and prompts, safety guards, and retrieval belong to different owners. A bad prompt affects only its template cohort, and per-tenant concurrency caps stop one large tenant starving the shared pools (the same idea as the noisy-neighbour layers in [the multi-tenant gateway](021_multi_tenant_api_gateway_solution.md)). See also [ML and LLM systems](../building_blocks/23_ml_and_llm_systems.md).
- **Build versus buy.** Start on a hosted model <abbr title="Application Programming Interface">API</abbr> to learn the real token distribution, and self-host GPUs only when volume makes it cheaper (at hundreds of GPUs, not tens). Build the orchestrator, ACL-aware retrieval and guards, since they depend on mail data and policy.
- **Phased evolution and what to measure first.** Ship summarise on a hosted <abbr title="Application Programming Interface">API</abbr>, then add routing and prefix caching, then self-hosting. Measure first: the prompt-length distribution (a 3,000-token average can hide a 20K-token tail), the quality gap between small and large on real tasks, the prefix-cache hit potential, and the task mix.

## Build exercise

Put an open model behind a small serving stack with continuous batching (e.g. vLLM). Build a gateway with token-bucket rate limits and token quotas, a prompt template with a long shared prefix, and a router between two model sizes. Load-test with a realistic prompt-length distribution and report time to first token, throughput, and cost per 1,000 requests with and without prefix caching and routing.
