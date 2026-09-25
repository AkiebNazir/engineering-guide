# Python Engineering — Advanced Production-Grade Curriculum

This is not a DSA/algorithm curriculum (see `../PyDSA` for that). This module teaches
**production-grade, idiomatic Python through 25 real-world engineering problems** — the
Python-idiom counterpart to `../GoEngineering`'s same 25 topics. Same engineering
problems, same rigor, adapted to how a senior Python engineer actually solves them:
`asyncio` instead of goroutines/channels, `typing.Protocol` instead of Go interfaces,
context managers instead of `defer`, exception hierarchies instead of error wrapping.

Assume competence. No beginner syntax explanations — every file explains *design
decisions*, trade-offs, performance, error handling, concurrency safety, and real-world
<abbr title="Application Programming Interface">API</abbr>/service design. Target **Python 3.12+** idioms: `asyncio.TaskGroup`, <abbr title="Python Enhancement Proposal. A design document providing information to the Python community, describing a new feature or its environment.">PEP</abbr> 695 generics
(`class Foo[T]`), `tomllib`, structural pattern matching, `ExceptionGroup`.

## Layout

```
PyEngineering/
  .venv/                        shared virtualenv for every problem
  requirements.txt              third-party deps used across the curriculum
  NN_topic_slug/
    NN_topic_slug_explanation.py   the challenge: stubs + TODOs, runs/imports as-is
    NN_topic_slug_solution.py      complete, idiomatic, heavily commented reference
    NN_topic_slug_test.py          pytest table-driven tests, when the topic calls for it
```

Unlike Go, Python files don't collide on shared symbols across files in the same
directory (each file is its own module), so — unlike `GoEngineering` — the three files
for a topic sit directly together in one folder, matching the file names in the original
spec.

## Workflow

1. Read `NN_topic_slug/NN_topic_slug_explanation.py` top-to-bottom — the header docstring
   states what you're building, why it matters, the spec, and acceptance criteria.
2. Implement every `# TODO:`. Run `mypy` and the file itself as you go.
3. Compare against `NN_topic_slug/NN_topic_slug_solution.py` — read the reasoning above
   each block, not just the code.
4. Run the tests where present: `.venv/bin/pytest NN_topic_slug/`.
5. Attempt the stretch goals listed at the bottom of the explanation file.

## Toolchain used across the curriculum

Standard library first; third-party only where it's the genuine real-world default —
each problem's header comment states why. Fixed choices for consistency across problems:

| Concern | Choice | Why |
|---|---|---|
| Web framework | `fastapi` + `uvicorn` | Type-hint-driven, async-native; the modern Python default over Flask for new services. |
| <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> client | `httpx` | `requests` has no native async/context-deadline story; `httpx` does. |
| Database | stdlib `sqlite3` | Zero external service to stand up; same transaction/isolation concepts transfer to Postgres. |
| Property testing | `hypothesis` | The real-world default for property-based testing in Python. |
| <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> | `grpcio` + `grpcio-tools` | No viable stdlib alternative. |
| Metrics | `prometheus_client` | The real-world default for a Python service's `/metrics` endpoint. |
| Everything else (config, concurrency, caching, pub/sub, DI, generics, profiling, <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>) | stdlib only | `tomllib`, `asyncio`, `dataclasses`, `typing`, `cProfile`/`tracemalloc`, `json`. |

## Curriculum

