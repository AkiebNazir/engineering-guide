// Package reflectgen is the reference solution for Problem 30 — Reflection
// and Code Generation. Part A uses reflect to build the kind of library
// encoding/json and go-playground/validator are made of; Part B uses go/ast,
// go/types and go/format to generate and lint code instead.
package reflectgen

import (
	"bytes"
	"errors"
	"fmt"
	"go/ast"
	"go/constant"
	"go/format"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"time"
)

// ============================================================================
// Part A — reflection
// ============================================================================

var (
	// ErrNotStruct is returned when a struct (or pointer to one) was expected.
	ErrNotStruct = errors.New("reflectgen: not a struct")
	// ErrNotPointer is returned when a non-nil pointer was required to modify a value.
	ErrNotPointer = errors.New("reflectgen: need a non-nil pointer to a struct")
)

// FieldError describes one failed validation rule.
type FieldError struct {
	Field   string // dotted path, e.g. "Address.City"
	Rule    string // e.g. "min"
	Message string
}

func (e *FieldError) Error() string { return e.Field + ": " + e.Message }

// ----------------------------------------------------------------------------
// A1. Validate — struct tags + a per-type rule cache
// ----------------------------------------------------------------------------

type rule struct{ name, arg string }

type fieldPlan struct {
	index  int
	name   string
	rules  []rule
	nested bool // struct or *struct field: recurse
}

// planCache maps reflect.Type → []fieldPlan. reflect.Type values are
// comparable and canonical (one per type), so they are perfect map keys.
// Parsing tags is the expensive, allocation-heavy part; doing it once per
// TYPE instead of once per VALUE is what makes reflective libraries
// usable on hot paths. encoding/json keeps exactly this kind of cache.
var planCache sync.Map

func planFor(t reflect.Type) ([]fieldPlan, error) {
	if p, ok := planCache.Load(t); ok {
		return p.([]fieldPlan), nil
	}
	plans := make([]fieldPlan, 0, t.NumField())
	for i := range t.NumField() {
		f := t.Field(i)
		if !f.IsExported() {
			continue // reflect can read but never set unexported fields; validators skip them
		}
		fp := fieldPlan{index: i, name: f.Name}
		ft := f.Type
		if ft.Kind() == reflect.Pointer {
			ft = ft.Elem()
		}
		fp.nested = ft.Kind() == reflect.Struct && ft != reflect.TypeFor[time.Time]()

		if tag, ok := f.Tag.Lookup("validate"); ok && tag != "" {
			for _, part := range strings.Split(tag, ",") {
				name, arg, _ := strings.Cut(strings.TrimSpace(part), "=")
				switch name {
				case "required", "email":
				case "min", "max":
					if _, err := strconv.ParseFloat(arg, 64); err != nil {
						return nil, fmt.Errorf("reflectgen: %s.%s: bad %s argument %q", t.Name(), f.Name, name, arg)
					}
				case "oneof":
					if arg == "" {
						return nil, fmt.Errorf("reflectgen: %s.%s: oneof needs values", t.Name(), f.Name)
					}
				default:
					// A typo'd tag is a programmer error; failing loudly beats
					// silently not validating.
					return nil, fmt.Errorf("reflectgen: %s.%s: unknown rule %q", t.Name(), f.Name, name)
				}
				fp.rules = append(fp.rules, rule{name, arg})
			}
		}
		if len(fp.rules) > 0 || fp.nested {
			plans = append(plans, fp)
		}
	}
	// LoadOrStore: if two goroutines race to build the plan, both get the
	// same stored slice.
	actual, _ := planCache.LoadOrStore(t, plans)
	return actual.([]fieldPlan), nil
}

// Validate checks `validate:"..."` struct tags on v (a struct or pointer to
// struct), recursing into nested struct fields. Supported rules: required,
// min=N, max=N (length for strings/slices/maps, value for numbers),
// oneof=a|b|c (strings), email. All failures are returned via errors.Join as
// *FieldError values.
//
// Measured cost on a valid SignupRequest (Apple M4 Pro, go1.26,
// `go test -bench . -benchmem`), even WITH the per-type plan cache:
//
//	BenchmarkValidateReflect       254.1 ns/op   136 B/op   5 allocs/op
//	BenchmarkValidateHandwritten     8.6 ns/op     0 B/op   0 allocs/op
//
// ~29x slower. A memory profile (-memprofile, pprof -sample_index=alloc_objects)
// attributes the allocations to building field-path strings in validateStruct
// (53%) and strings.Split for oneof in check (46%). Both could move into the
// cached plan — the next optimisation a real library would make.
func Validate(v any) error {
	rv := reflect.ValueOf(v)
	for rv.Kind() == reflect.Pointer {
		if rv.IsNil() {
			return ErrNotStruct
		}
		rv = rv.Elem()
	}
	if rv.Kind() != reflect.Struct {
		return fmt.Errorf("%w: got %s", ErrNotStruct, rv.Kind())
	}
	var errs []error
	if err := validateStruct(rv, "", &errs); err != nil {
		return err
	}
	return errors.Join(errs...)
}

