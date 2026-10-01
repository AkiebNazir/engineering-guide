/*
FOUNDATION LEVEL 02 - Field arguments: fields that take input
=================================================================
So far every field returned a constant. Arguments make a field a FUNCTION:
`greet(name: "Ada")` instead of just `greet`. In REST you would express this
as a path parameter (/greet/Ada) or a query string (/greet?name=Ada), and you
would parse and validate it yourself. Here the argument is part of the schema,
so the engine parses, type-checks, and rejects bad input for you before your
resolver is ever called.

Arguments belong to a FIELD, not to the request. Two fields in the same query
can each take their own, and a nested field deep in the tree can take
arguments too (level 04).

You will learn
  - how to declare an argument (FieldConfigArgument) and read it from p.Args
  - required (`String!`) vs optional-with-a-default (DefaultValue) arguments
  - that a missing required argument is a VALIDATION error: caught against the
    schema before any resolver runs, so your resolver never sees bad input
  - that a wrong-typed argument (Int given a string) is rejected the same way
  - that arguments are typed data, not string interpolation - which is why
    GraphQL has no equivalent of SQL-style query-string injection

Run it   go run ./GraphQL/Foundation/golang/02_field_arguments
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"strings"

	"github.com/graphql-go/graphql"
)

var resolverRan = map[string]int{}

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"greet": {
				Type: graphql.NewNonNull(graphql.String),
				// NewNonNull on the ARGUMENT's type makes it required:
				//   greet(name: String!): String!
				Args: graphql.FieldConfigArgument{
					"name": {Type: graphql.NewNonNull(graphql.String)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					resolverRan["greet"]++
					// By the time this line runs the engine has guaranteed:
					// "name" is present, and it is a string. We check neither.
					return "hello, " + p.Args["name"].(string), nil
				},
			},
			"power": {
				Type: graphql.NewNonNull(graphql.Int),
				// DefaultValue makes an argument optional, and - crucially -
				// publishes the default in the contract, so every client sees
				// it instead of having to read your docs. Note `exp` is
				// declared NULLABLE (no NewNonNull): graphql-go treats any
				// non-null argument as "must be written out", default or not.
				Args: graphql.FieldConfigArgument{
					"base": {Type: graphql.NewNonNull(graphql.Int)},
					"exp":  {Type: graphql.Int, DefaultValue: 2},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					resolverRan["power"]++
					base := p.Args["base"].(int)
					exp := p.Args["exp"].(int)
					return int(math.Pow(float64(base), float64(exp))), nil
				},
			},
			"shout": {
				Type: graphql.NewNonNull(graphql.String),
				Args: graphql.FieldConfigArgument{
					"text": {Type: graphql.NewNonNull(graphql.String)},
					// No NewNonNull and no default: a nullable, optional
					// argument. The client may omit it or pass null, and both
					// mean "nothing here" - which arrives as a missing key.
					"suffix": {Type: graphql.String},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					out := strings.ToUpper(p.Args["text"].(string))
					if suffix, ok := p.Args["suffix"].(string); ok {
						out += suffix
					}
					return out, nil
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

func run(schema graphql.Schema, title, query string) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query})
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
	schema := buildSchema()

	fmt.Println("=== the schema, as SDL: arguments are part of the contract ===")
	fmt.Println(`type Query {
  greet(name: String!): String!
  power(base: Int!, exp: Int = 2): Int!
  shout(text: String!, suffix: String): String!
}`)

	result := run(schema, "1. a field that takes an argument", `{ greet(name: "Ada") }`)
	must(result.Data.(map[string]any)["greet"] == "hello, Ada", "greet")

	// Same field, called twice in one query with different arguments. Aliases
	// (`en:` / `other:`) are needed because both results are keys in one object.
	result = run(schema, "2. the same field twice, with different arguments (aliases)",
		`{ en: greet(name: "Ada")  other: greet(name: "Grace") }`)
	data := result.Data.(map[string]any)
	must(data["en"] == "hello, Ada" && data["other"] == "hello, Grace", "aliases")

	result = run(schema, "3. an optional argument, left out -> the schema's default (exp = 2)", "{ power(base: 5) }")
	must(result.Data.(map[string]any)["power"] == 25, "default exp")

	result = run(schema, "4. the same field, default overridden", "{ power(base: 2, exp: 10) }")
	must(result.Data.(map[string]any)["power"] == 1024, "explicit exp")

	// The interesting part: bad input never reaches the resolver.
	before := resolverRan["greet"]
	result = run(schema, "5. a REQUIRED argument left out -> validation error, resolver never runs", "{ greet }")
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, `argument "name" of type "String!" is required`), "required arg message")
	must(resolverRan["greet"] == before, "the resolver must not have been called")
	fmt.Println("   -> compare REST, where an empty ?name= arrives as your problem to handle")

	result = run(schema, "6. a wrong-TYPED argument -> rejected the same way", `{ power(base: "five") }`)
	must(result.Data == nil && result.HasErrors(), "type mismatch is rejected")

	result = run(schema, "7. an optional nullable argument, omitted and then given",
		`{ plain: shout(text: "hi")  loud: shout(text: "hi", suffix: "!!!") }`)
	data = result.Data.(map[string]any)
	must(data["plain"] == "HI" && data["loud"] == "HI!!!", "optional suffix")

	fmt.Println("\nOK")
}
