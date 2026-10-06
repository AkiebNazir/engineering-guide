/*
Problem 30 — Reflection & Code Generation (reflect.Type/Value, struct tags,
settability, go/ast, go/types, go/format, writing a linter)

WHAT WE'RE BUILDING

Two ways of writing code that works on types you haven't seen yet, side by
side, so you can choose between them with evidence:

Part A — reflection, at run time:
 1. Validate(v) — a struct-tag validator (`validate:"required,min=2,email"`)
    that recurses into nested structs, collects every failure with
    errors.Join, and caches the parsed rules per reflect.Type.
 2. SetField(ptr, field, value) — parse a string into any exported scalar
    field (config loaders, CLI flag binders, ORMs all do this), with
    correct handling of settability, unexported fields, integer overflow
    and time.Duration.
 3. ToMap(v) — read `json` tags (name, "-", omitempty) the way
    encoding/json does.

Part B — source code as data, at build time:
 4. GenerateStringer(src, typeName) — parse Go source, evaluate the enum's
    constant values with go/types, emit a gofmt-clean String() method. The
    committed level_string_gen.go in this directory was produced by it
    from level.go.
 5. CheckContextFirst(filename, src) — a small lint check using go/ast that
    flags functions taking context.Context anywhere but first.

WHY THIS MATTERS IN REAL SYSTEMS

Reflection is behind encoding/json, fmt, text/template, database/sql row
scanning, validator/v10, viper/mapstructure, gorm and most DI containers.
Code generation is behind protobuf/gRPC, stringer, mockgen, sqlc, ent,
wire, easyjson and oapi-codegen. Senior Go engineers are expected to:

  - read and debug reflective library code ("why is this field not being
    decoded?" → unexported field, or a tag typo);
  - know the cost — measured below, the reflective validator is ~29x
    slower than the handwritten one and allocates where it doesn't;
  - reach for generation when the types are known at build time, and write
    small AST-based tools and linters that enforce team conventions.

MENTAL MODEL 1 — AN INTERFACE VALUE IS (TYPE, VALUE)

Every reflect call starts from an interface value, which is two words:

    var x any = SignupRequest{...}

    x ──▶ ┌──────────────┬───────────────┐
          │ *type (itab) │ *data         │
          └──────┬───────┴──────┬────────┘
                 │              │
    reflect.TypeOf(x)     reflect.ValueOf(x)
                 ▼              ▼
          reflect.Type     reflect.Value
          (what it IS:     (the bits, plus flags:
          name, fields,    addressable? exported?
          methods, tags)   settable?)

The three laws of reflection (Rob Pike, "The Laws of Reflection"):
  - 1. Reflection goes from interface value to reflection object.
  - 2. Reflection goes from reflection object back to interface value
    (v.Interface()).
  - 3. To modify a reflection object, the value must be settable.

MENTAL MODEL 2 — KIND IS NOT TYPE

    type UserID int64
    type Level int
    time.Duration              // also an int64 underneath

    reflect.TypeOf(UserID(1)).Kind()         == reflect.Int64
    reflect.TypeOf(time.Second).Kind()       == reflect.Int64
    reflect.TypeOf(UserID(1)) == reflect.TypeOf(time.Second)   // false

Kind is the underlying representation (Int64, Struct, Pointer, Slice...);
Type is the named type. Switch on Kind to decide HOW to read or write the
bits; compare Types when a specific named type needs special handling —
SetField must check `fv.Type() == reflect.TypeFor[time.Duration]()` before
its `case reflect.Int64`, or "1m30s" gets parsed as an integer and fails.

MENTAL MODEL 3 — SETTABILITY AND ADDRESSABILITY

    s := ServerConfig{Host: "a"}

    reflect.ValueOf(s)               a COPY of s inside an interface
      .Field(0)                      not addressable
      .SetString("b")                PANIC: using unaddressable value

    reflect.ValueOf(&s)              a pointer
      .Elem()                        the struct s itself: addressable
      .Field(0)                      addressable + exported = CanSet()
      .SetString("b")                s.Host is now "b" ✓

      .FieldByName("secret")         addressable but unexported
      .CanSet() == false             reflect refuses (it would break
                                     package encapsulation)

    ┌───────────────────────────┬─────────────┬──────────┬─────────┐
    │ how you got the Value     │ addressable │ exported │ CanSet  │
    ├───────────────────────────┼─────────────┼──────────┼─────────┤
    │ ValueOf(s).Field(i)       │ no          │ yes      │ no      │
    │ ValueOf(&s).Elem().Field  │ yes         │ yes      │ YES     │
    │ ValueOf(&s).Elem().Field  │ yes         │ no       │ no      │
    │ slice element v.Index(i)  │ yes         │ n/a      │ yes     │
    │ map value v.MapIndex(k)   │ no          │ n/a      │ no      │
    └───────────────────────────┴─────────────┴──────────┴─────────┘

That is why json.Unmarshal takes a pointer, and why passing a struct by
value to a reflective decoder should be an error, not a silent no-op.

MENTAL MODEL 4 — WHERE REFLECTION'S COST COMES FROM

    direct code: s.Age < 13
        one compare on a known offset, often inlined, zero allocations

    reflect:     rv.Field(i).Int() < limit
        ├─ bounds/kind checks on every call (panics if wrong)
        ├─ tag string parsing (strings.Split, Cut, ParseFloat)
        ├─ no inlining through reflect's generic paths
        ├─ v.Interface() boxes non-pointer values → heap allocations
        └─ errors built with fmt.Sprintf

Measured on this machine (Apple M4 Pro, go1.26) for the SignupRequest in
the test file — a reflective Validate WITH a per-type cache vs the same
checks written by hand:

    BenchmarkValidateReflect       254.1 ns/op   136 B/op   5 allocs/op
    BenchmarkValidateHandwritten     8.6 ns/op     0 B/op   0 allocs/op
    BenchmarkToMapReflect          711.1 ns/op   760 B/op  10 allocs/op

~29x slower. That is fine for validating one HTTP request (0.25 µs next to
milliseconds of network and DB time) and wrong inside a loop over a million
rows.

Mitigations, in order of impact:
  - Parse struct tags ONCE PER TYPE and cache the plan keyed by
    reflect.Type (sync.Map). encoding/json does this.
  - Keep the per-value loop to Field(i) + Kind switch; avoid Interface().
  - For hot paths with known types, generate code instead.

MENTAL MODEL 5 — THE CODE GENERATION PIPELINE

    level.go (source bytes)
         │ go/parser.ParseFile
         ▼
    *ast.File ── syntax tree: GenDecl{Tok: CONST, Specs: [ValueSpec...]}
         │ go/types.Config.Check           (resolves names, evaluates
         ▼                                  iota, checks types)
    types.Info.Defs: ident ──▶ *types.Const{Type: Level, Val: -1}
         │ walk decls in source order, filter by named type,
         │ skip "_" and aliases with duplicate values
         ▼
    text/buffer with the String() method
         │ go/format.Source                (gofmt; also catches a
         ▼                                  generator bug as a syntax error)
    level_string_gen.go

What the AST for the enum looks like:

    GenDecl (Tok=CONST)
    ├── ValueSpec  Names=[LevelDebug]  Type=Ident(Level)  Values=[BinaryExpr(iota - 1)]
    ├── ValueSpec  Names=[LevelInfo]   Type=nil           Values=nil   ← implicit repeat
    ├── ValueSpec  Names=[LevelWarn]   ...
    ├── ValueSpec  Names=[_]           ...                             ← blank: skip
    └── ValueSpec  Names=[LevelFatal]  ...

Notice LevelInfo has NO type and NO value in the AST — Go repeats the
previous expression implicitly. Reading values from the AST alone would
require re-implementing constant evaluation; go/types does it correctly.

MENTAL MODEL 6 — LINTERS ARE AST WALKS

	ast.Inspect(file, func(n ast.Node) bool {
	    fd, ok := n.(*ast.FuncDecl)
	    if !ok { return true }             // keep descending
	    for _, field := range fd.Type.Params.List {
	        // `a, b int` is ONE field with TWO names: count names, not fields
	    }
	    return true
	})

The production framework is golang.org/x/tools/go/analysis: an Analyzer
declares Run(pass *analysis.Pass) and reports with pass.Reportf. The same
analyzer then runs under `go vet -vettool=...`, gopls (live in the editor),
golangci-lint, or as a standalone singlechecker binary — and the pass gives
you type information (pass.TypesInfo), so you can check "is this
parameter's type context.Context" instead of matching names like we do here.

REFLECTION OR GENERATION?

    | Question                                     | Reflection | Generation |
    |----------------------------------------------|------------|------------|
    | Types unknown until run time (plugins, any)  | ✓          |            |
    | Types known at build time                    |            | ✓          |
    | Hot path, allocation-sensitive               |            | ✓          |
    | Errors caught at compile time                |            | ✓          |
    | No extra build step / less tooling           | ✓          |            |
    | Readable, debuggable, greppable output       |            | ✓          |
    | Small API surface for library users          | ✓          |            |

Generics (Go 1.18+) remove a third category: code that is the same for every
type (containers, Map/Filter) needs neither.

SPEC

	var ErrNotStruct, ErrNotPointer error
	type FieldError struct { Field, Rule, Message string }   // Error() = Field + ": " + Message

	func Validate(v any) error
	    v: struct or pointer to struct (nil pointer → ErrNotStruct).
	    Rules: required | min=N | max=N | oneof=a|b | email.
	      min/max: length for string/slice/map/array, value for numbers.
	    Exported fields only; recurse into struct and non-nil *struct fields
	    (field path "Address.City"); time.Time is not recursed into.
	    Unknown rule or bad argument → a non-FieldError error.
	    Failures returned via errors.Join, in field order.

	func SetField(ptr any, field, value string) error
	    ptr must be a non-nil pointer to struct (else ErrNotPointer).
	    Kinds: string, bool, int*, uint* (use Type().Bits() for overflow),
	    float*, and the named type time.Duration (time.ParseDuration).

	func ToMap(v any) (map[string]any, error)
	    Keys from `json` tags (field name if absent), skip "-", honour
	    omitempty via IsZero, nested structs → nested maps.

	func GenerateStringer(src []byte, typeName string) ([]byte, error)
	    Header "// Code generated by reflectgen.GenerateStringer; DO NOT EDIT."
	    One case per distinct value in source order; default returns
	    "TypeName(" + strconv.FormatInt(int64(i), 10) + ")". gofmt-formatted.

	type Diagnostic struct { Pos, Func, Message string }
	func CheckContextFirst(filename string, src []byte) ([]Diagnostic, error)
	    Resolves the local name of the "context" import (aliases!), reports
	    FuncDecls whose context.Context parameter is not at position 0.
	    Methods are named "Recv.Method".

ACCEPTANCE CRITERIA

  - `go test -v ./30_reflect_and_code_generation/solution/...` passes.
  - Regenerating level_string_gen.go from level.go produces identical bytes.
  - Generated code for a second enum type-checks together with its input.
  - The benchmark reports reflect-based Validate vs a handwritten
    equivalent; the solution file documents the measured numbers.

HOW TO RUN

	go test -v ./30_reflect_and_code_generation/solution/...
	go test -run Example -v ./30_reflect_and_code_generation/solution/...
	go test -run '^$' -bench . -benchmem ./30_reflect_and_code_generation/solution/...
	REFLECTGEN_UPDATE=1 go test -run TestGeneratedLevelStringIsFresh ./30_reflect_and_code_generation/solution/

HINTS

  - Deref loop: for rv.Kind() == reflect.Pointer { if rv.IsNil() {...}; rv = rv.Elem() }.
  - reflect.StructField.IsExported(), Tag.Lookup("validate"), Tag.Get("json").
  - reflect.TypeFor[time.Duration]() (Go 1.22+) replaces
    reflect.TypeOf((*time.Duration)(nil)).Elem().
  - Value.IsZero works for every kind — use it for required and omitempty.
  - go/types: types.Info{Defs: map[*ast.Ident]types.Object{}}; each
    constant ident maps to a *types.Const with .Type() and .Val().
  - Compare constant values with c.Val().ExactString() to dedupe aliases.

COMMON PITFALLS

  - Calling v.Int() on a uint field, or v.Elem() on a non-pointer/interface
    → panic. Always switch on Kind first.
  - Forgetting that `a, b int` is a single *ast.Field with two Names.
  - Generating code with string concatenation and skipping go/format: the
    output is unreadable and a missing brace only shows up when a user
    compiles it.
  - Using fmt.Sprintf("%v") on constant values instead of go/types — breaks
    on iota expressions and implicit repetition.
  - Caching by type NAME instead of reflect.Type: two different packages
    can both have a type named Config.
  - Validation that silently ignores unknown tags — a typo disables it.

STRETCH GOALS

  - Add `dive` (validate each element of a slice of structs) to Validate.
  - Turn CheckContextFirst into a real go/analysis Analyzer and run it with
    `go vet -vettool=$(which ctxfirst) ./...`.
  - Extend GenerateStringer to emit a ParseLevel(string) (Level, error) and
    wire it to //go:generate via a small cmd/ program.
*/

