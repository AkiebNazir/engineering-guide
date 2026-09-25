# Best Practices — Overview

System design is not just boxes-and-arrows scale/<abbr title="CAP Theorem - A concept stating that a distributed data store can only simultaneously provide two out of three guarantees: Consistency, Availability, and Partition tolerance.">CAP</abbr> thinking. Every box in a `building_blocks/` diagram is implemented by code, and how that code is structured — its coupling, its testability, its blast radius when requirements change — determines whether the architecture survives six months of real feature work. Senior+ interviews and real design reviews both probe this: it is not enough to draw a correct system; you have to defend the object- and module-level design inside each service too.

## How to use this module

Read [01 — Design principles](01_design_principles.md) first. Every other file in this module refers back to it — <abbr title="Five core design principles intended to make software designs more understandable, flexible, and maintainable (Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion).">SOLID</abbr> and the surrounding principles are the vocabulary the rest of the module assumes you have. After that, the files are largely independent; read in order if you want the natural progression from object-level to system-level to team-practice, or jump to whichever file matches the gap you're closing.

## Reading order

| File | Covers |
|---|---|
| [01 — Design principles](01_design_principles.md) | <abbr title="Five core design principles intended to make software designs more understandable, flexible, and maintainable (Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion).">SOLID</abbr> in full (rule, before/after example, concrete failure prevented) plus <abbr title="Don't Repeat Yourself - A software development principle aimed at reducing repetition of software patterns, replacing it with abstractions.">DRY</abbr>, <abbr title="Keep It Simple, Stupid - A design principle noting that most systems work best if they are kept simple rather than made complicated.">KISS</abbr>, <abbr title="You Aren't Gonna Need It - A principle of extreme programming that states a programmer should not add functionality until deemed necessary.">YAGNI</abbr>, separation of concerns, Law of Demeter, composition over inheritance, encapsulation, Postel's law, and more. |
| [02 — Creational patterns](02_design_patterns_creational.md) | Singleton, Factory Method, Abstract Factory, Builder, Prototype — problem solved, example, and when each is over-engineering. |
| [03 — Structural patterns](03_design_patterns_structural.md) | Adapter, Decorator, Facade, Proxy (virtual/remote/protection/caching), Composite, Bridge, Flyweight. |
| [04 — Behavioral patterns](04_design_patterns_behavioral.md) | Strategy, Observer, Command, State, Template Method, Chain of Responsibility, Iterator, Mediator, Memento, Visitor. |
| [05 — Architectural patterns](05_architectural_patterns.md) | Layered, hexagonal, clean architecture, MVC/MVVM, monolith vs. microservices, event-driven architecture, CQRS, event sourcing, DDD basics. |
| [06 — Code quality and practices](06_code_quality_and_practices.md) | Testing pyramid, <abbr title="Test-Driven Development. A software development process relying on software requirements being converted to test cases before software is fully developed.">TDD</abbr>, code review, refactoring discipline, technical debt, naming/function-size heuristics, 12-factor essentials, semver. |
| [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md) | God object, spaghetti code, anemic domain model, premature optimization, magic numbers, shotgun surgery, feature envy, big ball of mud, cargo-cult pattern overuse, tight coupling. |

## Related

- `../building_blocks/00_overview.md` — the system-level counterpart: what components exist and when they earn their place.
- `../README.md` — the full curriculum this module sits in.
