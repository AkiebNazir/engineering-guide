# CDN and Streaming Media

[02_networking.md](02_networking.md) gives the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> primer (cache key, TTL, invalidation) and [08_object_storage.md](08_object_storage.md) gives the origin store. This block goes one level down: how a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is built (hierarchy, request collapsing, steering), how video becomes cacheable files (ingest, encode, package), how the player picks a quality, and what breaks at tens of Tbps. Video is the hardest bulk-delivery problem in interviews because bandwidth, cost, latency and content protection all bind at once.

> 🎯 The one-liner: "A <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> turns a bandwidth problem into a cache-hit-ratio problem. Video is immutable, identical-for-everyone segment files that the player fetches at a bitrate it chooses, so I encode once, package once, cache the hot head inside the ISP or at the edge, collapse misses through a shield so the origin sees one request per object, and enforce entitlement at the license server, not at the byte path."

## What a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is, mechanically

```arch
%% caption: A miss walks up the hierarchy and is collapsed at every tier, so the origin sees roughly one request per object per shield instead of one per edge server.
grid 170x150
node v "Viewer" at 1,0 icon=user
group cdn "CDN hierarchy" color=purple icon=cdn
node e "Edge POP" at 1,1 in cdn icon=edge sub="TLS, hash to one of N servers"
node m "Regional mid-tier" at 1,2 in cdn icon=cache
node s "Origin shield" at 1,3 in cdn icon=shield
node o "Origin" at 1,4 icon=storage sub="object store and packager"
v -> e : "DNS or anycast steering"
e -> m : "miss, collapsed"
m -> s : "miss, collapsed"
s -> o : "miss, collapsed"
e:R -> v:R : "hit: reply from cache"
```

| Mechanism | What it does | Trade-off |
|---|---|---|
| Cache key | Path plus the query params and headers you list. **Signed-URL tokens, session ids and tracking params are excluded**, so every viewer shares one cached object. | Leave a token in the key and the hit ratio is ~0. Leave a real variant (language, codec) out and you serve the wrong bytes. |
| Request collapsing | Concurrent misses for one key trigger one upstream fetch, the rest wait ([07](07_caching.md)). | Waiters share the fetch's latency and failure. |
| TTL, stale-while-revalidate, stale-if-error | Freshness lifetime. RFC 5861 adds serving stale while refetching, and serving stale when the origin returns errors. | Bounded staleness buys origin protection ([28](28_overload_control_and_graceful_degradation.md)). |
| Purge | Push an invalidation to every POP. Propagation is not instant (vendors quote anything from sub-second to minutes) and a partitioned POP misses it. | Never make correctness depend on purge. Use immutable versioned URLs, and short TTLs only on mutable manifests. |
| Hashing inside a POP | Hash the cache key to one of N servers so each object is stored once per POP, not N times. 20 servers × 10 TB hold **200 TB unique** instead of 10 TB repeated. | A viral object concentrates on one server, so replicate the hottest objects to a few servers or use bounded-load hashing ([25](25_partitioning_and_hot_keys.md)). |
| Tiered vs flat | Edge, then mid-tier, then shield. With 90% edge hits and the mid-tier catching 80% of misses, the origin sees `0.1 × 0.2 = 2%` of requests. Without a shield, 200 POPs each fetch a cold object: 200 origin requests instead of 1. | An extra hop on a deep miss and more to operate. Flat is fine for small or regional catalogues. |
| Steering | <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> returns a POP by resolver location or measured latency. Anycast announces one <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> from every POP and BGP picks the path ([27](27_multi_region_and_global_traffic.md)). | <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> is as coarse as the resolver and as slow as its TTL. Anycast follows BGP, not latency, and a route flap can break a long <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> flow. Large CDNs combine both. |
| <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> and DDoS | <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> terminates at the edge, near the viewer, with pooled persistent connections to the origin. Aggregate edge capacity absorbs volumetric attacks ([02](02_networking.md)). | The edge sees plaintext, so protect its keys ([14](14_security.md)). |
| Signed URLs and cookies | The edge checks signature, expiry and a path prefix, then serves the shared object. | Short expiry means a leaked link dies fast, and a long-lived one defeats the point. |

**Decision rule:** normalise the cache key first (it is the cheapest hit-ratio win), collapse at every tier, use immutable URLs so purge is rare, and add a shield before adding POPs.

## Pull, push and popularity-based placement

