# GraphQL Contract Testing with Pact

This lab focuses on Contract Testing for GraphQL using Pact.

## How it works
GraphQL contract testing is similar to REST, but the interactions involve POSTing GraphQL queries and asserting on the returned JSON `data` structure.

### Example GraphQL Consumer Interaction
```javascript
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');

// Setup Pact provider...

provider
  .uponReceiving('a GraphQL query for a user')
  .withRequest({
    method: 'POST',
    path: '/graphql',
    headers: { 'Content-Type': 'application/json' },
    body: {
      query: `
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            name
          }
        }
      `,
      variables: { id: "1" }
    }
  })
  .willRespondWith({
    status: 200,
    body: {
      data: {
        user: {
          id: "1",
          name: MatchersV3.like("John Doe")
        }
      }
    }
  });
```
