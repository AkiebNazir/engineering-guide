/*
FOUNDATION LEVEL 03 - Variables: one query text, many different inputs
==========================================================================
In level 02 the argument value was baked into the query text: `greet(name:
"Ada")`. Asking about Grace meant building a DIFFERENT string. Variables fix
that: the query text declares typed placeholders (`$name: String!`), and the
actual values travel next to it in VariableValues.

Why this matters, concretely:
  - the query text becomes a constant in your code, not a string you build.
    No quoting, no escaping, no accidental injection of a `"` or a `}`.
  - because the text never changes, it can be cached, logged, whitelisted, or
    registered with the server once by ID (that last one is "persisted
    queries" - see ../labs/, it is exactly this idea taken further).
  - the variable's declared type is checked against the schema, so a wrong
    value is rejected with a clear error before any resolver runs.
  - this is the ONLY way a real client works: {"query": "...", "variables":
    {...}} is the JSON body you will POST in levels 11-13.

Note the named operation: `query Greet($name: String!) { ... }`. Once you
declare variables you need that `query` keyword and (by convention) a name -
which also gives you something useful in logs and traces.

You will learn
  - how to declare variables in a query and pass them separately
  - that the query text is now reusable and cacheable - the interesting
    difference from level 02
  - that variable types are validated against the schema (a missing variable
    and an explicit null for a `!` variable are both caught the same way)
  - that a variable with a default in the query text can be omitted entirely

Run it   go run ./GraphQL/Foundation/golang/03_variables
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/graphql-go/graphql"
)

var users = map[string]string{"1": "Ada", "2": "Grace", "3": "Katherine"}

// ONE constant string, declared once, reused for every caller below. This is
// the shape you want in real code: a package-level constant, never fmt.Sprintf.
const greetQuery = `
query Greet($name: String!, $excited: Boolean = false) {
  greet(name: $name, excited: $excited)
}`

const lookupQuery = `
query Lookup($id: ID!) {
  userName(id: $id)
}`

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"greet": {
				Type: graphql.NewNonNull(graphql.String),
				Args: graphql.FieldConfigArgument{
					"name":    {Type: graphql.NewNonNull(graphql.String)},
					"excited": {Type: graphql.Boolean, DefaultValue: false},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					out := "hello, " + p.Args["name"].(string)
					if excited, _ := p.Args["excited"].(bool); excited {
						out += "!"
					}
					return out, nil
				},
			},
			"userName": {
				Type: graphql.String, // nullable: an unknown id is null, not an error
				Args: graphql.FieldConfigArgument{
					"id": {Type: graphql.NewNonNull(graphql.ID)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					name, ok := users[p.Args["id"].(string)]
					if !ok {
						return nil, nil
					}
					return name, nil
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

func run(schema graphql.Schema, title, query string, vars map[string]any) *graphql.Result {
	// RequestString and VariableValues are two SEPARATE inputs - exactly the
	// two keys of the JSON body a real client posts.
	result := graphql.Do(graphql.Params{
		Schema:         schema,
		RequestString:  query,
		VariableValues: vars,
	})
	out, _ := json.Marshal(result)
	varsJSON, _ := json.Marshal(vars)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
	fmt.Printf("variables: %s\n", varsJSON)
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

	result := run(schema, "1. the query text with a placeholder, values passed beside it",
		greetQuery, map[string]any{"name": "Ada"})
	must(result.Data.(map[string]any)["greet"] == "hello, Ada", "greet with variable")

	// Exactly the same string as above. Only the variables changed - this is
	// the whole lesson.
	result = run(schema, "2. SAME query text, different variables",
		greetQuery, map[string]any{"name": "Grace", "excited": true})
	must(result.Data.(map[string]any)["greet"] == "hello, Grace!", "excited variant")

	// A variable with a default in the query text may be left out entirely.
	result = run(schema, "3. $excited has a default in the query text, so it can be omitted",
		greetQuery, map[string]any{"name": "Katherine"})
	must(result.Data.(map[string]any)["greet"] == "hello, Katherine", "defaulted variable")

	result = run(schema, "4. a non-null variable that was not supplied -> clear error, no resolver runs",
		greetQuery, map[string]any{"excited": true})
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, "$name"), "the error names the variable")

	result = run(schema, "5. an explicit null for a non-null variable -> rejected against the schema",
		greetQuery, map[string]any{"name": nil})
	must(result.Data == nil && result.HasErrors(), "null for String! is rejected")
	fmt.Println("   -> note: implementations differ in how strict they are about coercing a")
	fmt.Println("      number into a String; none of them will accept null for a `!` variable")

	result = run(schema, "6. variables carry data, never syntax: a quote-heavy value is just a value",
		greetQuery, map[string]any{"name": `Bobby "); DROP TABLE users; --`})
	must(result.Data.(map[string]any)["greet"] == `hello, Bobby "); DROP TABLE users; --`, "value stays a value")
	fmt.Println("   -> the value never becomes part of the query document, so it cannot change its meaning")

	result = run(schema, "7. a second reusable query, looking a user up by ID",
		lookupQuery, map[string]any{"id": "2"})
	must(result.Data.(map[string]any)["userName"] == "Grace", "lookup")

	result = run(schema, "8. same text, an ID that does not exist -> null, not an error",
		lookupQuery, map[string]any{"id": "999"})
	must(result.Data.(map[string]any)["userName"] == nil && !result.HasErrors(), "unknown id is null")

	fmt.Println("\nOK")
}
