# 038 — Design Video Conferencing

Design a video conferencing service in the spirit of Google Meet or Zoom: people join from a browser or phone, see and hear each other in real time across continents, share their screen, and optionally record. Most meetings are a handful of people, a few have hundreds, and webinars have tens of thousands of listeners.

## Functional requirements

- Create, schedule and join a meeting from a link (browser, mobile, desktop), with a waiting room and host controls (mute, remove, lock).
- Real-time audio and 720p video with adaptive quality, screen sharing, and active-speaker and gallery layouts.
- Meetings of 2 to 500+ interactive participants across regions, plus a webinar mode with panelists and view-only attendees who can raise a hand to speak.
- Roster, mute state, active-speaker indicators and in-meeting chat that stay consistent for everyone.
- Cloud recording with a transcript, and an optional end-to-end-encrypted mode.

## Constraints to assume

- About 1M concurrent meetings at peak, mean 6 participants, with a heavy tail: a few thousand meetings above 100 people, some at 500+. Webinars reach 50,000 view-only attendees. Participants are spread over 20+ regions.
- One-way media latency p95 of 150 to 250 ms within a continent, audio protected before video. Join to first media p95 under 2 s.
- 720p30 video that degrades gracefully to audio-only. Uplinks range from 1 to 100 Mbps and 1 to 5% packet loss is common. Some networks block UDP.
- 10% of meetings recorded, with recording and transcript ready within 15 minutes of the end and kept 30 days.
- A media-node failure must cost affected participants under 10 s and must not end the meeting.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Mesh versus MCU versus SFU with the bandwidth and CPU cost of each, signaling and NAT traversal (ICE, STUN, TURN) with the relay share, simulcast or SVC with per-receiver layer selection, bandwidth estimation, loss recovery and jitter buffering against a latency budget, active-speaker detection, meeting-to-SFU placement with cross-region cascading, scaling one huge meeting or webinar, the recording and transcription pipeline, and the end-to-end-encryption trade-off.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
