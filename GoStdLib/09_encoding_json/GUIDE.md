# encoding/json — encoding and decoding <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>

`encoding/json` converts between Go values and <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> text. Reach for it for
any <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> wire format: <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> APIs, config files, message queues. It works
through struct tags and reflection, with escape hatches (`MarshalJSON`,
`json.Number`, streaming `Decoder`) for the cases where the default mapping
isn't good enough.

## When to reach for it vs alternatives already in this repo

- One-shot encode/decode of a value you already have fully in memory →
  `json.Marshal`/`json.Unmarshal`.
- Reading a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> file from disk → pair with `os.ReadFile` (see `../01_os`)
  then `json.Unmarshal`, or `os.Open` + `json.NewDecoder` for large files -
  see level 8.
- A <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> array too large to hold entirely in memory, or a stream that arrives
  incrementally (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> response body, growing log file) → `json.NewDecoder`
  and `Decoder.Token()`/`Decoder.Decode()` one element at a time - see level 7.
  This is the streaming equivalent of `bufio.Scanner` for <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>.
- Numbers that must stay exact (big integer IDs, monetary amounts) →
  `json.Number` via `Decoder.UseNumber()`, never decode into `any`/`float64`
  and hope for the best - see level 9.
- A type whose <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> shape doesn't match its Go shape (e.g. a custom string
  encoding for an enum, or cents stored as an int but written as a decimal
  string) → a `MarshalJSON`/`UnmarshalJSON` method - see level 5.

## Gotchas

| Gotcha | Detail |
|---|---|
| Decoding into `any`/`map[string]any` turns every <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> number into `float64` | A 64-bit integer ID like `9007199254740993` silently loses precision the moment it round-trips through a generic `map[string]any` - float64 only has 53 bits of integer precision. See level 9. |
| Unexported struct fields are invisible to `encoding/json` | Only exported (capitalized) fields are ever marshaled or unmarshaled - no error, they're just silently skipped. |
| `omitempty` treats the zero value as "empty", not "unset" | A struct field with `json:"count,omitempty"` and value `0` is omitted the same as if it were never set - you cannot distinguish "explicitly zero" from "absent" without a pointer or a wrapper type. |
| Unknown fields are ignored by default | `json.Unmarshal`/plain `Decoder.Decode` silently drop <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> fields with no matching struct field. `Decoder.DisallowUnknownFields()` turns that into a real error - useful for strict <abbr title="Application Programming Interface">API</abbr> validation. |
| A `MarshalJSON` method must be on the right receiver | Defining it on `*T` means only `*T` values marshal with it - a bare `T` (not a pointer) falls back to the default struct encoding, a common surprise when a slice holds `T` instead of `*T`. |
| Streaming decode of a top-level array still requires `Token()` bookkeeping | `Decoder.Decode` on a `[]T` still buffers the entire array in memory; true streaming means reading the opening `[` token, looping `Decode` for each element, then reading `]` - see level 7. |

## What the 10 levels cover

Levels 1-2 cover `Marshal`/`Unmarshal` on a simple struct and the struct-tag
surface (`json:"name,omitempty"`). Level 3 nests structs inside each other.
Level 4 triggers two real errors: a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> syntax error and a
`DisallowUnknownFields` rejection. Level 5 writes a custom
`MarshalJSON`/`UnmarshalJSON` pair. Level 6 measures decoding straight into a
typed struct against decoding into `map[string]any` first. Level 7 streams a
large <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> array token by token with `json.NewDecoder`, never holding the
whole array in memory. Level 8 is interop: reading/writing a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> config
file via `os.ReadFile`/`os.WriteFile`. Level 9 is the classic production
trap: decoding a big integer ID into `any` and watching it lose precision,
then fixing it with `json.Number`. Level 10 is a capstone record pipeline
combining struct tags, a custom type, streaming decode, and precision-safe
IDs.
