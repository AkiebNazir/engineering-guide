# Redis Streams

Redis Streams is a data type which models a log data structure in a more abstract way. It provides a way to append entries and process them with multiple consumers, providing features similar to Apache Kafka.

## Key Concepts
- **Entries**: An entry in a stream is a set of field-value pairs.
- **Consumer Groups**: Allow a group of clients to cooperate consuming a different portion of the same stream of messages.

## Basic Commands

### Adding Entries
Use `XADD` to append a new entry to a stream. The `*` auto-generates a unique ID.
```bash
> XADD mystream * sensor-id 1234 temperature 19.8
"1518951480106-0"
```

### Reading Entries
Use `XRANGE` to get a range of entries.
```bash
> XRANGE mystream - +
1) 1) "1518951480106-0"
   2) 1) "sensor-id"
      2) "1234"
      3) "temperature"
      4) "19.8"
```

Use `XREAD` for reading multiple streams, optionally blocking until new data arrives.
```bash
> XREAD BLOCK 0 STREAMS mystream $
```

### Consumer Groups
Create a consumer group with `XGROUP CREATE`:
```bash
> XGROUP CREATE mystream mygroup $
```
Read through the consumer group with `XREADGROUP`:
```bash
> XREADGROUP GROUP mygroup alice COUNT 1 STREAMS mystream >
```

Redis Streams are ideal for message brokers, event sourcing, and unified logs.
