# Go Engineering — Advanced Production-Grade Curriculum

This is not a DSA/algorithm curriculum (see `../GoDSA` for that). This module teaches
**production-grade, idiomatic Go through 35 real-world engineering problems**: services,
concurrency, I/O, databases, testing, and operational concerns — the things that show up
in a real backend codebase, not an interview whiteboard.

Assume competence. No beginner syntax explanations — every file explains *design
decisions*, trade-offs, performance, error handling, concurrency safety, and real-world
<abbr title="Application Programming Interface">API</abbr>/service design.

## Layout

```
GoEngineering/
  go.mod                        single module — every problem is a subpackage/subcommand
  NN_topic_slug/
    explanation/                the challenge — learner implements this
      *.go                      stubs + TODOs, compiles as-is (panics/zero-values)
    solution/                   the reference implementation
      *.go                      complete, idiomatic, heavily commented
      *_test.go                 table-driven tests, when the topic calls for them
```

Two directories instead of two files per topic because Go compiles per-package: a
`_explanation.go` and `_solution.go` sharing one package would collide on every type and
function name. Splitting into `explanation/` and `solution/` subpackages means each side
builds and runs completely independently — exactly what "must compile so you can iterate
immediately" requires.

## Workflow

1. Read `NN_topic_slug/explanation/*.go` top-to-bottom — the header comment states what
   you're building, why it matters, the spec, and acceptance criteria.
2. Implement every `// TODO:`. Run `go build ./...` and `go vet ./...` inside the folder
   as you go.
3. Compare against `NN_topic_slug/solution/*.go` — read the reasoning above each block,
   not just the code.
4. Run the tests where present: `go test ./NN_topic_slug/solution/...`.
5. Attempt the stretch goals listed at the bottom of the explanation file.

## Curriculum

| # | Problem | Core concepts |
|---|---|---|
| 01 | <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr> service | `net/http` 1.22+ routing, <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, validation, graceful shutdown |
| 02 | Middleware chain | `log/slog`, request IDs, panic recovery, timeouts, auth |
| 03 | <abbr title="Application Programming Interface">API</abbr> client with retries | Backoff, jitter, circuit breaker, context deadlines |
| 04 | Custom `io.Reader`/`io.Writer` | Streaming transforms, `io.Pipe`, backpressure |
| 05 | Large file line processor | `bufio.Scanner` limits, chunked reads, bounded memory |
| 06 | Atomic file store | Temp file + rename, fsync, permissions, crash safety |
| 07 | Filesystem walker | `io/fs`, `filepath.WalkDir`, `fstest` |
| 08 | Config loader | `embed`, env overrides, layered config, validation |
| 09 | Database repository layer | `database/sql`, pooling, prepared statements, scanning |
| 10 | Transactions & concurrency control | Isolation levels, optimistic locking, retryable serialization |
| 11 | Migrations & schema management | Versioned migrations, idempotency, rollback |
| 12 | Worker pool | Bounded concurrency, `errgroup`, cancellation |
| 13 | Pipeline | Fan-out/fan-in, channel ownership, leak-free shutdown |
| 14 | Concurrent cache | `sync.Map` vs mutex, single-flight, TTL eviction |
| 15 | Rate limiter | Token bucket, per-key limiting, vs `x/time/rate` |
| 16 | Pub/sub event bus | Subscriber lifecycle, slow-consumer handling, graceful close |
| 17 | Error taxonomy | Sentinel vs typed errors, `errors.Is/As/Join`, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> code mapping |
| 18 | Dependency injection & layering | Ports and adapters, wiring in `main` |
| 19 | Generic utilities | Type parameters, constraints, generic Result/Option, when generics hurt |
| 20 | Table-driven tests & fakes | `httptest`, golden files, fakes, subtests, parallel tests |
| 21 | Fuzzing & property testing | `testing.F`, invariants, seed corpora |
| 22 | Profiling & optimization | pprof, escape analysis, allocations, `sync.Pool`, honest benchmarks |
| 23 | Custom <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> & protobuf encoding | `MarshalJSON`, streaming encoders, schema evolution |
| 24 | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> service | Protobuf contract, interceptors, streaming, deadlines |
| 25 | Production service capstone | Health checks, metrics, structured logging, Dockerfile, <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr> |
| 26 | Advanced Concurrency Patterns | Context trees, `errgroup` patterns, `sync.Cond`, atomic pointers |
| 27 | CGO and Unsafe | Interfacing with C, `unsafe.Pointer`, memory layout, padding |
| 28 | Scheduler & <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> Tuning | `GOMAXPROCS`, `GOGC`, `GOMEMLIMIT`, preemption, stack growth |
| 29 | Compiler Directives & Build Tags | `//go:generate`, `//go:build`, conditional compilation, embedding |
| 30 | Reflect and Code Generation | `reflect` performance, <abbr title="Abstract Syntax Tree. A tree representation of the abstract syntactic structure of source code written in a programming language.">AST</abbr>-based tools, custom `go/analysis` linters |
| 31 | Deadlocks & Sync Primitives | Deadlock identification, starvation, `Mutex` vs `RWMutex`, `-race` |
| 32 | Context & Timeouts Deep Dive | Cascading timeouts, cancellation trees, debugging context leaks |
| 33 | Advanced Interfaces & Composition | Type switches, `var _ Interface = (*Struct)(nil)`, type embedding |
| 34 | Network Programming & Dialers | <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr>/<abbr title="User Datagram Protocol - A simple, connectionless communication protocol that allows for sending messages with minimal overhead but no delivery guarantees.">UDP</abbr> keep-alives, socket timeouts, custom <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> dialers |
| 35 | Profiling & Tracing | `runtime/trace`, execution tracer, scheduler latency, flame graphs |

A Python-parallel curriculum lives in `../PyEngineering`.