**Pull** fetches on the first miss: no planning, but the first viewer per POP pays the origin round trip and a synchronised first request stampedes. **Push** (pre-positioning) copies content before demand: you spend bytes on objects nobody may ask for but the first viewer is a hit. Popularity is heavy-tailed, so place the head and pull the tail. With 10,000 titles and a Zipf `s = 1` popularity (assumption), the top 10% (1,000 titles) get `H₁₀₀₀ / H₁₀₀₀₀ = 7.49 / 9.79 ≈ 77%` of views. With the illustrative 18.8 Mbps ladder from the worked example below (`18.8 × 3,600 / 8 = 8.5 GB` per title-hour for one codec) and 1.5 hours per title, that head is `1,000 × 1.5 × 8.5 GB ≈ 13 TB`, a small fraction of a 200 TB POP. So push the head to every POP, pull the tail through the hierarchy.

**ISP-embedded caches.** Netflix's public Open Connect material describes purpose-built cache appliances that Netflix offers to ISPs to install inside the ISP's own network (or that it places at internet exchanges), filled with video files during off-peak hours instead of at peak, with a Netflix control plane choosing which appliance a given client streams from. As Netflix describes it, that control plane stays in the cloud and only the video bytes come from the appliances. The design reason is general: the cheapest byte is one that never crosses a transit or peering link, and off-peak fill moves the unavoidable transfer to when links are idle. The cost is hardware and operations that only pay off at very large, steady volume. **Decision rule:** pull for a long tail and a small operator, popularity-based pre-positioning plus embedded caches when the head is stable and volume is huge.

## The media pipeline: ingest, transcode, package

```arch
%% caption: Encode cost is paid once per title, in parallel chunks, and everything after packaging is a static file the CDN can cache.
node src "Source master" at 0,0 icon=video
node ing "Ingest and validate" at 1,0 icon=check
node spl "Split into chunks" at 2,0 icon=layers sub="at shot boundaries"
node enc "Parallel encode" at 2,1 icon=cpu sub="rungs by codecs"
node stc "Stitch and quality check" at 1,1 icon=gauge sub="VMAF"
node pkg "Package" at 0,1 icon=package sub="CMAF, encrypt CENC, write HLS and DASH manifests"
node org "Origin store" at 0,2 icon=storage
node cdn "CDN tiers" at 2,2 icon=cdn
src -> ing -> spl -> enc -> stc -> pkg -> org
org -> cdn : "fill off-peak or on demand"
```

**Split, encode, stitch.** Cut the source at shot or keyframe boundaries so each chunk is independently encodable, encode every chunk × rung as an idempotent task (a failed or pre-empted task reruns alone), then stitch and check quality. Netflix's tech blog ("High Quality Video Encoding at Scale", 2015) describes this chunked, parallel cloud approach. Derived: a 2-hour title at 20 s chunks is 360 chunks, × 6 rungs = 2,160 tasks. At 10 core-minutes each that is 360 core-hours, about 15 days on one core and **10 minutes** on 2,160 cores. Parallelism buys wall clock, not cost: at ~$0.3 per core-hour (assumption) that is about $108 for the title, ≈ $54 per title-hour, which the break-even below rounds to $50. Rate control must be coordinated across chunks or quality visibly jumps at the seams.

| Codec | Compression vs H.264 (rough, content-dependent) | Encode cost | Device support |
|---|---|---|---|
| H.264 / AVC | Baseline | Cheapest | Universal, the safe floor rung |
| HEVC / H.265 | Roughly 30–50% fewer bits | Several × H.264 | Wide hardware decode, fragmented licensing |
| VP9 | Comparable to HEVC | Several × H.264 | Chrome, Android, many TVs, royalty-free |
| AV1 | A further ~20–30% (Netflix reported roughly 20% over VP9 in its 2020 Android launch post) | Several × to an order of magnitude more | Newer hardware, software fallback drains battery, royalty-free |

Break-even (assumptions ours): 30% off a 5 Mbps stream saves `0.3 × 2.25 GB = 0.68 GB` per viewed hour, or $0.0068 at $0.01/GB. If the extra encode costs $50 per title-hour, a title needs `50 / 0.0068 ≈ 7,400` viewed hours to pay back. So run expensive codecs only on the head, keep H.264 for the tail, and let the player advertise the codecs it can decode.

**Bitrate ladders.** A fixed ladder wastes bits on easy content and starves hard content. Netflix's "Per-Title Encode Optimization" (2015) chooses a ladder per title from its measured complexity. Its shot-based "Dynamic Optimizer" work (2018) goes finer, picking per-shot settings to maximise quality at a bitrate, where quality is measured by VMAF, the perceptual metric Netflix published and open-sourced ("Toward A Practical Perceptual Video Quality Metric", 2016). The price is many trial encodes and a bespoke ladder per title that the player must read from the manifest. **Decision rule:** fixed ladder for UGC and the tail, per-title or per-shot for the head. The full VOD design is [016](../solutions/016_video_on_demand_solution.md).

## Segments, manifests and adaptive bitrate

