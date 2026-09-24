/*
FOUNDATION LEVEL 01 - Many fields, and the scalar types they come in
========================================================================
Level 00 had one field of one type. A real Query object is a menu: several
fields, each with its own type and its own resolver. This level adds that
menu, and shows the single most surprising thing about GraphQL for anyone
coming from REST: the CLIENT decides which items to order, and only those
resolvers run. There is no "the /status response", there is only "whatever
you asked for this time".

GraphQL's built-in scalars are the leaf values - the points where the
response stops nesting: Int, Float, String, Boolean, ID. Everything else
(objects, lists, enums, custom scalars) is built out of them.

You will learn
  - a Query type is just a bag of independent fields, each with a resolver
  - the response mirrors the query: ask for two fields, get exactly two keys
  - resolvers for fields you did NOT ask for never run (watch the counters) -
    this is why one GraphQL endpoint can replace a dozen REST endpoints
  - the five built-in scalars (Int, Float, String, Boolean, ID) and what
    NewNonNull means: `String!` promises "never null", `String` allows null
  - lists: NewList(NewNonNull(String)) wrapped in NewNonNull is `[String!]!`

Run it   go run ./GraphQL/Foundation/golang/01_multiple_fields_and_scalar_types
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"sort"

	"github.com/graphql-go/graphql"
)

// Counts how many times each field's resolver ran, so the demo can prove
// that unrequested fields cost nothing.
var calls = map[string]int{}

func buildSchema() graphql.Schema {
	// A tiny helper so the seven fields below read as a list of types, not as
	// seven copies of the same closure boilerplate.
	field := func(name string, t graphql.Output, value any) *graphql.Field {
		return &graphql.Field{
			Type: t,
			Resolve: func(p graphql.ResolveParams) (any, error) {
				calls[name]++
				return value, nil
			},
		}
	}

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			// String!  - non-null: this field promises a value
			"name": field("name", graphql.NewNonNull(graphql.String), "foundation-service"),
			// Int!     - a 32-bit signed integer, by spec
			"version": field("version", graphql.NewNonNull(graphql.Int), 3),
			// Float!
			"uptime": field("uptime", graphql.NewNonNull(graphql.Float), 12.5),
			// Boolean!
			"healthy": field("healthy", graphql.NewNonNull(graphql.Boolean), true),
			// ID!      - an opaque identifier. Serialized as a string, but the
			//            point is "do not do arithmetic on this", not its shape.
			"nodeId": field("nodeId", graphql.NewNonNull(graphql.ID), "node-7"),
			// [String!]! - a non-null list of non-null strings
			"regions": field("regions", graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(graphql.String))),
				[]string{"eu-west", "us-east"}),
			// String   - NULLABLE: a legitimate value here is "there isn't one",
			//            with no error at all.
			"motd": field("motd", graphql.String, nil),
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		log.Fatal(err)
	}
	return schema
}

func run(schema graphql.Schema, title, query string) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query})
	out, _ := json.Marshal(result)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("query    : %s\n", query)
	fmt.Printf("response : %s\n", out)
	return result
}

func ran() string {
	names := []string{}
	for name, n := range calls {
		if n > 0 {
			names = append(names, fmt.Sprintf("%s=%d", name, n))
		}
	}
	sort.Strings(names)
	return fmt.Sprint(names)
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()

	fmt.Println("=== the schema, as SDL: seven fields, seven types ===")
	fmt.Println(`type Query {
  name: String!
  version: Int!
  uptime: Float!
  healthy: Boolean!
  nodeId: ID!
  regions: [String!]!
  motd: String
}`)

	// Ask for two fields out of seven. Only two resolvers run. In REST you
	// would have had to design an endpoint for exactly this combination (or
	// send all seven and let the client throw six away).
	result := run(schema, "1. ask for two fields - get exactly two keys back", "{ name version }")
	data := result.Data.(map[string]any)
	must(len(data) == 2 && data["name"] == "foundation-service" && data["version"] == 3, "two fields")
	fmt.Println("resolver calls:", ran())
	must(calls["uptime"] == 0 && calls["regions"] == 0, "unrequested resolvers must not run")

	// A different client wants a different slice. Same schema, same endpoint,
	// no new server code - that is the whole selling point.
	result = run(schema, "2. a different client wants a different slice", "{ healthy regions nodeId }")
	data = result.Data.(map[string]any)
	must(data["healthy"] == true && data["nodeId"] == "node-7", "second slice")
	must(len(data["regions"].([]any)) == 2, "regions list")

	// Types are real: the engine serializes each leaf according to the schema,
	// so an Int! field is a JSON number and never the string "3".
	result = run(schema, "3. types are enforced on the way out", "{ version uptime healthy }")
	data = result.Data.(map[string]any)
	must(data["version"] == 3, "Int! stays an integer")
	must(data["uptime"] == 12.5, "Float! stays a float")
	must(data["healthy"] == true, "Boolean! stays a bool")

	// A nullable field returning nil is a SUCCESS, not a failure. Compare
	// level 06, where a nullable field fails for real.
	result = run(schema, "4. a nullable field with nothing to say -> null, and no error", "{ motd }")
	data = result.Data.(map[string]any)
	must(data["motd"] == nil && !result.HasErrors(), "null is not an error")
	fmt.Println("   -> `String` may be null; `String!` may not. That difference drives level 06.")

	// Everything at once, to show all seven resolvers finally running.
	result = run(schema, "5. the whole menu", "{ name version uptime healthy nodeId regions motd }")
	must(len(result.Data.(map[string]any)) == 7, "all seven fields")
	fmt.Println("resolver calls:", ran())
	for _, name := range []string{"name", "version", "uptime", "healthy", "nodeId", "regions", "motd"} {
		must(calls[name] >= 1, "every resolver ran at least once: "+name)
	}

	fmt.Println("\nOK")
}
