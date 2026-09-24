package reflectgen

import (
	"bytes"
	"errors"
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

// ----------------------------------------------------------------------------
// Fixtures
// ----------------------------------------------------------------------------

type Address struct {
	City    string `validate:"required" json:"city"`
	Country string `validate:"required,oneof=IN|US|DE" json:"country"`
}

type SignupRequest struct {
	Name     string   `validate:"required,min=2,max=32" json:"name"`
	Email    string   `validate:"required,email" json:"email"`
	Age      int      `validate:"min=13,max=130" json:"age"`
	Plan     string   `validate:"oneof=free|pro|team" json:"plan,omitempty"`
	Tags     []string `validate:"max=3" json:"tags,omitempty"`
	Address  *Address `validate:"required" json:"address"`
	Password string   `json:"-"`
	internal string   //nolint:unused // proves unexported fields are skipped
}

func validSignup() SignupRequest {
	return SignupRequest{
		Name: "Ada", Email: "ada@example.com", Age: 36, Plan: "pro",
		Address: &Address{City: "Pune", Country: "IN"}, Password: "hunter2",
	}
}

// ----------------------------------------------------------------------------
// Validate
// ----------------------------------------------------------------------------

func TestValidateAcceptsValidInput(t *testing.T) {
	s := validSignup()
	if err := Validate(s); err != nil {
		t.Fatalf("value: %v", err)
	}
	if err := Validate(&s); err != nil {
		t.Fatalf("pointer: %v", err)
	}
}

func TestValidateReportsEveryFailure(t *testing.T) {
	bad := SignupRequest{
		Name:    "A",                          // min=2
		Email:   "not-an-email",               // email
		Age:     7,                            // min=13
		Plan:    "enterprise",                 // oneof
		Tags:    []string{"a", "b", "c", "d"}, // max=3
		Address: &Address{City: "", Country: "FR"},
	}
	err := Validate(bad)
	if err == nil {
		t.Fatal("expected errors")
	}

	var got []string
	for _, e := range err.(interface{ Unwrap() []error }).Unwrap() {
		var fe *FieldError
		if !errors.As(e, &fe) {
			t.Fatalf("non-FieldError in result: %v", e)
		}
		got = append(got, fe.Field+"/"+fe.Rule)
	}
	want := []string{"Name/min", "Email/email", "Age/min", "Plan/oneof", "Tags/max",
		"Address.City/required", "Address.Country/oneof"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("failures:\n got %v\nwant %v", got, want)
	}
	t.Logf("errors.Join output:\n%v", err)
}

func TestValidateNilNestedPointerIsRequired(t *testing.T) {
	s := validSignup()
	s.Address = nil
	err := Validate(s)
	var fe *FieldError
	if !errors.As(err, &fe) || fe.Field != "Address" || fe.Rule != "required" {
		t.Fatalf("got %v", err)
	}
}

func TestValidateRejectsNonStructsAndBadTags(t *testing.T) {
	if err := Validate(42); !errors.Is(err, ErrNotStruct) {
		t.Fatalf("Validate(42) = %v", err)
	}
	if err := Validate((*SignupRequest)(nil)); !errors.Is(err, ErrNotStruct) {
		t.Fatalf("nil pointer = %v", err)
	}
	type typo struct {
		N int `validate:"mni=3"`
	}
	if err := Validate(typo{}); err == nil || !strings.Contains(err.Error(), "unknown rule") {
		t.Fatalf("typo'd tag should fail loudly, got %v", err)
	}
}

// ----------------------------------------------------------------------------
// SetField
// ----------------------------------------------------------------------------

type ServerConfig struct {
	Host    string
	Port    uint16
	Retries int8
	Debug   bool
	Ratio   float64
	Timeout time.Duration
	secret  string
}

func TestSetField(t *testing.T) {
	var c ServerConfig
	steps := []struct{ field, value string }{
		{"Host", "0.0.0.0"}, {"Port", "8443"}, {"Retries", "-3"},
		{"Debug", "true"}, {"Ratio", "0.25"}, {"Timeout", "1m30s"},
	}
	for _, s := range steps {
		if err := SetField(&c, s.field, s.value); err != nil {
			t.Fatalf("SetField(%s=%s): %v", s.field, s.value, err)
		}
	}
	want := ServerConfig{Host: "0.0.0.0", Port: 8443, Retries: -3, Debug: true, Ratio: 0.25, Timeout: 90 * time.Second}
	if c != want {
		t.Fatalf("got %+v\nwant %+v", c, want)
	}

	errCases := []struct {
		name  string
		ptr   any
		field string
		value string
		want  string
	}{
		{"struct by value", c, "Host", "x", "non-nil pointer"},
		{"unknown field", &c, "Nope", "x", "no field"},
		{"unexported field", &c, "secret", "x", "unexported"},
		{"int8 overflow", &c, "Retries", "300", "out of range"},
		{"uint16 overflow", &c, "Port", "70000", "out of range"},
		{"bad duration", &c, "Timeout", "soon", "invalid duration"},
	}
	for _, ec := range errCases {
		t.Run(ec.name, func(t *testing.T) {
			err := SetField(ec.ptr, ec.field, ec.value)
			if err == nil || !strings.Contains(err.Error(), ec.want) {
				t.Fatalf("err = %v, want containing %q", err, ec.want)
			}
		})
	}
}

// TestLesson_UnaddressableValuePanics shows what SetField protects callers
// from: reflect on a struct VALUE is a copy, and setting it panics.
func TestLesson_UnaddressableValuePanics(t *testing.T) {
	c := ServerConfig{Host: "a"}
	var msg string
	func() {
		defer func() { msg = fmt.Sprint(recover()) }()
		reflect.ValueOf(c).Field(0).SetString("b")
	}()
	if !strings.Contains(msg, "unaddressable") {
		t.Fatalf("expected an unaddressable panic, got %q", msg)
	}
	t.Logf("reflect.ValueOf(c).Field(0).SetString → panic: %s", msg)

	reflect.ValueOf(&c).Elem().Field(0).SetString("b") // via pointer: fine
	if c.Host != "b" {
		t.Fatal("setting through Elem() of a pointer should modify c")
	}
}

// ----------------------------------------------------------------------------
// ToMap
// ----------------------------------------------------------------------------

func TestToMapHonoursJSONTags(t *testing.T) {
	s := validSignup()
	s.Plan = "" // omitempty
	m, err := ToMap(&s)
	if err != nil {
		t.Fatal(err)
	}
	want := map[string]any{
		"name": "Ada", "email": "ada@example.com", "age": 36,
		"address": map[string]any{"city": "Pune", "country": "IN"},
	}
	if !reflect.DeepEqual(m, want) {
		t.Fatalf("got  %#v\nwant %#v", m, want)
	}
	if _, err := ToMap("nope"); !errors.Is(err, ErrNotStruct) {
		t.Fatal("ToMap of a string should fail")
	}
}

// ----------------------------------------------------------------------------
// GenerateStringer
// ----------------------------------------------------------------------------

// Regenerate with: REFLECTGEN_UPDATE=1 go test -run TestGeneratedLevelStringIsFresh .
func TestGeneratedLevelStringIsFresh(t *testing.T) {
	src, err := os.ReadFile("level.go")
	if err != nil {
		t.Fatal(err)
	}
	fresh, err := GenerateStringer(src, "Level")
	if err != nil {
		t.Fatal(err)
	}
	if os.Getenv("REFLECTGEN_UPDATE") == "1" {
		if err := os.WriteFile("level_string_gen.go", fresh, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	committed, err := os.ReadFile("level_string_gen.go")
	if err != nil {
		t.Fatalf("%v (run with REFLECTGEN_UPDATE=1 to create it)", err)
	}
	if !bytes.Equal(fresh, committed) {
		t.Fatalf("level_string_gen.go is stale; regenerate.\n--- fresh ---\n%s", fresh)
	}
}

func TestGeneratedStringerBehaviour(t *testing.T) {
	// A slice, not a map: LevelDefault == LevelInfo would be a duplicate key.
	cases := []struct {
		lvl  Level
		want string
	}{
		{LevelDebug, "LevelDebug"},
		{LevelInfo, "LevelInfo"},
		{LevelFatal, "LevelFatal"},
		{LevelDefault, "LevelInfo"}, // alias shares the first name
		{Level(3), "Level(3)"},      // the reserved `_` slot
		{Level(42), "Level(42)"},
	}
	for _, c := range cases {
		if got := c.lvl.String(); got != c.want {
			t.Errorf("Level(%d).String() = %q, want %q", int(c.lvl), got, c.want)
		}
	}
	if got := fmt.Sprintf("%v|%d", LevelWarn, LevelWarn); got != "LevelWarn|1" {
		t.Fatalf("fmt uses Stringer for %%v but not %%d: got %q", got)
	}
}

// TestGeneratedCodeTypeChecks compiles (type-checks) generated output together
// with its input for a second, independent enum — no subprocess needed.
func TestGeneratedCodeTypeChecks(t *testing.T) {
	src := []byte(`package shapes

type Kind uint8

const (
	Circle Kind = 1 << iota
	Square
	Triangle
)
`)
	gen, err := GenerateStringer(src, "Kind")
	if err != nil {
		t.Fatal(err)
	}
	fset := token.NewFileSet()
	f1, _ := parser.ParseFile(fset, "shapes.go", src, 0)
	f2, err := parser.ParseFile(fset, "kind_string.go", gen, 0)
	if err != nil {
		t.Fatalf("generated code does not parse: %v\n%s", err, gen)
	}
	conf := types.Config{Importer: importer.Default()}
	if _, err := conf.Check("shapes", fset, []*ast.File{f1, f2}, nil); err != nil {
		t.Fatalf("generated code does not type-check: %v\n%s", err, gen)
	}
	for _, want := range []string{"case Circle:", "case Square:", "case Triangle:", "DO NOT EDIT"} {
		if !bytes.Contains(gen, []byte(want)) {
			t.Fatalf("missing %q in:\n%s", want, gen)
		}
	}

	if _, err := GenerateStringer(src, "Missing"); err == nil {
		t.Fatal("expected error for unknown type")
	}
	if _, err := GenerateStringer([]byte("package x\nconst ("), "X"); err == nil {
		t.Fatal("expected parse error")
	}
}

// ----------------------------------------------------------------------------
// CheckContextFirst
// ----------------------------------------------------------------------------

func TestCheckContextFirst(t *testing.T) {
	src := []byte(`package svc

import stdctx "context"

type Store struct{}

func Good(ctx stdctx.Context, id string) error          { return nil }
func NoContext(id string) error                         { return nil }
func Bad(id string, ctx stdctx.Context) error            { return nil }
func BadGrouped(a, b int, ctx stdctx.Context)            {}
func (s *Store) Get(key string, ctx stdctx.Context) error { return nil }
func (s Store) Put(ctx stdctx.Context, key string) error  { return nil }
`)
	diags, err := CheckContextFirst("svc.go", src)
	if err != nil {
		t.Fatal(err)
	}
	var funcs []string
	for _, d := range diags {
		funcs = append(funcs, d.Func)
		t.Log(d)
	}
	want := []string{"Bad", "BadGrouped", "Store.Get"}
	if !reflect.DeepEqual(funcs, want) {
		t.Fatalf("flagged %v, want %v", funcs, want)
	}
	if !strings.Contains(diags[1].Message, "position 2") {
		t.Fatalf("grouped params must count names, not fields: %s", diags[1].Message)
	}

	noImport := []byte("package x\nfunc F(a int, context int) {}\n")
	if d, _ := CheckContextFirst("x.go", noImport); len(d) != 0 {
		t.Fatalf("no context import → no findings, got %v", d)
	}
}

// ----------------------------------------------------------------------------
// Benchmarks — what does reflection cost?
// ----------------------------------------------------------------------------

func validateByHand(s *SignupRequest) error {
	var errs []error
	if n := len(s.Name); n == 0 || n < 2 || n > 32 {
		errs = append(errs, &FieldError{Field: "Name", Rule: "min"})
	}
	if at := strings.LastIndexByte(s.Email, '@'); at < 1 || !strings.Contains(s.Email[at+1:], ".") {
		errs = append(errs, &FieldError{Field: "Email", Rule: "email"})
	}
	if s.Age < 13 || s.Age > 130 {
		errs = append(errs, &FieldError{Field: "Age", Rule: "min"})
	}
	switch s.Plan {
	case "free", "pro", "team":
	default:
		errs = append(errs, &FieldError{Field: "Plan", Rule: "oneof"})
	}
	if len(s.Tags) > 3 {
		errs = append(errs, &FieldError{Field: "Tags", Rule: "max"})
	}
	if s.Address == nil || s.Address.City == "" {
		errs = append(errs, &FieldError{Field: "Address", Rule: "required"})
	} else {
		switch s.Address.Country {
		case "IN", "US", "DE":
		default:
			errs = append(errs, &FieldError{Field: "Address.Country", Rule: "oneof"})
		}
	}
	return errors.Join(errs...)
}

var sinkErr error

func BenchmarkValidateReflect(b *testing.B) {
	s := validSignup()
	b.ReportAllocs()
	for b.Loop() {
		sinkErr = Validate(&s)
	}
}

func BenchmarkValidateHandwritten(b *testing.B) {
	s := validSignup()
	b.ReportAllocs()
	for b.Loop() {
		sinkErr = validateByHand(&s)
	}
}

var sinkMap map[string]any

func BenchmarkToMapReflect(b *testing.B) {
	s := validSignup()
	b.ReportAllocs()
	for b.Loop() {
		sinkMap, _ = ToMap(&s)
	}
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleValidate() {
	type Login struct {
		User string `validate:"required,min=3"`
		Pass string `validate:"required,min=8"`
	}
	fmt.Println(Validate(Login{User: "al", Pass: "correct horse"}))
	// Output: User: length 2 is less than 3
}

func ExampleSetField() {
	type Opts struct {
		Workers int
		Timeout time.Duration
	}
	var o Opts
	_ = SetField(&o, "Workers", "8")
	_ = SetField(&o, "Timeout", "250ms")
	fmt.Printf("%+v\n", o)
	fmt.Println(SetField(o, "Workers", "1")) // by value: refused, not a silent no-op
	// Output:
	// {Workers:8 Timeout:250ms}
	// reflectgen: need a non-nil pointer to a struct
}

func ExampleGenerateStringer() {
	src := []byte("package p\n\ntype Weekday int\n\nconst (\n\tMonday Weekday = iota + 1\n\tTuesday\n)\n")
	out, _ := GenerateStringer(src, "Weekday")
	fmt.Print(string(out))
	// Output:
	// // Code generated by reflectgen.GenerateStringer; DO NOT EDIT.
	//
	// package p
	//
	// import "strconv"
	//
	// func (i Weekday) String() string {
	// 	switch i {
	// 	case Monday:
	// 		return "Monday"
	// 	case Tuesday:
	// 		return "Tuesday"
	// 	default:
	// 		return "Weekday(" + strconv.FormatInt(int64(i), 10) + ")"
	// 	}
	// }
}
