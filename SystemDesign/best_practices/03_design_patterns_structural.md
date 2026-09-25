# Design Patterns — Structural

Structural patterns compose classes/objects into larger structures while keeping the pieces independently replaceable. Each entry: problem solved → short example → when it's overkill.

## Adapter

**Problem solved:** make an existing class's interface compatible with what a caller expects, without modifying either side — typically to integrate a third-party or legacy class.

```python
class LegacyXmlLogger:
    def log_xml(self, xml_str: str): ...

class Logger(Protocol):
    def log(self, message: str) -> None: ...

class XmlLoggerAdapter(Logger):
    def __init__(self, legacy: LegacyXmlLogger):
        self._legacy = legacy
    def log(self, message: str) -> None:
        self._legacy.log_xml(f"<msg>{message}</msg>")
```

**When it's overkill:** if you control both sides of the interface, just change one of them to match — don't add an adapter layer to paper over a mismatch you're free to fix at the source.

## Decorator

**Problem solved:** attach additional behavior to an object dynamically, without subclassing every combination of behaviors (avoids combinatorial subclass explosion: `LoggingCachingRetryingClient`, `CachingClient`, `RetryingClient`, ...).

```python
class DataSource(Protocol):
    def read(self) -> str: ...

class CachingDecorator(DataSource):
    def __init__(self, wrapped: DataSource):
        self._wrapped = wrapped
        self._cache = None
    def read(self) -> str:
        if self._cache is None:
            self._cache = self._wrapped.read()
        return self._cache

source = CachingDecorator(LoggingDecorator(FileDataSource("data.txt")))
```

**When it's overkill:** stacking more than two or three decorators makes call-stack debugging painful (which layer produced this value?) — past that, a single configurable class or a middleware pipeline (see Chain of Responsibility, [04](04_design_patterns_behavioral.md)) is often clearer.

## Facade

**Problem solved:** provide one simple, higher-level interface over a complex subsystem so most callers don't need to learn every part of it.

```python
class VideoConversionFacade:
    def convert(self, path: str, target_format: str) -> str:
        codec = CodecFactory.for_format(target_format)
        raw = FFmpegDecoder().decode(path)
        return codec.encode(raw)
```

**When it's overkill:** if callers legitimately need the subsystem's full flexibility, a facade that only covers the 80% case forces power users to bypass it anyway — now you maintain two entry points into the same subsystem.

## Proxy

**Problem solved:** control access to an object by standing in for it, adding a concern (lazy loading, remote access, permission checks, caching) without changing the real object's code.

| Variant | Purpose | Example |
|---|---|---|
| Virtual proxy | Defer expensive construction until first use. | Lazy-load a large image only when it's actually rendered. |
| Remote proxy | Represent an object living in another process/machine. | <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> client stub standing in for the remote service. |
| Protection proxy | Enforce access control before delegating. | Wrapper that checks permissions before calling the real file handle. |
| Caching proxy | Serve repeated calls from a cache instead of the real object. | <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> caching reverse proxy in front of an origin service. |

```python
class ProtectionProxy(FileHandle):
    def __init__(self, real: FileHandle, user):
        self._real, self._user = real, user
    def read(self):
        if not self._user.can_read():
            raise PermissionError
        return self._real.read()
```

**When it's overkill:** if there's no cross-cutting concern to add (no lazy-load, no remote boundary, no access check, no cache), a proxy is an indirection layer that just forwards calls — delete it.

## Composite

**Problem solved:** treat individual objects and groups of objects uniformly through a shared interface, so client code doesn't need to special-case "is this a leaf or a group" (typical for tree structures: file systems, UI component trees, org charts).

```python
class FileSystemNode(Protocol):
    def size(self) -> int: ...

class File(FileSystemNode):
    def size(self): return self._bytes

class Directory(FileSystemNode):
    def size(self):
        return sum(child.size() for child in self._children)
```

**When it's overkill:** if the structure is never actually recursive/nested (a flat list is enough), Composite adds tree-traversal machinery for a shape you don't have.

## Bridge

**Problem solved:** decouple an abstraction from its implementation so the two can vary independently, avoiding an `M × N` subclass explosion (e.g., `Shape` × `RenderingEngine`).

```python
class Renderer(Protocol):
    def render_circle(self, x, y, r): ...

class Circle:
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
    def draw(self, x, y, r):
        self._renderer.render_circle(x, y, r)

# VectorRenderer and RasterRenderer vary independently of Circle, Square, etc.
```

**When it's overkill:** if you only ever have one implementation dimension (one renderer, ever), you don't need to decouple two axes that don't both vary — a plain interface is enough.

## Flyweight

**Problem solved:** share the immutable part of many fine-grained objects to cut memory use, when a program needs to instantiate huge numbers of similar objects (glyphs in a text editor, particles in a game).

```python
class GlyphFlyweight:
    _pool = {}
    @classmethod
    def get(cls, char: str, font: str):
        key = (char, font)
        if key not in cls._pool:
            cls._pool[key] = cls(char, font)  # shared, immutable
        return cls._pool[key]
```

Extrinsic (position on screen) state stays outside the flyweight; intrinsic (glyph shape) state is shared.

**When it's overkill:** without a real, measured memory problem from object count, Flyweight adds a shared-state cache and the bug class that comes with it (accidentally mutating shared intrinsic state) for no measured benefit — don't add it speculatively.

## Related

- [02 — Creational patterns](02_design_patterns_creational.md)
- [04 — Behavioral patterns](04_design_patterns_behavioral.md) — Chain of Responsibility often replaces deep Decorator stacks for pipeline-shaped problems.
- [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md) — cargo-cult pattern overuse.
