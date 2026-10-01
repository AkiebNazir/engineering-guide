# Testing & Quality

Code that isn't tested is broken in ways nobody has found yet. This module teaches how
professional teams build confidence in their software, from a single pytest function up to
deliberately breaking production on purpose: the testing pyramid, test doubles, integration
and end-to-end tests with real dependencies, property-based and mutation testing, contract
testing between microservices, and chaos engineering.

## Who this is for

- **Students and new grads** who have written a few `assert`s and want to know how testing is
  done at scale, and what interviewers mean by "mock vs fake" or "the pyramid".
- **Working engineers (L3–L5)** preparing for interviews or setting a test strategy for a
  service: Testcontainers, Playwright, Hypothesis, Pact, Chaos Mesh.
- **Senior and staff engineers** who own CI, flakiness, and reliability policy across teams.

Every chapter starts with a from-zero **Foundations** section, then goes deep, and ends with
common interview questions, a table of what each engineering level (Intern to Staff+) is
expected to know, and an interview checklist. The Python examples were run with pytest 9.1,
Hypothesis 6.168, mutmut 3.8 and pact-python 3.4; the Go examples with Go 1.24.

## Read in this order

1. [The Testing Pyramid and Unit Tests](01_testing_pyramid.md): what a test is, the pyramid and its
   alternatives, Google's test sizes, pytest and Go table-driven tests, TDD, flaky tests, coverage,
   and keeping a large suite fast.
2. [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md): seams, the five kinds of double,
   `unittest.mock` done right (autospec, "patch where it is looked up"), fakes kept honest with
   contract suites, Go interfaces and `httptest`, controlling time.
3. [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md): real databases with
   Testcontainers (Python, Go, Java), test-data isolation, HTTP and broker boundaries, Playwright
   E2E tests that aren't flaky, and where each layer runs in the pipeline.
4. [Advanced: Property-Based and Mutation Testing](04_property_and_mutation.md): Hypothesis
   properties, shrinking and stateful testing, Go native fuzzing, and mutation testing with real
   mutmut output.
5. [Microservices: Contract Testing](05_contract_testing.md): consumer-driven contracts with Pact
   from consumer test to provider verification, the broker, `can-i-deploy`, safe API evolution,
   and the alternatives. Includes the live flow of the whole handshake.
6. [Resilience: Chaos Engineering](06_chaos_engineering.md): principles, experiment design, fault
   types, Chaos Mesh / AWS FIS / Toxiproxy / Istio fault injection, safe production experiments,
   and game days. Includes a live flow of an experiment that holds and one that aborts.

Chapters 1–3 are the core that every engineer needs; 4–6 can be read in any order after them.

## Prerequisites

- Comfortable reading Python; Go helps for the Go examples (see `GoStdLib/` and `GoEngineering/`).
- Basic HTTP and SQL. Chapter 3 assumes you know what Docker is; chapter 6 assumes a rough idea of
  Kubernetes (see `Tool-Kit/`).

## Related modules

- `CICD/`: where these tests run (pipelines, deployment strategies, feature flags, rollbacks).
- [Testability, Refactoring, and Legacy Code](../SoftwareDesign/05_testability_refactoring_and_legacy_code.md): designing code with seams.
- `PyEngineering/20_table_driven_tests_fakes/`, `PyEngineering/21_fuzzing_property_testing/`, and the
  Go equivalents in `GoEngineering/`: hands-on exercises.
- [Consumer driven contracts pact](../API/REST/labs/python/06_consumer_driven_contracts_pact.py) and
  `API/REST/labs/golang/08_provider_verification_and_can_i_deploy/`: contract testing built from scratch.
- [Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md) and
  [Observability and Reliability](../SystemDesign/building_blocks/15_observability_and_reliability.md): the patterns chaos experiments test.
