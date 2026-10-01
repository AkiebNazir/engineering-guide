/*
LEVEL 08 (interop) - net/http + encoding/json + errors: a strict JSON endpoint

You will learn
  - decode request bodies with json.NewDecoder(r.Body), not io.ReadAll +
    Unmarshal, and cap the size first with http.MaxBytesReader so one client
    can't make you buffer a gigabyte
  - DisallowUnknownFields turns a typo'd field name into a 400 instead of a
    silently ignored value (see ../09_encoding_json level 4)
  - errors.As with *http.MaxBytesError tells "too large" (413) apart from
    "malformed" (400)
  - httptest.NewRecorder calls a handler directly, with no server and no
    socket - the fastest way to unit-test handlers

Run: go run ./GoStdLib/16_net_http/level_08_interop_json_bodies
*/

package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

type signup struct {
	Email string `json:"email"`
	Plan  string `json:"plan"`
}

type apiError struct {
	Error string `json:"error"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func handleSignup(w http.ResponseWriter, r *http.Request) {
	if ct := r.Header.Get("Content-Type"); !strings.HasPrefix(ct, "application/json") {
		writeJSON(w, http.StatusUnsupportedMediaType, apiError{"send application/json"})
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<10) // 1 KB is plenty for this payload
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	var in signup
	if err := dec.Decode(&in); err != nil {
		var tooBig *http.MaxBytesError
		if errors.As(err, &tooBig) {
			writeJSON(w, http.StatusRequestEntityTooLarge, apiError{fmt.Sprintf("body over %d bytes", tooBig.Limit)})
			return
		}
		writeJSON(w, http.StatusBadRequest, apiError{err.Error()})
		return
	}
	if !strings.Contains(in.Email, "@") {
		writeJSON(w, http.StatusUnprocessableEntity, apiError{"email is not valid"})
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"email": in.Email, "plan": in.Plan})
}

func main() {
	cases := []struct {
		name, contentType, body string
		want                    int
	}{
		{"valid", "application/json", `{"email":"a@b.io","plan":"pro"}`, 201},
		{"typo'd field", "application/json", `{"email":"a@b.io","plna":"pro"}`, 400},
		{"broken JSON", "application/json", `{"email":`, 400},
		{"too large", "application/json", `{"email":"` + strings.Repeat("a", 2000) + `@b.io"}`, 413},
		{"bad email", "application/json", `{"email":"nope","plan":"free"}`, 422},
		{"form post", "application/x-www-form-urlencoded", `email=a@b.io`, 415},
	}
	for _, c := range cases {
		req := httptest.NewRequest(http.MethodPost, "/signup", strings.NewReader(c.body))
		req.Header.Set("Content-Type", c.contentType)
		rec := httptest.NewRecorder() // no server, no socket
		handleSignup(rec, req)

		out := strings.TrimSpace(rec.Body.String())
		if len(out) > 70 {
			out = out[:70] + "..."
		}
		fmt.Printf("%-13s -> %d %s\n", c.name, rec.Code, out)
		if rec.Code != c.want {
			panic(fmt.Sprintf("%s: want %d, got %d", c.name, c.want, rec.Code))
		}
		if rec.Header().Get("Content-Type") != "application/json" {
			panic("every response, errors included, should be JSON")
		}
	}
	fmt.Println("OK")
}