package reflectgen

import "errors"

var (
	// ErrNotStruct is returned when a struct (or pointer to one) was expected.
	ErrNotStruct = errors.New("reflectgen: not a struct")
	// ErrNotPointer is returned when a non-nil pointer was required to modify a value.
	ErrNotPointer = errors.New("reflectgen: need a non-nil pointer to a struct")
)

// FieldError describes one failed validation rule.
type FieldError struct {
	Field   string
	Rule    string
	Message string
}

func (e *FieldError) Error() string { return e.Field + ": " + e.Message }

// ============================================================================
// Part A — reflection
// ============================================================================

// Validate checks `validate` struct tags on v. See SPEC.
func Validate(v any) error {
	// TODO: deref pointers; require a struct.
	// TODO: planFor(t reflect.Type) that parses tags once and caches in a sync.Map.
	// TODO: walk fields; check each rule; recurse into nested structs with "Parent." prefix.
	// TODO: return errors.Join(errs...).
	panic("not implemented")
}

// SetField parses value into the exported field of the struct ptr points to.
func SetField(ptr any, field, value string) error {
	// TODO: require non-nil pointer to struct; FieldByName; IsValid; CanSet.
	// TODO: check time.Duration by TYPE before switching on Kind.
	// TODO: ParseInt/ParseUint/ParseFloat with fv.Type().Bits().
	panic("not implemented")
}