func validateStruct(rv reflect.Value, prefix string, errs *[]error) error {
	plans, err := planFor(rv.Type())
	if err != nil {
		return err
	}
	for _, p := range plans {
		fv := rv.Field(p.index)
		path := prefix + p.name

		for _, r := range p.rules {
			if msg := check(fv, r); msg != "" {
				*errs = append(*errs, &FieldError{Field: path, Rule: r.name, Message: msg})
			}
		}

		if p.nested {
			if fv.Kind() == reflect.Pointer {
				if fv.IsNil() {
					continue // `required` above already reported it if needed
				}
				fv = fv.Elem()
			}
			if err := validateStruct(fv, path+".", errs); err != nil {
				return err
			}
		}
	}
	return nil
}

// check returns "" when fv satisfies r, otherwise a human-readable message.
func check(fv reflect.Value, r rule) string {
	switch r.name {
	case "required":
		// IsZero is correct for every kind: "", 0, nil pointer/slice/map,
		// zero struct. (Note: an empty but non-nil slice is NOT zero.)
		if fv.IsZero() {
			return "is required"
		}
	case "min", "max":
		limit, _ := strconv.ParseFloat(r.arg, 64) // validated in planFor
		var got float64
		var what string
		switch fv.Kind() {
		case reflect.String:
			// len counts BYTES. For user-facing limits on names you may want
			// utf8.RuneCountInString instead — a deliberate choice to make.
			got, what = float64(fv.Len()), "length"
		case reflect.Slice, reflect.Map, reflect.Array:
			got, what = float64(fv.Len()), "length"
		case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
			got, what = float64(fv.Int()), "value"
		case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
			got, what = float64(fv.Uint()), "value"
		case reflect.Float32, reflect.Float64:
			got, what = fv.Float(), "value"
		default:
			return fmt.Sprintf("rule %s not supported on %s", r.name, fv.Kind())
		}
		if r.name == "min" && got < limit {
			return fmt.Sprintf("%s %v is less than %s", what, got, r.arg)
		}
		if r.name == "max" && got > limit {
			return fmt.Sprintf("%s %v is greater than %s", what, got, r.arg)
		}
	case "oneof":
		if fv.Kind() != reflect.String {
			return "oneof requires a string"
		}
		for _, opt := range strings.Split(r.arg, "|") {
			if fv.String() == opt {
				return ""
			}
		}
		return fmt.Sprintf("%q is not one of %s", fv.String(), r.arg)
	case "email":
		if fv.Kind() != reflect.String {
			return "email requires a string"
		}
		s := fv.String()
		at := strings.LastIndexByte(s, '@')
		if at < 1 || !strings.Contains(s[at+1:], ".") {
			return fmt.Sprintf("%q is not an email address", s)
		}
	}
	return ""
}

// ----------------------------------------------------------------------------
// A2. SetField — the third law of reflection: to modify, it must be settable
// ----------------------------------------------------------------------------