| # | Problem | Core concepts |
|---|---|---|
| 01 | <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr> service | FastAPI routing, Pydantic validation, <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, graceful shutdown |
| 02 | Middleware chain | Structured logging, request IDs, exception handling, timeouts, auth |
| 03 | <abbr title="Application Programming Interface">API</abbr> client with retries | Backoff, jitter, circuit breaker, `httpx` timeouts/cancellation |
| 04 | Custom stream reader/writer | `io` subclassing, generators as transforms, backpressure |
| 05 | Large file line processor | Chunked reads, memory-bounded parsing, iterator pipelines |
| 06 | Atomic file store | Temp file + `os.replace`, `fsync`, permissions, crash safety |
| 07 | Filesystem walker | `pathlib`, `os.walk`, testability with `tmp_path` |
| 08 | Config loader | `tomllib`, env overrides, layered config, validation via dataclasses |
| 09 | Database repository layer | `sqlite3`, connection handling, parameterized queries, row mapping |
| 10 | Transactions & concurrency control | Isolation levels, optimistic locking, retryable lock errors |
| 11 | Migrations & schema management | Versioned migrations, idempotency, rollback strategy |
| 12 | Worker pool | Bounded concurrency via `asyncio.Semaphore`/`TaskGroup`, cancellation |
| 13 | Pipeline | Fan-out/fan-in with `asyncio.Queue`, clean shutdown, leak-free design |
| 14 | Concurrent cache | Lock-protected dict vs sharded locks, single-flight, TTL eviction |
| 15 | Rate limiter | Token bucket, per-key limiting, `asyncio`-safe implementation |
| 16 | Pub/sub event bus | Subscriber lifecycle, slow-consumer handling, graceful close |
| 17 | Error taxonomy | Exception hierarchy, `ExceptionGroup`, mapping to <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> codes |
| 18 | Dependency injection & layering | `typing.Protocol` ports and adapters, wiring at the composition root |
| 19 | Generic utilities | <abbr title="Python Enhancement Proposal. A design document providing information to the Python community, describing a new feature or its environment.">PEP</abbr> 695 type parameters, `Result`/`Option` containers, when generics hurt |
| 20 | Table-driven tests & fakes | `pytest.mark.parametrize`, fixtures, fakes, `unittest.mock` |
| 21 | Fuzzing & property testing | `hypothesis` strategies, invariants, shrinking |
| 22 | Profiling & optimization | `cProfile`, `tracemalloc`, allocation reduction, honest benchmarks |
| 23 | Custom <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> & protobuf encoding | `json` custom encode/decode hooks, streaming, schema evolution |
| 24 | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> service | Protobuf contract, interceptors, streaming, deadlines |
| 25 | Production service capstone | Health checks, `/metrics`, structured logging, Dockerfile, <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr> |
| 26 | Metaprogramming & Decorators | Class decorators, descriptors (`__get__`, `__set__`), metaclasses |
| 27 | Asyncio Deep Dive | Contextvars, event loop tuning, `run_in_executor`, handling blocking I/O |
| 28 | Memory Management & C Extensions | Garbage collection, `weakref`, `ctypes`, `cffi`, reference counting |
| 29 | <abbr title="Abstract Syntax Tree. A tree representation of the abstract syntactic structure of source code written in a programming language.">AST</abbr> Manipulation & Introspection | `ast`, `inspect`, dynamic execution, custom linters |
| 30 | Packaging, Distribution & Monorepos | Poetry/uv, native wheels (`cibuildwheel`), entry points |
| 31 | Advanced <abbr title="Object-Oriented Programming - A programming paradigm based on the concept of 'objects', which can contain data and code.">OOP</abbr> & <abbr title="Method Resolution Order. The order in which a programming language resolves a method or attribute in a class hierarchy.">MRO</abbr> | Abstract Base Classes, Multiple Inheritance, Mixins, `super()` |
| 32 | Pydantic v2 Deep Dive | Model/Field validators, custom serializers, nested models |
| 33 | Concurrency Models & IPC | `multiprocessing` vs `threading`, Pipes, bypassing the <abbr title="Global Interpreter Lock. A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.">GIL</abbr> |
| 34 | The <abbr title="Global Interpreter Lock. A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.">GIL</abbr> & Subinterpreters | Releasing <abbr title="Global Interpreter Lock. A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.">GIL</abbr> in C, Python 3.12+ <abbr title="Python Enhancement Proposal. A design document providing information to the Python community, describing a new feature or its environment.">PEP</abbr> 684 subinterpreters |
| 35 | Advanced Typing & Static Analysis | `TypeGuard`, `@overload`, `Literal`, Covariance/Contravariance |

The Go-parallel curriculum lives in `../GoEngineering`.
