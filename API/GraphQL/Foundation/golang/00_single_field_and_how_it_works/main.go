/*
FOUNDATION LEVEL 00 (start here) - A basic GraphQL endpoint, explained end to end
=====================================================================================
If someone says "build me a basic GraphQL endpoint", THIS is what they mean: one
schema with one field, one function behind that field. The client sends the text
`{ hello }`, and gets back `{"data": {"hello": "world"}}`. Nothing about HTTP,
databases, or nested types yet - just enough to watch the whole ask/answer loop
happen once, so every later level is "add one more piece" instead of "understand
everything at once".

THE MENTAL MODEL (read this before the code)

	GraphQL is not a server, and not a network protocol. It is three things:
	  - a SCHEMA: the complete list of fields a client is allowed to ask for,
	    and what type each one returns. This is the contract.
	  - a QUERY: a little document the CLIENT writes, naming which of those
	    fields it wants. The response comes back in the same shape as the query.
	  - an EXECUTION ENGINE: reads the query, checks it against the schema, then
	    calls one RESOLVER function per requested field and assembles the answers.
	A "resolver" is nothing exotic: it is a normal function whose return value
	becomes that field's value in the response.

	Because it is just an engine, we can call it DIRECTLY in this process - no
	port, no socket, no curl. That is exactly what levels 00-10 do, so you can
	study GraphQL itself without HTTP noise in the way. In production the same
	engine sits behind a single HTTP POST endpoint (level 11 builds that for
	real, and level 13 proves there is nothing magic about the wire).

	{data, errors} is GraphQL's version of REST's "status code + body": `data`
	holds whatever resolved successfully, `errors` lists what went wrong. Unlike
	REST, the two arrive TOGETHER - a request can be half-successful (level 06).

	Nothing is remembered between calls. Each execution is a fresh, unrelated
	conversation: resolvers run again from scratch (see ../../Theory.md).

You will learn
  - what a schema is (the contract) and what a resolver is (a plain function)
  - that a query is written by the CLIENT, and the response mirrors its shape
  - what `{data, errors}` means, and why it replaces REST's status codes
  - that asking for a field the schema does not have is a normal, handled
    outcome - rejected before a single resolver runs (GraphQL's "404")
  - that GraphQL rides over ordinary HTTP, and needs it no more than this file does

Run it         go run ./GraphQL/Foundation/golang/00_single_field_and_how_it_works
Keep serving   go run ./GraphQL/Foundation/golang/00_single_field_and_how_it_works -serve   (curl -s localhost:8080/graphql -d '{"query":"{ hello }"}')
*/
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"strings"

	"github.com/graphql-go/graphql"
)

// Proves resolvers really do run per execution, and that nothing is cached
// or remembered between calls.
var helloResolverCalls int

func buildSchema() graphql.Schema {
	// This object IS the schema's "Query" type. Every entry in Fields becomes
	// a field a client is allowed to ask for; Type is that field's type in the
	// contract; Resolve is the function that produces its value.
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"hello": {
				// String! - the `!` (NewNonNull) promises "never null".
				Type: graphql.NewNonNull(graphql.String),
				// A resolver is called ONLY when the client asks for its field.
				// It could read a database, call another service, or - here -
				// just return a constant. The engine does not care where the
				// value came from, only that it matches the declared type.
				Resolve: func(p graphql.ResolveParams) (any, error) {
					helloResolverCalls++
					return "world", nil
				},
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		log.Fatal(err) // an invalid schema is a programming error, caught at startup
	}
	return schema
}

// run executes a query against the schema, in-process. No network involved.
func run(schema graphql.Schema, title, query string) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query})
	// This JSON is exactly what a GraphQL HTTP endpoint would send back.
	out, _ := json.Marshal(result)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("query    : %s\n", query)
	fmt.Printf("response : %s\n", out)
	return result
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	schema := buildSchema()

	if *serve {
		// Optional: the exact same schema, behind one real HTTP POST endpoint.
		// This is a preview - level 11 builds it properly and level 13 shows
		// the raw bytes underneath. Notice how little there is to it: read a
		// JSON body, hand `query` to the engine, write {data, errors} back.
		http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
			var body struct {
				Query string `json:"query"`
			}
			json.NewDecoder(r.Body).Decode(&body)
			result := graphql.Do(graphql.Params{Schema: schema, RequestString: body.Query})
			w.Header().Set("Content-Type", "application/json")
			// GraphQL says 200 even for field errors - see level 06.
			json.NewEncoder(w).Encode(result)
		})
		log.Println("listening on http://localhost:8080/graphql")
		log.Println(`try: curl -s localhost:8080/graphql -d '{"query":"{ hello }"}'`)
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", nil))
	}

	fmt.Println("=== the schema, printed as SDL - this IS the contract ===")
	fmt.Println("type Query {\n  hello: String!\n}")

	result := run(schema, "1. the whole point: ask for a field, get that field back", "{ hello }")
	data := result.Data.(map[string]any)
	must(data["hello"] == "world", "hello must resolve to world")
	must(!result.HasErrors(), "a successful execution has no errors entry at all")

	// Run the identical query again. Same answer, but the resolver ran a
	// SECOND time - the engine kept nothing from last time.
	run(schema, "2. the same query again - stateless: the resolver runs again", "{ hello }")
	fmt.Printf("hello resolver calls so far: %d\n", helloResolverCalls)
	must(helloResolverCalls == 2, "each execution is independent - nothing is cached")

	// Now ask for something the schema never promised. GraphQL checks the
	// whole query against the schema BEFORE running anything, so this is
	// caught for free - you never wrote this check. This is the moral
	// equivalent of REST's 404, except it is one uniform mechanism for every
	// mistake, not a status code per situation.
	result = run(schema, "3. a field the schema does not have - rejected before any resolver runs", "{ goodbye }")
	must(result.Data == nil, "data must be null")
	must(strings.Contains(result.Errors[0].Message, `Cannot query field "goodbye"`), "validation message")
	must(helloResolverCalls == 2, "nothing resolved: validation failed first")
	fmt.Println("   -> data is null, errors explains why. Nothing crashed.")

	fmt.Println("\nOK")
}
