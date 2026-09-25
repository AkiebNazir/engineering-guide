# MongoDB Sharding

Sharding is a method for distributing data across multiple machines. MongoDB uses sharding to support deployments with very large data sets and high throughput operations.

## Key Concepts
- **Shard**: Contains a subset of the sharded data. Each shard can be deployed as a replica set.
- **Mongos**: Acts as a query router, providing an interface between client applications and the sharded cluster.
- **Config Servers**: Store metadata and configuration settings for the cluster.

## Shard Keys
The shard key determines the distribution of the collection's documents among the cluster's shards. The shard key consists of a field or multiple fields in the documents.

- **Hashed Sharding**: Distributes data across shards using a hashed index of the shard key value. Good for even data distribution.
- **Ranged Sharding**: Divides data into ranges based on the shard key values. Useful for range-based queries.

## Example
To shard a collection:

1. Enable sharding for the database:
```javascript
sh.enableSharding("myDatabase")
```

2. Shard the collection using a specific key:
```javascript
sh.shardCollection("myDatabase.myCollection", { "userId": 1 })
```

Proper shard key selection is critical for the performance and scalability of a sharded cluster.
