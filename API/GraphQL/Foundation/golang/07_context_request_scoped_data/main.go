/*
FOUNDATION LEVEL 07 - Context: handing request-scoped data to every resolver
================================================================================
A resolver deep in the tree often needs something that belongs to the REQUEST,
not to the schema: who is calling, a request id for logs, the open database
connection, the loaded config. You cannot pass it as a field argument - it is
not the client's business, and you would have to thread it through every
level. You must not put it in a package-level variable - two requests running
at once would overwrite each other.

The answer is the CONTEXT: one value built per execution, handed to the engine
as graphql.Params.Context, and available to every resolver at every depth via
p.Context. It is Go's ordinary context.Context, the same one net/http gives
you (level 11 will pass r.Context() straight through). Same lifetime, too:
created when the request arrives, discarded when the response is sent.

This is the mechanism levels 08, 09 and 10 are built on: middleware writes
into the context, resolvers read from it. Learn it here, in isolation, with
nothing else going on.

You will learn
  - how to build a context per execution and pass it to the engine
  - how to read it from a resolver (p.Context.Value) at any depth
  - why the key is an unexported custom type, not a plain string
  - that the context is per-request: concurrent executions never see each
    other's values - proven below with real goroutines
  - what belongs in it (request id, caller identity, db handle, loaders) and
    what does not (anything the client should be sending as an argument)

Run it   go run ./GraphQL/Foundation/golang/07_context_request_scoped_data
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"
	"sync"

	"github.com/graphql-go/graphql"
)

// A private key type. If the key were the plain string "requestID", any other
// package could collide with it (or read it) by accident. This is the standard
// Go idiom, and it is the one detail people skip.
type ctxKey string

const (
	requestIDKey ctxKey = "requestID"
	callerKey    ctxKey = "caller"
	dbKey        ctxKey = "db"
)

type fakeDB struct{ Rows int }

func requestID(ctx context.Context) string {
	id, _ := ctx.Value(requestIDKey).(string)
	return id
}

func buildSchema() graphql.Schema {
	traceType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Trace",
		Fields: graphql.Fields{
			"requestId": {
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// Two levels down from the root, and the context is exactly
					// the same value the top-level resolver saw. Nobody passed
					// it along by hand.
					return requestID(p.Context), nil
				},
			},
			"path": {
				// p.Info carries more than the context: this is where the
				// engine is currently working in the response tree.
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					parts := make([]string, 0, len(p.Info.Path.AsArray()))
					for _, segment := range p.Info.Path.AsArray() {
						parts = append(parts, fmt.Sprint(segment))
					}
					return strings.Join(parts, "."), nil
				},
			},
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"whoami": {
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// The caller identity was put here by whoever built the
					// context - the HTTP layer in a real service (level 11).
					// The resolver just reads it.
					caller, _ := p.Context.Value(callerKey).(string)
					return caller, nil
				},
			},
			"requestId": {
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					return requestID(p.Context), nil
				},
			},
			"trace": {
				Type:    graphql.NewNonNull(traceType),
				Resolve: func(graphql.ResolveParams) (any, error) { return struct{}{}, nil },
			},
			"dbRows": {
				// A stand-in for the real reason context exists: shared,
				// expensive, per-request resources. Opening a connection per
				// resolver would be a bug.
				Type: graphql.NewNonNull(graphql.Int),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					db, _ := p.Context.Value(dbKey).(*fakeDB)
					return db.Rows, nil
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

// buildContext is called ONCE per incoming request. In level 11 this runs
// inside the HTTP handler, starting from r.Context() and reading the request
// id and the Authorization header off the wire.
func buildContext(reqID, caller string) context.Context {
	ctx := context.Background()
	ctx = context.WithValue(ctx, requestIDKey, reqID)
	ctx = context.WithValue(ctx, callerKey, caller)
	ctx = context.WithValue(ctx, dbKey, &fakeDB{Rows: 42})
	return ctx
}

func run(schema graphql.Schema, title, query string, ctx context.Context) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query, Context: ctx})
	out, _ := json.Marshal(result)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("context  : requestID=%s caller=%v\n", requestID(ctx), ctx.Value(callerKey))
	fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
	fmt.Printf("response : %s\n", out)
	return result
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()

	// Note: `requestId` is NOT an argument the client supplies. It is not in
	// the query as input at all - it comes from beside the query.
	result := run(schema, "1. a resolver reading a value the client never sent",
		"{ requestId whoami }", buildContext("req-001", "alice"))
	data := result.Data.(map[string]any)
	must(data["requestId"] == "req-001" && data["whoami"] == "alice", "context values")

	result = run(schema, "2. the same context, seen identically two levels down",
		"{ requestId trace { requestId path } }", buildContext("req-002", "alice"))
	data = result.Data.(map[string]any)
	trace := data["trace"].(map[string]any)
	must(data["requestId"] == "req-002" && trace["requestId"] == "req-002", "same value at depth")
	must(trace["path"] == "trace.path", "p.Info.Path")
	fmt.Println("   -> no plumbing: the nested resolver did not receive it from its parent")

	result = run(schema, "3. a shared per-request resource (a fake db handle) instead of a value",
		"{ dbRows }", buildContext("req-003", "bob"))
	must(result.Data.(map[string]any)["dbRows"] == 42, "db handle from context")

	// The point of per-request scope: run several executions at the same time,
	// in different goroutines, and no resolver sees another request's id. A
	// package-level variable could not do this.
	var (
		mu      sync.Mutex
		results = map[string]string{}
		wg      sync.WaitGroup
	)
	for _, id := range []string{"req-10", "req-11", "req-12"} {
		wg.Add(1)
		go func(reqID string) {
			defer wg.Done()
			res := graphql.Do(graphql.Params{
				Schema:        schema,
				RequestString: "{ requestId trace { requestId } }",
				Context:       buildContext(reqID, "concurrent"),
			})
			out, _ := json.Marshal(res.Data)
			mu.Lock()
			results[reqID] = string(out)
			mu.Unlock()
		}(id)
	}
	wg.Wait()

	fmt.Println("\n# 4. three executions at once, in three goroutines")
	ids := make([]string, 0, len(results))
	for id := range results {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		fmt.Printf("  %s -> %s\n", id, results[id])
		expected := fmt.Sprintf(`{"requestId":"%s","trace":{"requestId":"%s"}}`, id, id)
		must(results[id] == expected, "each goroutine saw only its own context: "+id)
	}
	fmt.Println("   -> every resolver saw its OWN request's context. This is why it is not a global.")

	fmt.Println("\nOK")
}
