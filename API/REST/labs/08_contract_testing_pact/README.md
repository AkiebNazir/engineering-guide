# REST Contract Testing with Pact

This lab covers Consumer-Driven Contract Testing for REST APIs using Pact.

## Consumer Side
1. Define the interactions (requests and expected responses).
2. Run the tests to generate the Pact JSON file.
3. Publish the Pact file to a Pact Broker.

## Provider Side
1. Fetch the Pact file from the broker.
2. Run the provider verification tests against a running instance of your API.

### Example Node.js Consumer Test snippet
```javascript
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { like } = MatchersV3;

const provider = new PactV3({
  consumer: 'MyConsumer',
  provider: 'MyProvider',
});

provider
  .given('a user exists')
  .uponReceiving('a request to get a user')
  .withRequest({
    method: 'GET',
    path: '/users/1',
  })
  .willRespondWith({
    status: 200,
    body: {
      id: 1,
      name: like('John Doe'),
    },
  });
```