HLS (RFC 8216) and MPEG-DASH describe the same idea, a manifest listing renditions plus a sequence of short segment files. CMAF (fragmented MP4) lets one set of segments serve both, so the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> caches one copy, not two. Segment duration is a five-way trade:

| Segment | Start-up | Switch agility | Requests per viewer-hour | Efficiency | Live latency |
|---|---|---|---|---|---|
| 2 s | Fast | High | 1,800 (500k rps per 1M viewers) | Lower, a keyframe at each start | Lowest |
| 6 s | Slower | Low | 600 (167k rps per 1M viewers) | Higher | Latency floor of several × 6 s |

**ABR** runs in the player, so servers stay stateless and cacheable.

| Algorithm | Signal | Strength | Weakness |
|---|---|---|---|
| Throughput-based | Recent segment download rates (harmonic mean, safety factor) | Reacts fast, needed at start-up | Noisy estimates, oscillation, over-reacts to short dips |
| Buffer-based | Buffer occupancy only: lowest rung below a reservoir, highest above a cushion, linear between (Huang et al., SIGCOMM 2014, tested on Netflix) | Fewer rebuffers, stable quality | Slow to ramp up with an empty buffer |
| Hybrid / MPC | Throughput prediction plus buffer, optimised over a look-ahead horizon (Yin et al., SIGCOMM 2015) | Best QoE trade-offs | Needs a good predictor, more complex |

**QoE metrics:** start-up time, rebuffer ratio (stall time ÷ play time), average bitrate or VMAF, and number and size of switches. They conflict (a higher rung raises quality and rebuffer risk), so QoE is a weighted combination, as in the MPC paper. **Start-up budget** (assumption: 30 ms RTT, 10 Mbps, 2 s segments, first rung 1.75 Mbps): <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> 20 ms + <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> and <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> 75 ms + manifest 40 ms + first segment `1.75 × 2 / 10 = 0.35 s` plus RTT ≈ 380 ms (the DRM license, ≈ 120 ms, is fetched in parallel) + decode and first frame 100 ms ≈ **615 ms**, and 735 ms if the license is serial. So start on a low rung, prefetch manifest and first segment on hover, and parallelise the license.

## DRM and entitlement

Segments are encrypted once with Common Encryption (ISO/IEC 23001-7, CENC) so one CMAF file set can work with Widevine, FairPlay and PlayReady (the `cbcs` scheme, on current devices), and the decryption keys travel in a **license** that the player's content-decryption module requests from a license server. That server checks subscription, region, device security level and concurrent streams. The segments are identical for every viewer and stay cacheable. Entitlement is enforced where the rate is low (session start and license issue), not per segment.

```arch
%% caption: Entitlement is enforced at the playback API and the license server, so segments stay identical for every viewer and stay cacheable.
node p "Player" at 1,0 icon=client color=slate
node api "Playback API" at 0,1 icon=server color=purple
node cdn "CDN Edge" at 1,1 icon=cdn color=teal
node lic "License Server" at 2,1 icon=lock color=amber

p -> api : "play title X"
node check "check sub, region, concurrency" at 0,2 shape=text
api -> check -> api
api -> p : "manifest URL & token, license URL"

p -> cdn : "GET manifest"
cdn -> p : "manifest from cache"

p -> lic : "license req (device challenge)"
lic -> p : "license with keys"

p -> cdn : "GET first segment (low rung)"
cdn -> p : "encrypted segment (same for all)"

node abr "GET next segment at ABR-chosen rung" at 1,2 shape=card
p -> abr -> cdn
```

The cost is that the license server sits on the start-up critical path, so it needs its own regional capacity and availability target, and DRM support varies by device. **Decision rule:** signed short-lived URLs for access to bytes, DRM for content protection, and never per-segment auth calls.

## Live streaming

Pipeline: contributor to ingest (RTMP is legacy, SRT and WebRTC-based ingest handle loss better), real-time ladder transcode, packaging into segments or parts, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, player. Live changes three things. The manifest mutates every segment (short TTL, and the latest segment is requested by every viewer at once, a synchronised herd), the encode cannot use slow presets, and latency becomes a product feature.

| Mode | Delivery | Glass-to-glass (derived) | Scaling |
|---|---|---|---|
| Classic HLS/DASH, 6 s segments | Whole segments over the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> | Encode 0.5 + ingest 0.2 + transcode 1 + wait for the segment 6 + <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> 0.2 + player buffer of 3 segments (18) ≈ **26 s** | Excellent, plain cacheable files |
| Low-latency HLS or DASH | Parts of ~0.5 s (LL-DASH: CMAF chunks sent with <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> chunked transfer as they are encoded) published before the segment ends, LL-HLS playlist requests block until the part exists | 0.5 + 0.2 + 1 + 0.5 + 0.2 + player buffer of 3 parts (1.5) = **3.9 s** | Still <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>-cacheable, but needs collapsing on blocked requests |
| WebRTC | Per-viewer connection to an SFU ([22](22_realtime_and_collaboration.md)) | Under 1 s | No shared <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> cache, so cost per viewer is high and scale is limited |

