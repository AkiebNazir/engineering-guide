# 05 Stream Processing

Batch processing (e.g., nightly Spark jobs) introduces latency before data is available for analysis. In scenarios demanding real-time insights (fraud detection, real-time analytics, ride-sharing surge pricing, IoT telemetry), Data Engineers rely on **Stream Processing** pipelines to compute on data in motion.

## Event-Driven Architecture

An Event-Driven Architecture (EDA) is built on the paradigm that changes in state (events) are produced, detected, consumed, and reacted to in real-time. Instead of a monolithic system periodically polling databases, decoupled services emit events to a central nervous system.

```arch
node pa "Mobile App" at 0,0 icon=users color=slate
node pw "Web Server" at 0,1 icon=server color=slate
node b "Message Broker" at 1,0 icon=process color=teal
node d "Stream Processor" at 2,0 icon=process color=blue
node e "Real-time OLAP DB" at 3,0 icon=db color=purple
node f "Alerting Service" at 3,1 icon=gateway color=red
pa -> b : "Emit Event"
pw -> b : "Emit Event"
b -> d : "Subscribe/Consume"
d -> e : "Write Results"
d -> f : "Trigger Action"
```

## Message Brokers (The Nervous System)

A Message Broker (or Event Bus) is an intermediary system that accepts messages from producers and delivers them to consumers. It acts as a buffer and guarantees delivery, decoupling the sender and receiver.

### Apache Kafka
Kafka is a distributed event streaming platform built for high throughput and fault tolerance. Data in Kafka is organized into **Topics** (logical channels), partitioned across multiple brokers, and replicated for durability. Kafka stores events on disk, allowing consumers to rewind and replay data.

### Google Cloud Pub/Sub
Pub/Sub is a fully-managed serverless messaging service on Google Cloud. It excels at auto-scaling and global availability without the operational overhead of managing Kafka clusters. Unlike Kafka's offset-based retention, Pub/Sub traditionally uses message acknowledgment, though it now supports retention and replay.

## Stream Processing Engines

Stream Processing Engines continuously ingest streams from message brokers, compute stateful aggregations, joins, or ML inferences, and output the processed data.

### Apache Flink
The industry standard for stateful, distributed stream processing. Flink processes events strictly one-by-one (true streaming), manages massive internal state (e.g., keeping track of millions of open user sessions), and features a robust snapshotting mechanism (Checkpoints) to object storage (like S3/GCS) to guarantee exact-once processing semantics even during node crashes.

### Apache Spark Streaming
Originally designed for batch processing, Spark supports streaming through **Structured Streaming**. Instead of processing event-by-event, Spark processes data in "micro-batches" (e.g., every 1 second). This provides slightly higher latency than Flink but offers unified APIs for batch and stream processing.

## Time and State Management

Stream processing introduces profound complexities around timing and ordering, primarily due to network latency, distributed system clocks, and mobile offline scenarios.

### Event Time vs. Processing Time
- **Event Time**: The timestamp when the event *actually occurred* on the source device (e.g., when the user clicked a button on their phone).
- **Processing Time**: The timestamp when the stream processor *received* or processed the event.

To generate accurate analytics (e.g., exactly how many clicks happened between 1:00 and 1:05), systems must use **Event Time**, which requires handling out-of-order and late-arriving data.

### Watermarks
A **Watermark** is a heuristic threshold that tells the stream processor how long to wait for late events. If a watermark is set for a 10-minute delay, the system will allow events to arrive up to 10 minutes late. Once the processing engine's watermark progresses past a window's end time plus the allowed lateness, the window is finalized. Any data arriving after the watermark is typically discarded or sent to a dead-letter queue.

## Windowing Strategies

You cannot compute a traditional aggregation (like "sum" or "average") over an infinite, unbounded stream. You must slice the stream into finite chunks called **Windows**.

1. **Tumbling Windows**: Fixed-size, contiguous, and non-overlapping time intervals.
   *Example: Sum of sales every 5 minutes (1:00-1:05, 1:05-1:10).*
2. **Sliding (Hopping) Windows**: Overlapping time intervals of a fixed size.
   *Example: Moving average over the last 5 minutes, updated every 1 minute.*
3. **Session Windows**: Dynamic windows defined by periods of activity followed by a gap of inactivity.
   *Example: All clicks by a user until they are inactive for 30 minutes.*

```arch
node s "Data Stream" at 0,1 icon=doc color=slate
node t "Tumbling Window" at 1,0 shape=card color=blue sub="Group by strict [00:00 - 00:05)"
node l "Sliding Window" at 1,1 shape=card color=amber sub="Group in [00:00-05), [00:01-06)"
node e "Session Window" at 1,2 shape=card color=teal sub="Group user actions until gap > 10m"
s -> t
s -> l
s -> e
```
# Stream Processing Fundamentals

Batch processing (like Spark jobs running nightly) introduces a 24-hour delay before data is available for analysis. When businesses need real-time dashboards (e.g., fraud detection, ride-sharing surge pricing), Data Engineers build Stream Processing pipelines.

## 1. The Core Concepts

A stream processor continuously consumes events from an event bus (like Apache Kafka), computes aggregations on the fly, and outputs the results continuously.

### Time: Event vs Processing Time
- **Event Time**: The timestamp when the event actually occurred on the user's phone.
- **Processing Time**: The timestamp when the stream processor received the event.

Because mobile phones lose network connection, events can arrive out of order or hours late. Stream processing systems must group data by *Event Time* to be accurate.

### Windows
You cannot compute an "average" over an infinite stream of data. You must chop the stream into finite chunks called Windows.

1. **Tumbling Window**: Fixed, non-overlapping (e.g., 1:00-1:05, 1:05-1:10).
2. **Hopping/Sliding Window**: Overlapping (e.g., the last 5 minutes, updated every 1 minute).
3. **Session Window**: Dynamic. Groups events for a specific user, closing the window after a period of inactivity (e.g., 30 minutes with no clicks).

### Watermarks
If an event is 2 hours late, how long should the 1:00-1:05 window stay "open" waiting for it? 
A **Watermark** is a threshold. If the watermark is set to 10 minutes, the processor will wait 10 minutes for late data. Once the watermark passes 1:15, the 1:00-1:05 window is finalized, and any data arriving later is discarded (or sent to a dead-letter queue).

## 2. Tools of the Trade

- **Apache Flink**: The industry standard for heavy-duty, stateful stream processing. Flink manages massive amounts of internal state (keeping track of millions of open windows) and checkpoints that state to S3 so it can recover perfectly if a node crashes.
- **Spark Structured Streaming**: Uses "micro-batches". Instead of processing event-by-event like Flink, it processes data in 1-second chunks. Easier if you already know Spark, but slightly higher latency than Flink.
- **Kafka Streams / ksqlDB**: Lightweight libraries that run directly inside your application (no separate cluster needed). Great for simple joins and aggregations directly on top of Kafka.
