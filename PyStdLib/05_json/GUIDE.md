# json — Encoding and Decoding JSON

`json` converts Python values to/from the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> text format: `dict`<->object,
`list`/`tuple`<->array, `str`<->string, `int`/`float`<->number, `True`/`False`/`None`
<->`true`/`false`/`null`. It is the default choice for config files, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> payloads,
and any structured data you want humans to be able to read and diff.

## When to reach for `json` vs alternatives in this repo

- Need schema validation, type coercion, or nested model objects, not just
  dict-in/dict-out -> see `PyEngineering/32_pydantic_v2_deep_dive` (Pydantic
  builds on top of exactly this module for its own <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> mode).
- Need tabular, spreadsheet-shaped data -> see `PyStdLib/06_csv` — smaller
  files, opens in Excel, but no nested structure.
- Need a config file a human hand-edits with comments -> `tomllib` (see
  `PyEngineering/08_config_loader`) reads TOML, which allows comments; <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> does not.
- Need to encode/decode straight from a byte stream over a socket or a file
  you don't want to hold fully as a string first -> combine this module with
  `PyStdLib/04_io` (level 8 here does exactly that with `io.StringIO`).
- Need binary-efficient serialization (not human-readable) -> stdlib `pickle`
  or a schema format like protobuf (see `PyEngineering/23_custom_json_protobuf_encoding`)
  are the real alternatives; `json` is deliberately text-only.

## Gotchas

| Gotcha | Detail |
|---|---|
| Duplicate keys: last one wins | `{"a": 1, "a": 2}` silently decodes to `{"a": 2}` — the first value is gone, no warning. |
| `NaN`/`Infinity` are non-standard | Python's `json` accepts and emits `NaN`, `Infinity`, `-Infinity` by default — valid Python, **invalid** strict <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> per RFC 8259. |
| `default=` is one-way | It lets `dumps()` encode a custom object, but `loads()` won't reconstruct it automatically — you need `object_hook` on the way back. |
| Dict key order in output | Since Python 3.7 dicts preserve insertion order and `json.dumps` respects it unless `sort_keys=True` is passed. |
| Non-string dict keys get stringified | `{1: "a"}` dumps to `{"1": "a"}` — the round trip through `loads()` gives you back a `str` key, not `int`. |
| `ensure_ascii` default is `True` | Every non-ASCII character is escaped as `\uXXXX` unless you pass `ensure_ascii=False` — correct but hard to read. |

## What the 10 levels cover

Level 1 is the `dumps()`/`loads()` round trip. Level 2 covers `dump()`/`load()`
against real files, `indent=`, `sort_keys=`, and `ensure_ascii=False`. Level 3
combines those into a small config-file idiom. Level 4 triggers a real
`JSONDecodeError` on malformed input and inspects `.lineno`/`.colno`/`.pos`.
Level 5 covers `default=` for encoding custom objects (a `datetime`) and
`object_hook` for decoding them back. Level 6 measures `indent=` vs compact
`separators=(",", ":")` output size and dump time with `time.perf_counter()`.
Level 7 covers a lifecycle concern: writing a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> file atomically so a crash
mid-write can't leave a half-written, corrupt file. Level 8 pairs `json` with
`io.StringIO` for in-memory encode/decode. Level 9 demonstrates the
duplicate-key and `NaN`/`Infinity` gotchas actually misbehaving, then the
fixes (`object_pairs_hook`, `allow_nan=False`). Level 10 is a capstone config
store combining most of the above.