A **DVR window** is the sliding manifest of retained segments. At the ladder below (18.8 Mbps) a 2-hour window is `18.8 × 7,200 / 8 = 17 GB` per channel. Old segments are immutable and cold, so seek-back traffic goes to the shield and origin, not the hot edge. **Decision rule:** pick latency by product (sports and auctions need seconds, news and concerts tolerate more), and use WebRTC only for small interactive audiences ([033](../solutions/033_live_streaming_and_comments_solution.md)).

## Worked example: a 10M-viewer live event

Assumptions (ours): 10M concurrent viewers, 4 Mbps average delivered, 2-hour event, illustrative six-rung ladder 0.3, 0.75, 1.75, 3, 5, 8 Mbps (sum 18.8), 100 Gbps servers run at 70%.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Egress | 10M × 4 Mbps | **40 Tbps** (5 TB/s) | No origin can serve this, so the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is the product. |
| Fan-out | 40 Tbps ÷ 18.8 Mbps of unique bytes | ≈ 2.1M× | Origin load depends on shield count, not viewers, if collapsing works. |
| Edge servers | 40 Tbps ÷ 70 Gbps | ≈ 570 servers | About 600 with headroom. |
| POPs | 40 Tbps ÷ 1–2 Tbps per POP, ×2 for skew toward big metros | ≈ 40–80 POP-equivalents | A zone or POP loss must be absorbable by neighbours (N+1 per metro). |
| Bytes | 5 TB/s × 7,200 s | 36 PB | Egress at $0.005–$0.05 per GB (assumed range, committed to list) is **$0.18M–$1.8M** for this one event. |

So: the bill is set by who carries the bytes, which is why large operators build peering and embedded caches, and the risk is a few POPs at their interconnect limit rather than the total. Serving from inside the ISP removes the transit component of that price.

## Origin protection and cold popular objects

The worst moment is a cold, hugely popular object: a premiere or a live segment that every edge server wants in the same second. With 200 POPs × 20 servers = 4,000 edge servers and no collapsing, one 3.75 MB segment produces `4,000 × 3.75 MB = 15 GB` of origin egress in a burst, for a segment the origin could have shipped once. With hashing inside the POP, collapsing at each tier and one shield, the origin sees **one fetch per rung**. Beyond that: pre-position a premiere before it opens, apply stale-if-error so an origin blip does not become a viewer error, rate-limit fetches per shield (an overloaded origin should shed the tail, not the head, per [28](28_overload_control_and_graceful_degradation.md)), and expect a POP failure to shift traffic to neighbours with cold caches, where lower ABR rungs are the natural brownout.

## Interview angles

- **"How does video get from upload to a viewer?"** Ingest, chunk-parallel encode into a ladder, CMAF plus manifests, origin, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, player ABR. Name where cost and latency sit.
- **"Edge hit ratio is 60%. Fix it."** Normalise the cache key and drop tokens, hash inside the POP, add a shield, use immutable URLs with SWR, pre-position the head.
- **"10M people watch a live game. What breaks first?"** Compute Tbps and POP interconnects, the manifest and newest-segment herd, license-server capacity, then collapsing, a shield and a lower-rung brownout.
- **"How do you cut start-up time?"** A conservative first rung, prefetch, a parallel license fetch, connection reuse, small first segments.
- **"Is a cached segment a leak?"** No: DRM-encrypted and useless without a license, with entitlement at the license server and short-lived signed URLs at the edge.
- **"Why 2 to 6 second segments?"** The five-way trade in the table above, with the request-rate arithmetic.
- **"A POP dies."** Steering moves viewers, neighbours are cold, ABR steps down, and capacity is N+1.

## Related building blocks

- [02_networking.md](02_networking.md) — the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> primer, <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>, DDoS
- [07_caching.md](07_caching.md) — collapsing, stale-while-revalidate, stampedes
- [08_object_storage.md](08_object_storage.md) — origin store, multipart upload, lifecycle tiers
- [18_back_of_envelope_estimation.md](18_back_of_envelope_estimation.md) — the bits-and-bytes arithmetic
- [25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md) — consistent hashing and hot objects
- [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md) — <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> and anycast steering
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) — shedding, herds, brownouts
- [22_realtime_and_collaboration.md](22_realtime_and_collaboration.md) — WebRTC and real-time delivery
- [016 Video on Demand](../solutions/016_video_on_demand_solution.md) and [033 Live Streaming and Comments](../solutions/033_live_streaming_and_comments_solution.md) — the full designs built from these parts