// SetField parses value and stores it into the exported field `field` of the
// struct that ptr points to. Supports string, bool, ints (with overflow
// detection), uints, floats and time.Duration.
func SetField(ptr any, field, value string) error {
	rv := reflect.ValueOf(ptr)
	// reflect.ValueOf(s) on a struct VALUE holds a copy; modifying it could
	// never affect the caller's variable, so reflect makes it unaddressable
	// and any Set panics. Requiring a pointer is the only correct API.
	if rv.Kind() != reflect.Pointer || rv.IsNil() || rv.Elem().Kind() != reflect.Struct {
		return ErrNotPointer
	}
	fv := rv.Elem().FieldByName(field)
	if !fv.IsValid() {
		return fmt.Errorf("reflectgen: no field %q", field)
	}
	if !fv.CanSet() {
		// Exported fields of an addressable struct are settable; unexported
		// ones never are, even through a pointer.
		return fmt.Errorf("reflectgen: field %q is unexported and cannot be set", field)
	}

	// Check the named type BEFORE the kind: time.Duration's Kind is Int64.
	if fv.Type() == reflect.TypeFor[time.Duration]() {
		d, err := time.ParseDuration(value)
		if err != nil {
			return fmt.Errorf("reflectgen: %s: %w", field, err)
		}
		fv.SetInt(int64(d))
		return nil
	}

	switch fv.Kind() {
	case reflect.String:
		fv.SetString(value)
	case reflect.Bool:
		b, err := strconv.ParseBool(value)
		if err != nil {
			return fmt.Errorf("reflectgen: %s: %w", field, err)
		}
		fv.SetBool(b)
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		// Parse with the field's real bit size so "300" into an int8 is an
		// error instead of silently wrapping to 44.
		n, err := strconv.ParseInt(value, 10, fv.Type().Bits())
		if err != nil {
			return fmt.Errorf("reflectgen: %s: %w", field, err)
		}
		fv.SetInt(n)
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		n, err := strconv.ParseUint(value, 10, fv.Type().Bits())
		if err != nil {
			return fmt.Errorf("reflectgen: %s: %w", field, err)
		}
		fv.SetUint(n)
	case reflect.Float32, reflect.Float64:
		f, err := strconv.ParseFloat(value, fv.Type().Bits())
		if err != nil {
			return fmt.Errorf("reflectgen: %s: %w", field, err)
		}
		fv.SetFloat(f)
	default:
		return fmt.Errorf("reflectgen: %s: unsupported kind %s", field, fv.Kind())
	}
	return nil
}

// ----------------------------------------------------------------------------
// A3. ToMap — reading tags the way encoding/json does
// ----------------------------------------------------------------------------

// ToMap converts a struct (or pointer to struct) into a map keyed by `json`
// tag names. Honours `json:"-"` and `,omitempty`; nested structs become
// nested maps; unexported fields are skipped.
func ToMap(v any) (map[string]any, error) {
	rv := reflect.ValueOf(v)
	for rv.Kind() == reflect.Pointer {
		if rv.IsNil() {
			return nil, ErrNotStruct
		}
		rv = rv.Elem()
	}
	if rv.Kind() != reflect.Struct {
		return nil, ErrNotStruct
	}
	return toMap(rv), nil
}

func toMap(rv reflect.Value) map[string]any {
	t := rv.Type()
	out := make(map[string]any, t.NumField())
	for i := range t.NumField() {
		f := t.Field(i)
		if !f.IsExported() {
			continue
		}
		name, opts, _ := strings.Cut(f.Tag.Get("json"), ",")
		if name == "-" {
			continue
		}
		if name == "" {
			name = f.Name
		}
		fv := rv.Field(i)
		if strings.Contains(opts, "omitempty") && fv.IsZero() {
			continue
		}
		if fv.Kind() == reflect.Pointer && !fv.IsNil() && fv.Elem().Kind() == reflect.Struct {
			fv = fv.Elem()
		}
		if fv.Kind() == reflect.Struct && fv.Type() != reflect.TypeFor[time.Time]() {
			out[name] = toMap(fv)
			continue
		}
		// Interface() boxes the value into an `any` — typically one heap
		// allocation per non-pointer field. This is a big part of why
		// reflection-based encoders allocate so much.
		out[name] = fv.Interface()
	}
	return out
}

// ============================================================================
// Part B — code generation and static analysis with go/ast
// ============================================================================

