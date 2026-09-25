# GraphQL Federation Lab

In this lab, we build a federated GraphQL architecture using Apollo Federation.

## Components
1. **Users Subgraph**: Manages user data.
2. **Reviews Subgraph**: Manages product reviews and extends the User type.
3. **Gateway (Router)**: The Apollo Router that aggregates the subgraphs.

### Subgraph 1: Users (schema.graphql)
```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"])

type User @key(fields: "id") {
  id: ID!
  username: String!
}
```

### Subgraph 2: Reviews (schema.graphql)
```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"])

type Review {
  id: ID!
  body: String!
  author: User!
}

type User @key(fields: "id") {
  id: ID!
  reviews: [Review!]!
}
```

## Instructions
1. Implement and start both subgraph servers (e.g., using Apollo Server).
2. Use the `rover` CLI to compose the supergraph schema.
3. Start the Apollo Router with the composed supergraph schema.
