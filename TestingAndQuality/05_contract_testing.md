# Microservices: Contract Testing

In a microservices architecture, Team A writes the Orders service, and Team B writes the Users service.
Orders calls Users to get an email address.

If Team B renames `emailAddress` to `email_address` in their JSON response, the Orders service will crash in production. How do we prevent this?

## 1. The Problem with E2E
You could run an E2E test that spins up both Orders and Users, but managing 50 microservices in a single test environment is notoriously flaky and slow.

## 2. Consumer-Driven Contract Testing (Pact)

Contract testing ensures that services can communicate without needing to spin them up simultaneously.

### Step 1: The Consumer (Orders) writes a Contract
The Orders team writes a unit test using a Contract framework (like Pact). The test says: "I expect that when I request `/users/42`, the response will have a field called `emailAddress` of type String."

The framework generates a JSON Contract file and uploads it to a central Contract Broker.

### Step 2: The Provider (Users) verifies the Contract
When the Users team runs their CI pipeline, the framework downloads the Contract from the Broker. It automatically replays the Orders team's request against the Users service and checks the response.

If the Users team renamed the field to `email_address`, the framework sees the response no longer matches the Contract, and the Users team's CI build fails instantly.

```arch
%% caption: Consumer-driven contract testing prevents breaking changes between microservices without requiring full E2E environments.
route straight
node c "Consumer\\n(Orders)" at 0,0 icon=app color=blue
node b "Pact Broker\\n(Stores Contracts)" at 2,0 icon=file color=slate
node p "Provider\\n(Users)" at 4,0 icon=app color=green

c -> b : "Uploads\\nexpectations"
b -> p : "Downloads &\\nverifies"
```

**Result**: Team B is physically prevented from merging code that breaks Team A, and neither team ever had to spin up the other's database to run a test.
