/*
FOUNDATION LEVEL 08 - Middleware: code that wraps every execution
=====================================================================
Levels 00-07 called graphql.Do(...) directly. Real services never do: every
request first passes through a stack of concerns that have nothing to do with
your schema - logging, timing, metrics, request ids, crash recovery, and (next
two levels) authentication and authorization.

A middleware is a WRAPPER: a function that takes "the thing that executes a
request" and returns a NEW thing with the same shape, which runs code before
and/or after calling the original. Because the shape is unchanged, wrappers
stack, and your schema never learns any of it exists.

	execute := withLogging(withRecovery(runQuery))
	           ^ outermost                ^ the real work

Note the two DIFFERENT safety nets in this file, because conflating them is
the classic confusion:

 1. the ENGINE's per-field net. A resolver that panics is caught by
    graphql-go itself and turned into an errors[] entry (level 06). Sibling
    fields still resolve. You get this for free.
 2. YOUR net, withRecovery. It catches bugs in the request-handling code
    AROUND execution - the parts GraphQL knows nothing about. Without it, one
    malformed request takes the whole process down.

You will learn
  - a middleware has the same shape as what it wraps: request in, response out
  - chaining: wrapping a wrapper, in a chosen order
  - that a resolver panicking is already contained by the engine - the query
    still returns a clean, partial answer and the process stays up
  - that a panic OUTSIDE execution needs your own recover(), or the process dies
  - that ORDER matters: with logging OUTSIDE recovery the crash is still
    logged; swap them and the log line silently disappears

Run it   go run ./GraphQL/Foundation/golang/08_middleware_logging_and_recovery
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/graphql-go/graphql"
)

// Middleware talks in whole requests and whole responses, not in fields.
type request map[string]any  // {"query": "...", "variables": {...}}
type response map[string]any // {"data": ..., "errors": [...]}
type execute func(request) response

var logLines []string

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"healthy": {
				Type:    graphql.NewNonNull(graphql.Boolean),
				Resolve: func(graphql.ResolveParams) (any, error) { return true, nil },
			},
			"boom": {
				// A real bug in a resolver: a panic, not a returned error.
				Type: graphql.String,
				Resolve: func(graphql.ResolveParams) (any, error) {
					panic("resolver blew up")
				},
			},
			"slow": {
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(graphql.ResolveParams) (any, error) {
					time.Sleep(20 * time.Millisecond) // so the timing middleware has something to print
					return "done", nil
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

// ---- the innermost layer: the only part that knows about GraphQL ----------
func makeRunQuery(schema graphql.Schema) execute {
	return func(req request) response {
		// Deliberately written the naive way, exactly as a first draft usually
		// is: it TRUSTS the request to carry a "query" string. A client that
		// posts {"variables": {...}} and nothing else makes this type
		// assertion panic. That is the realistic crash withRecovery contains.
		queryText := req["query"].(string)

		vars, _ := req["variables"].(map[string]any)
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  queryText,
			VariableValues: vars,
		})
		res := response{"data": result.Data}
		if result.HasErrors() {
			res["errors"] = result.Errors
		}
		return res
	}
}

// ---- middleware 1: what ran, and how long it took ------------------------
func withLogging(next execute) execute {
	return func(req request) response {
		start := time.Now()
		res := next(req) // <- everything inside happens here
		queryText, ok := req["query"].(string)
		if !ok {
			queryText = "<no query>"
		}
		line := fmt.Sprintf("[log] %s -> %d error(s) in %.1fms",
			strings.Join(strings.Fields(queryText), " "), errorCountOf(res),
			float64(time.Since(start).Microseconds())/1000)
		logLines = append(logLines, line)
		fmt.Println("  " + line)
		return res
	}
}

// ---- middleware 2: turn any escaped panic into a clean GraphQL error -----
func withRecovery(next execute) execute {
	return func(req request) (res response) {
		// A deferred recover() is Go's equivalent of try/except around
		// everything this middleware wraps. The named return value is what
		// lets us replace the response after a panic has already unwound.
		defer func() {
			if r := recover(); r != nil {
				// Never leak the panic text to the client in a real service -
				// log it, and hand back something deliberately vague.
				fmt.Printf("  [recovery] caught %v - the process stays up, this ONE request fails\n", r)
				res = response{"data": nil, "errors": []map[string]string{{"message": "internal server error"}}}
			}
		}()
		return next(req)
	}
}

// errorCountOf counts the errors in a response without caring which layer
// produced them (the engine's typed errors, or recovery's hand-made one).
func errorCountOf(res response) int {
	raw, _ := json.Marshal(res["errors"])
	var list []any
	json.Unmarshal(raw, &list)
	return len(list)
}

func show(res response) response {
	out, _ := json.Marshal(res)
	fmt.Printf("response : %s\n", out)
	return res
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()
	runQuery := makeRunQuery(schema)

	// Built once, outside in. Logging is OUTERMOST so it also sees requests
	// that recovery had to rescue - see demo 4 for what happens if you swap.
	pipeline := withLogging(withRecovery(runQuery))

	fmt.Println("\n# 1. a normal request: the log line is the only visible difference")
	res := show(pipeline(request{"query": "{ healthy slow }"}))
	data := res["data"].(map[string]any)
	must(data["healthy"] == true && data["slow"] == "done", "normal request")
	must(strings.Contains(logLines[len(logLines)-1], "0 error(s)"), "logged with no errors")

	// Safety net 1 (the engine's). The resolver panicked, and yet: the process
	// is alive, `healthy` still answered, and the failure is a normal error.
	fmt.Println("\n# 2. a resolver that blows up: contained by the engine, per field")
	res = show(pipeline(request{"query": "{ healthy boom }"}))
	data = res["data"].(map[string]any)
	must(data["healthy"] == true && data["boom"] == nil, "partial data after a resolver panic")
	must(errorCountOf(res) == 1, "one field error")
	must(strings.Contains(logLines[len(logLines)-1], "1 error(s)"), "the log line saw it")
	fmt.Println("   -> one bad resolver is a partial response, not a dead server (level 06's rule)")

	// Safety net 2 (ours). This panic happens in runQuery, before the engine
	// is ever involved - GraphQL cannot help, so withRecovery must.
	fmt.Println("\n# 3. a malformed request that crashes OUR code, not a resolver")
	res = show(pipeline(request{"variables": map[string]any{"x": 1}}))
	must(res["data"] == nil && errorCountOf(res) == 1, "clean internal error")
	must(strings.HasPrefix(logLines[len(logLines)-1], "[log] <no query>"), "logging still ran: it wraps recovery")
	fmt.Println("   -> without withRecovery this panic would have escaped and killed the process")

	// Order. Same two middlewares, wrapped the other way round.
	fmt.Println("\n# 4. the SAME two middlewares, chained in the wrong order")
	wrongOrder := withRecovery(withLogging(runQuery))
	before := len(logLines)
	res = show(wrongOrder(request{"variables": map[string]any{"x": 1}}))
	must(res["data"] == nil && errorCountOf(res) == 1, "still a clean failure")
	must(len(logLines) == before, "the panic escaped withLogging before it could log anything")
	fmt.Println("   -> the request still failed cleanly, but NOTHING was logged: the panic")
	fmt.Println("      unwound through withLogging at its `next(req)` call, so the code after")
	fmt.Println("      that call never ran. Outermost middleware sees the most.")

	// Still alive after all of the above - which is the entire point.
	fmt.Println("\n# 5. the process survived every failure above")
	res = show(pipeline(request{"query": "{ healthy }"}))
	must(res["data"].(map[string]any)["healthy"] == true, "still serving")

	fmt.Printf("\nlog lines collected: %d\n", len(logLines))
	fmt.Println("OK")
}
