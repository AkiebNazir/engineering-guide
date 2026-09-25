# 030 — Design an <abbr title="Large Language Model">LLM</abbr>-Powered Assistant Feature

Design an <abbr title="Artificial Intelligence">AI</abbr> writing assistant inside an email product: users ask it to summarise long threads, draft replies, and answer questions about their own mail.

## Functional requirements

- "Summarise this thread", "draft a reply", and free-form questions about the user's mailbox ("when is my flight?").
- Responses stream token by token to the UI.
- Answers about the mailbox use only mail the user is allowed to see, with links to the source emails.
- Per-user and per-organisation usage limits by plan; enterprise admins can disable the feature.
- Unsafe or policy-violating output is blocked; prompt-injection content in emails must not take over the assistant.

## Constraints to assume

- 50 million daily users of the feature; average 6 requests per user per day.
- Average prompt of 3,000 tokens (thread or retrieved context) and 250 output tokens.
- Time to first token under 1 second at p95; full summaries under 5 seconds.
- A fixed GPU budget: cost per request matters as much as latency.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: request rate, tokens per second, GPU capacity, and cost drivers.
3. <abbr title="Application Programming Interface">API</abbr> contract, including streaming and quotas.
4. Baseline architecture: gateway, orchestration, retrieval over the mailbox, model serving.
5. Serving capacity: batching, KV and prefix caching, model routing, and handling peaks.
6. Quotas and rate limits, safety and prompt injection, privacy, evaluation, and fallbacks.
7. One explicit trade-off you would revisit between answer quality and cost.

Do not open the solution until you have made and explained your own design.