// ToMap converts a struct into a map keyed by json tag names.
func ToMap(v any) (map[string]any, error) {
	// TODO: name, opts, _ := strings.Cut(f.Tag.Get("json"), ",")
	panic("not implemented")
}

// ============================================================================
// Part B — code generation and static analysis
// ============================================================================

// GenerateStringer returns a String() method for the constants of typeName in src.
func GenerateStringer(src []byte, typeName string) ([]byte, error) {
	// TODO: parser.ParseFile → types.Config{Importer: importer.Default()}.Check
	// TODO: walk GenDecl(CONST) → ValueSpec names → info.Defs[ident].(*types.Const)
	// TODO: filter by named type; skip "_" and duplicate values; build source; format.Source.
	panic("not implemented")
}

// Diagnostic is one finding reported by a lint check.
type Diagnostic struct {
	Pos     string
	Func    string
	Message string
}

func (d Diagnostic) String() string { return d.Pos + ": " + d.Message }

// CheckContextFirst reports functions whose context.Context parameter is not first.
func CheckContextFirst(filename string, src []byte) ([]Diagnostic, error) {
	// TODO: find the local name of the "context" import (alias-aware).
	// TODO: ast.Inspect FuncDecls; count parameter positions by NAMES; report pos != 0.
	panic("not implemented")
}
