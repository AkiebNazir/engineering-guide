# Graph Databases

Graph databases are a type of NoSQL database that use graph structures for semantic queries with nodes, edges, and properties to represent and store data.

## Key Concepts
- **Nodes**: Represent entities (e.g., people, organizations).
- **Edges**: Represent relationships between nodes (e.g., "KNOWS", "WORKS_AT").
- **Properties**: Key-value pairs attached to nodes and edges for storing metadata.

## Cypher Queries (Neo4j)

Cypher is a declarative graph query language that allows for expressive and efficient querying, updating, and administering of the graph.

### Example: Creating Nodes and Relationships
```cypher
CREATE (alice:Person {name: 'Alice', age: 30})
CREATE (bob:Person {name: 'Bob', age: 28})
CREATE (alice)-[:KNOWS {since: 2020}]->(bob)
```

### Example: Querying the Graph
```cypher
MATCH (p:Person)-[r:KNOWS]->(friend:Person)
WHERE p.name = 'Alice'
RETURN friend.name, r.since
```

Graph databases excel in scenarios requiring complex relationship traversal, such as social networks, recommendation engines, and fraud detection.