// GenerateStringer parses Go source src, finds every constant whose type is
// the named type typeName, and returns gofmt-formatted source for a
// `func (i typeName) String() string` method.
//
// Constant VALUES come from go/types, not from reading the AST: `iota - 1`,
// `1 << iota`, skipped `_` lines and aliases like `LevelDefault = LevelInfo`
// all require actually evaluating the constant expressions, which is exactly
// what the type checker does.
func GenerateStringer(src []byte, typeName string) ([]byte, error) {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "input.go", src, parser.SkipObjectResolution)
	if err != nil {
		return nil, fmt.Errorf("reflectgen: parse: %w", err)
	}

	info := &types.Info{Defs: map[*ast.Ident]types.Object{}}
	conf := types.Config{Importer: importer.Default()}
	if _, err := conf.Check(file.Name.Name, fset, []*ast.File{file}, info); err != nil {
		return nil, fmt.Errorf("reflectgen: type-check: %w", err)
	}

	type entry struct {
		name  string
		value constant.Value
	}
	var entries []entry
	seen := map[string]bool{} // constant.Value's exact string form → already emitted

	// Walk declarations in SOURCE order so the switch reads like the enum.
	for _, decl := range file.Decls {
		gd, ok := decl.(*ast.GenDecl)
		if !ok || gd.Tok != token.CONST {
			continue
		}
		for _, spec := range gd.Specs {
			for _, ident := range spec.(*ast.ValueSpec).Names {
				if ident.Name == "_" {
					continue
				}
				c, ok := info.Defs[ident].(*types.Const)
				if !ok {
					continue
				}
				named, ok := c.Type().(*types.Named)
				if !ok || named.Obj().Name() != typeName {
					continue
				}
				key := c.Val().ExactString()
				if seen[key] {
					continue // alias of an earlier constant: a duplicate case wouldn't compile
				}
				seen[key] = true
				entries = append(entries, entry{ident.Name, c.Val()})
			}
		}
	}
	if len(entries) == 0 {
		return nil, fmt.Errorf("reflectgen: no constants of type %s", typeName)
	}

	var buf bytes.Buffer
	fmt.Fprintf(&buf, "// Code generated by reflectgen.GenerateStringer; DO NOT EDIT.\n\n")
	fmt.Fprintf(&buf, "package %s\n\nimport \"strconv\"\n\n", file.Name.Name)
	fmt.Fprintf(&buf, "func (i %s) String() string {\n\tswitch i {\n", typeName)
	for _, e := range entries {
		fmt.Fprintf(&buf, "\tcase %s:\n\t\treturn %q\n", e.name, e.name)
	}
	fmt.Fprintf(&buf, "\tdefault:\n\t\treturn %q + strconv.FormatInt(int64(i), 10) + \")\"\n\t}\n}\n", typeName+"(")

	out, err := format.Source(buf.Bytes())
	if err != nil {
		return nil, fmt.Errorf("reflectgen: generated invalid Go (bug): %w\n%s", err, buf.Bytes())
	}
	return out, nil
}

// Diagnostic is one finding reported by a lint check.
type Diagnostic struct {
	Pos     string // file:line:col
	Func    string
	Message string
}

func (d Diagnostic) String() string { return d.Pos + ": " + d.Message }

// CheckContextFirst reports functions and methods that accept a
// context.Context anywhere other than as their first parameter — the
// convention every Go codebase (and the context package docs) follows.
//
// This is a purely syntactic check: it resolves the local name of the
// "context" import (handling aliases like `import stdctx "context"`), then
// matches parameter types of the form <localName>.Context. A production
// linter would use go/analysis with type information to also catch named
// types that embed context.Context; the AST walk is the same.
func CheckContextFirst(filename string, src []byte) ([]Diagnostic, error) {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, filename, src, parser.SkipObjectResolution)
	if err != nil {
		return nil, err
	}

	ctxName := ""
	for _, imp := range file.Imports {
		if path, _ := strconv.Unquote(imp.Path.Value); path == "context" {
			ctxName = "context"
			if imp.Name != nil {
				ctxName = imp.Name.Name
			}
		}
	}
	if ctxName == "" || ctxName == "_" {
		return nil, nil // file can't mention context.Context
	}

	isCtx := func(e ast.Expr) bool {
		sel, ok := e.(*ast.SelectorExpr)
		if !ok || sel.Sel.Name != "Context" {
			return false
		}
		x, ok := sel.X.(*ast.Ident)
		return ok && x.Name == ctxName
	}

	var diags []Diagnostic
	ast.Inspect(file, func(n ast.Node) bool {
		fd, ok := n.(*ast.FuncDecl)
		if !ok || fd.Type.Params == nil {
			return true
		}
		pos := 0 // parameter position; `a, b int` is ONE field with two names
		for _, field := range fd.Type.Params.List {
			width := max(len(field.Names), 1)
			if isCtx(field.Type) && pos != 0 {
				name := fd.Name.Name
				if fd.Recv != nil && len(fd.Recv.List) > 0 {
					name = receiverName(fd.Recv.List[0].Type) + "." + name
				}
				diags = append(diags, Diagnostic{
					Pos:     fset.Position(field.Pos()).String(),
					Func:    name,
					Message: fmt.Sprintf("%s: context.Context should be the first parameter (found at position %d)", name, pos),
				})
			}
			pos += width
		}
		return true
	})
	return diags, nil
}

func receiverName(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.StarExpr:
		return receiverName(t.X)
	case *ast.Ident:
		return t.Name
	case *ast.IndexExpr: // generic receiver T[K]
		return receiverName(t.X)
	case *ast.IndexListExpr: // generic receiver T[K, V]
		return receiverName(t.X)
	}
	return "?"
}
