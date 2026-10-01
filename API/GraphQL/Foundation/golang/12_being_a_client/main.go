/*
FOUNDATION LEVEL 12 - Being the client: calling a GraphQL endpoint by hand
==============================================================================
Levels 00-11 were all SERVER code. You will spend at least as much time on the
other side: calling someone else's GraphQL API. This level flips the lens. The
server here is a stripped-down copy of level 11 (deliberately made flaky), and
the interesting code is the CLIENT.

No client library is used, on purpose. There is nothing to install: a GraphQL
request is one HTTP POST with a JSON body you can build in four lines.

	{"query": "query Q($id: ID!) { ... }", "variables": {"id": "r1"}}

The GraphQL-specific trap for clients, and the main reason this level exists:
HTTP 200 DOES NOT MEAN SUCCESS. A field can fail while the transport worked
perfectly (level 06), so every response needs TWO checks - the status code,
and then `errors`. And the two failure kinds want opposite handling:

  - HTTP 5xx / connection refused / timeout -> transient. Retry with backoff.
  - HTTP 200 with `errors` -> the server understood you and says no (bad
    query, blank title, FORBIDDEN). Retrying is pointless, and for a
    mutation it can be actively harmful.

You will learn
  - how to build a {query, variables} POST body and a Bearer header by hand
  - to check the status code AND `errors` - never just one of them
  - exponential backoff for genuinely transient failures, and a retry budget
  - why a 200 carrying `errors` must NOT be retried, though a 503 should be
  - that partial data (`data` and `errors` together) is a normal thing a
    client has to decide about, not a bug

Run it   go run ./GraphQL/Foundation/golang/12_being_a_client
*/
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/graphql-go/graphql"
)

type identity struct {
	User string
	Role string
}

var tokens = map[string]identity{"alice-token": {User: "alice", Role: "admin"}}

type ctxKey string

const userCtxKey ctxKey = "user"

var attempts int

type graphqlError struct {
	message    string
	extensions map[string]any
}

func (e graphqlError) Error() string              { return e.message }
func (e graphqlError) Extensions() map[string]any { return e.extensions }

// ---- "someone else's API": a small, deliberately flaky level-11 endpoint ----
type reportRow struct {
	ID    string
	Title string
}

func buildSchema() graphql.Schema {
	reportType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Report",
		Fields: graphql.Fields{
			"id":    {Type: graphql.NewNonNull(graphql.ID)},
			"title": {Type: graphql.NewNonNull(graphql.String)},
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"report": {
				Type: reportType,
				Args: graphql.FieldConfigArgument{"id": {Type: graphql.NewNonNull(graphql.ID)}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					if p.Args["id"].(string) != "r1" {
						return nil, nil
					}
					return reportRow{ID: "r1", Title: "Q1 uptime"}, nil
				},
			},
			"me": {
				Type: graphql.String,
				Resolve: func(p graphql.ResolveParams) (any, error) {
					user, ok := p.Context.Value(userCtxKey).(identity)
					if !ok {
						return nil, graphqlError{"not authenticated", map[string]any{"code": "UNAUTHENTICATED"}}
					}
					return user.User, nil
				},
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		log.Fatal(err)
	}
	return schema
}

// flakyHandler 503s the first two calls - a real service warming up, briefly
// overloaded, or mid-deploy. Not actually broken.
func flakyHandler(schema graphql.Schema) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		attempts++
		w.Header().Set("Content-Type", "application/json")
		if attempts <= 2 {
			w.WriteHeader(http.StatusServiceUnavailable)
			json.NewEncoder(w).Encode(map[string]any{
				"errors": []map[string]string{{"message": "temporarily unavailable"}}})
			return
		}

		var req struct {
			Query     string         `json:"query"`
			Variables map[string]any `json:"variables"`
		}
		body, _ := io.ReadAll(r.Body)
		json.Unmarshal(body, &req)

		ctx := r.Context()
		if token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer "); ok {
			if user, known := tokens[token]; known {
				ctx = context.WithValue(ctx, userCtxKey, user)
			}
		}
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			VariableValues: req.Variables,
			Context:        ctx,
		})
		w.WriteHeader(http.StatusOK) // 200 even when `errors` is populated
		json.NewEncoder(w).Encode(result)
	}
}

// ---- THE CLIENT: this is the part worth reading ---------------------------

// graphqlErrors200 means the server answered 200 and said no. NOT retryable.
type graphqlErrors200 struct {
	Errors []map[string]any
	Data   map[string]any
}

func (e graphqlErrors200) Error() string {
	messages := make([]string, 0, len(e.Errors))
	for _, entry := range e.Errors {
		message, _ := entry["message"].(string)
		messages = append(messages, message)
	}
	return strings.Join(messages, "; ")
}

type response struct {
	Data   map[string]any   `json:"data"`
	Errors []map[string]any `json:"errors"`
}

// graphqlPost is ONE attempt. It builds the request by hand - this is the
// entire protocol.
func graphqlPost(url, query string, vars map[string]any, token string) (int, response, error) {
	body, _ := json.Marshal(map[string]any{"query": query, "variables": vars})
	req, err := http.NewRequest("POST", url, bytes.NewReader(body))
	if err != nil {
		return 0, response{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token) // level 09, from the client's side
	}

	client := &http.Client{Timeout: 2 * time.Second}
	res, err := client.Do(req)
	if err != nil {
		return 0, response{}, err // the server did not answer at all
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)
	var parsed response
	json.Unmarshal(raw, &parsed)
	return res.StatusCode, parsed, nil
}

