# 033 — Design Live Streaming and Live Comments

Design a live video platform in the spirit of Twitch, YouTube Live or Facebook Live: broadcasters go live from an encoder or phone, millions watch with adaptive quality, and viewers chat and react in real time on the same page.

## Functional requirements

- A broadcaster starts a stream with a stream key and an ingest protocol (RTMP, SRT or WebRTC) and can be live within seconds.
- Viewers watch adaptive-bitrate playback on web, mobile and TV, with a standard tier and a low-latency tier.
- Live comments and reactions, shown in sync with what the viewer is watching (no spoilers from chat running ahead of video).
- Moderation: automated filtering, per-channel rules (slow mode, blocked terms) and moderator actions that take effect within seconds.
- Rewind during the broadcast (DVR), VOD of the recording soon after it ends, and live viewer counts.

## Constraints to assume

- 200,000 concurrent broadcasters (mean 5 Mbps ingest, up to 1080p60) and about 15M concurrent viewers at the platform peak, 10M of them on the single largest event.
- Glass-to-glass p95: under 10 s for the standard tier, under 3 s for the low-latency tier; playback start under 2 s.
- On the biggest stream: peaks of 300,000 comments/s and 2M reaction taps/s for a few seconds after a key moment. A viewer can read about 5 messages/s.
- Comment post-to-display p99 under 2 s; a moderator delete visible to 99% of viewers within 2 s.
- VOD available within 1 minute of stream end, kept 14 days; an ingest or transcoder failure must cost viewers less than 10 s.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Ingest and redundancy, the live transcoding ladder and packaging with a latency budget by stage, CDN fan-out with origin protection for one mega-stream, live comment and reaction fan-out to millions, and the moderation pipeline.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
