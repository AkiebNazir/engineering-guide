/*
LEVEL 04 (core) - real errors: json.SyntaxError and DisallowUnknownFields

You will learn
  - malformed JSON produces a *json.SyntaxError with a byte Offset - a real,
    inspectable error type, not a generic string
  - a type mismatch (JSON string into a Go int) produces *json.UnmarshalTypeError
  - by default, unknown JSON fields are silently dropped; Decoder.DisallowUnknownFields
    turns that into a real, catchable error

Run: go run ./GoStdLib/09_encoding_json/level_04_errors_syntax_and_unknown_fields
*/

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

type Config struct {
	Host string `json:"host"`
	Port int    `json:"port"`
}

func main() {
	// --- a real syntax error: trailing comma is not valid JSON ---
	badJSON := []byte(`{"host": "localhost", "port": 8080,}`)
	var cfg Config
	err := json.Unmarshal(badJSON, &cfg)
	if err == nil {
		panic("expected a syntax error for trailing comma, got nil")
	}
	var syntaxErr *json.SyntaxError
	if !errors.As(err, &syntaxErr) {
		panic(fmt.Sprintf("expected *json.SyntaxError, got %T: %v", err, err))
	}
	fmt.Printf("syntax error at byte offset %d: %v\n", syntaxErr.Offset, syntaxErr)

	// --- a real type error: JSON string where the struct expects an int ---
	typeMismatch := []byte(`{"host": "localhost", "port": "not-a-number"}`)
	err = json.Unmarshal(typeMismatch, &cfg)
	var typeErr *json.UnmarshalTypeError
	if !errors.As(err, &typeErr) {
		panic(fmt.Sprintf("expected *json.UnmarshalTypeError, got %T: %v", err, err))
	}
	if typeErr.Field != "port" {
		panic(fmt.Sprintf("UnmarshalTypeError.Field = %q, want %q", typeErr.Field, "port"))
	}
	fmt.Printf("type error on field %q: got %s, want %s\n", typeErr.Field, typeErr.Value, typeErr.Type)

	// --- by default, an unknown field is silently ignored ---
	withExtra := []byte(`{"host": "localhost", "port": 8080, "unexpected_field": true}`)
	var lenient Config
	if err := json.Unmarshal(withExtra, &lenient); err != nil {
		panic(fmt.Sprintf("plain Unmarshal should ignore unknown fields, got: %v", err))
	}
	if lenient.Host != "localhost" || lenient.Port != 8080 {
		panic(fmt.Sprintf("lenient decode = %+v, want {localhost 8080}", lenient))
	}

	// --- DisallowUnknownFields makes the same input a real, catchable error ---
	dec := json.NewDecoder(bytes.NewReader(withExtra))
	dec.DisallowUnknownFields()
	var strict Config
	err = dec.Decode(&strict)
	if err == nil {
		panic("expected DisallowUnknownFields to reject unexpected_field, got nil error")
	}
	if !strings.Contains(err.Error(), "unexpected_field") {
		panic(fmt.Sprintf("error should name the offending field, got: %v", err))
	}
	fmt.Printf("strict decoder correctly rejected unknown field: %v\n", err)

	fmt.Println("OK")
}