// graphqlCall calls a GraphQL endpoint properly: retry transport failures,
// never retry a GraphQL error, and return `data` only once it is trustworthy.
func graphqlCall(url, query string, vars map[string]any, token string,
	maxAttempts int, allowPartial bool) (map[string]any, []map[string]any, error) {

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		status, parsed, err := graphqlPost(url, query, vars, token)
		backoff := 50 * time.Millisecond * (1 << (attempt - 1)) // 50ms, 100ms, 200ms ...

		switch {
		case err != nil:
			// No answer at all - retryable, same as a 5xx.
			if attempt == maxAttempts {
				return nil, nil, err
			}
			fmt.Printf("  attempt %d: no answer (%v), backing off %v\n", attempt, err, backoff)
			time.Sleep(backoff)

		case status >= 500:
			// TRANSIENT: the server is having a bad moment, not refusing us.
			if attempt == maxAttempts {
				return nil, nil, fmt.Errorf("giving up after %d attempts, last status %d", attempt, status)
			}
			fmt.Printf("  attempt %d: HTTP %d, backing off %v before retrying\n", attempt, status, backoff)
			time.Sleep(backoff)

		case status != 200:
			// 400/404/405: our request is malformed. It will be next time too.
			return nil, nil, fmt.Errorf("HTTP %d: %s", status, parsed.Errors)

		default:
			// HTTP 200 - the transport is done, now READ THE BODY. This check
			// is the one people forget, and the whole reason this level exists.
			if len(parsed.Errors) > 0 && !(allowPartial && parsed.Data != nil) {
				return nil, nil, graphqlErrors200{Errors: parsed.Errors, Data: parsed.Data}
			}
			return parsed.Data, parsed.Errors, nil
		}
	}
	return nil, nil, errors.New("unreachable")
}

const reportQuery = `
query GetReport($id: ID!) {
  report(id: $id) { id title }
}`

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func asJSON(value any) string {
	out, _ := json.Marshal(value)
	return string(out)
}

func main() {
	schema := buildSchema()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, flakyHandler(schema))
	url := "http://" + ln.Addr().String() + "/graphql"

	fmt.Println("# 1. the first two calls fail with 503 - the client retries, backing off")
	data, gqlErrors, err := graphqlCall(url, reportQuery, map[string]any{"id": "r1"}, "", 5, false)
	must(err == nil, "the call eventually succeeded")
	fmt.Printf("   -> data: %s\n", asJSON(data))
	report := data["report"].(map[string]any)
	must(report["id"] == "r1" && report["title"] == "Q1 uptime" && len(gqlErrors) == 0, "report fetched")
	must(attempts == 3, "expected exactly 2 transient failures then a success")
	fmt.Println("   -> succeeded on attempt 3. A client that gave up after one 503 would have failed.")

	fmt.Println("\n# 2. a GraphQL error arrives as HTTP 200 - and must NOT be retried")
	before := attempts
	_, _, err = graphqlCall(url, "{ me }", nil, "", 5, false)
	var gqlErr graphqlErrors200
	must(errors.As(err, &gqlErr), "the call returned a GraphQL error, not a transport error")
	fmt.Printf("   -> HTTP 200, errors: %s\n", asJSON(gqlErr.Errors))
	ext, _ := gqlErr.Errors[0]["extensions"].(map[string]any)
	must(ext["code"] == "UNAUTHENTICATED", "the 401-equivalent")
	must(attempts == before+1, "exactly ONE attempt: retrying would be pointless")
	fmt.Println("   -> one attempt only. The server understood us; a second identical ask changes nothing.")

	fmt.Println("\n# 3. the same query WITH the Authorization header")
	data, _, err = graphqlCall(url, "{ me }", nil, "alice-token", 5, false)
	must(err == nil && data["me"] == "alice", "authenticated call")
	fmt.Printf("   -> data: %s\n", asJSON(data))

	fmt.Println("\n# 4. a null result is a legitimate answer, not a failure")
	data, gqlErrors, err = graphqlCall(url, reportQuery, map[string]any{"id": "does-not-exist"}, "", 5, false)
	must(err == nil && data["report"] == nil && len(gqlErrors) == 0, "null is not an error")
	fmt.Printf("   -> data: %s\n", asJSON(data))

	fmt.Println("\n# 5. partial data: the caller decides whether it is usable")
	data, gqlErrors, err = graphqlCall(url, `{ report(id: "r1") { title } me }`, nil, "", 5, true)
	must(err == nil, "allowPartial accepted the response")
	fmt.Printf("   -> data: %s\n", asJSON(data))
	fmt.Printf("   -> errors: %s\n", asJSON(gqlErrors))
	must(data["report"].(map[string]any)["title"] == "Q1 uptime", "the good half survived")
	must(data["me"] == nil && len(gqlErrors) == 1, "the bad half reported itself")
	fmt.Println("   -> with allowPartial=false this same response would have been an error. Both are")
	fmt.Println("      valid policies - what is NOT valid is ignoring `errors` and using `data` blindly.")

	fmt.Println("\nOK")
}
