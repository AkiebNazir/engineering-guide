# Integration and End-to-End (E2E) Testing

Unit tests prove that the gears work in isolation. Integration tests prove that the gears mesh together correctly.

## 1. Integration Tests

Integration tests verify that your application communicates correctly with external dependencies (Database, Redis, Kafka, other microservices).

**The Golden Rule:** Never use Mocks for your own database in an integration test.

### Testcontainers
The modern way to run integration tests is using **Testcontainers**. It is a library that dynamically spins up actual Docker containers (e.g., a real Postgres DB) directly from your test code, runs the test against it, and kills the container when the test finishes.

```java
@Testcontainers
class UserRepositoryTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @Test
    void testSaveUser() {
        // This test connects to the ephemeral Docker DB
        UserRepository repo = new UserRepository(postgres.getJdbcUrl());
        repo.save(new User("Alice"));
        assert repo.count() == 1;
    }
}
```

## 2. End-to-End (E2E) Tests

E2E tests verify the entire system from the user's perspective, starting from the UI (Browser/Mobile) all the way down to the database and back.

- **Tools**: Cypress, Playwright, Selenium.
- **Pros**: Highest confidence. If the E2E test passes, the user can definitely buy the product.
- **Cons**: Extremely slow, highly brittle (a button color changes and the test breaks), hard to debug (was it a network timeout, a DB lock, or a UI bug?).

Keep E2E tests limited to the critical "Happy Paths" (e.g., User Login, Checkout Cart). Test the edge cases (invalid password, empty cart) in Unit and Integration tests.
