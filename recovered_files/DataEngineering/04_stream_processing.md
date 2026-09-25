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
