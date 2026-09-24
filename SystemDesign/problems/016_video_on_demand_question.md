# 016 — Design a Video-on-Demand Platform

Design a platform where creators upload videos and viewers stream them globally with adaptive quality.

## Functional requirements

- A creator uploads a raw video file; the platform transcodes it into multiple adaptive-bitrate renditions and generates captions.
- Viewers stream a video with quality that adapts to their network, from servers close to them worldwide.
- Content can be access-restricted (private, unlisted, subscriber-only, geo-restricted).
- Playback events (starts, buffering, completion) are recorded for analytics without blocking playback.
- Creators can see upload/processing status and are notified when a video is ready.

## Constraints to assume

- 500,000 hours of video uploaded/day.
- 200 million daily viewers, streaming globally.
- Transcoding turnaround p99 under 30 minutes for a 1-hour video.
- Playback start latency p99 under 2 seconds.
- Analytics may lag playback by up to 5 minutes.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Transcoding pipeline and rendition/access-control delivery strategy.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
