/*
LAB 01 (basic) - A GraphQL schema built in Go (graphql-go)
==========================================================
You will learn
  - the schema is code here: NewObject / Fields / Args / Resolve (schema-first tools like gqlgen
    generate this from .graphql files - same model, less typing)
  - a resolver is  func(p ResolveParams) (any, error)  and receives:
    p.Source  the parent object     p.Args  the field arguments     p.Context  the request context
  - resolvers run ONLY for requested fields (watch the counters)
  - NonNull, List, Enum, and how nullability changes error behaviour
  - partial results: one failing nullable field does not destroy the rest of the response

Run it   go run ./GraphQL/labs/golang/01_schema_and_resolvers
*/
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"sync/atomic"

	"github.com/graphql-go/graphql"
)

type Author struct {
	ID   int
	Name string
}
type Book struct {
	ID       int
	Title    string
	Year     int
	AuthorID int
	Genre    string
}

var (
	authors = map[int]Author{1: {1, "Ursula Le Guin"}, 2: {2, "Ted Chiang"}}
	books   = []Book{
		{1, "The Dispossessed", 1974, 1, "SCIFI"},
		{2, "A Wizard of Earthsea", 1968, 1, "FANTASY"},
		{3, "Exhalation", 2019, 2, "SCIFI"},
	}
	authorResolverCalls atomic.Int32 // proves resolvers only run when requested
)

func buildSchema() graphql.Schema {
	genre := graphql.NewEnum(graphql.EnumConfig{
		Name: "Genre",
		Values: graphql.EnumValueConfigMap{
			"SCIFI":   {Value: "SCIFI"},
			"FANTASY": {Value: "FANTASY"},
		},
	})

	authorType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Author",
		Fields: graphql.Fields{
			"id":   {Type: graphql.NewNonNull(graphql.Int)},
			"name": {Type: graphql.NewNonNull(graphql.String)},
		},
	})

	// Fields with no Resolve use the DEFAULT resolver: read the same-named field from p.Source.
	bookType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Book",
		Fields: graphql.Fields{
			"id":    {Type: graphql.NewNonNull(graphql.Int)},
			"title": {Type: graphql.NewNonNull(graphql.String)},
			"year":  {Type: graphql.Int},
			"genre": {Type: genre},
			"author": {
				Type: graphql.NewNonNull(authorType),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					authorResolverCalls.Add(1)
					return authors[p.Source.(Book).AuthorID], nil
				},
			},
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"books": {
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(bookType))),
				Args: graphql.FieldConfigArgument{
					"genre":          {Type: genre},
					"publishedAfter": {Type: graphql.Int, Description: "only books published after this year"},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					var out []Book
					for _, b := range books {
						if g, ok := p.Args["genre"].(string); ok && b.Genre != g {
							continue
						}
						if y, ok := p.Args["publishedAfter"].(int); ok && b.Year <= y {
							continue
						}
						out = append(out, b)
					}
					return out, nil
				},
			},
			"book": {
				Type: bookType, // nullable: unknown id -> null
				Args: graphql.FieldConfigArgument{"id": {Type: graphql.NewNonNull(graphql.Int)}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					for _, b := range books {
						if b.ID == p.Args["id"].(int) {
							return b, nil
						}
					}
					return nil, nil
				},
			},
			"flaky": { // nullable + always fails -> partial data
				Type:    graphql.String,
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("upstream timeout") },
			},
			"strict": { // NON-NULL + always fails -> the null bubbles up and wipes `data`
				Type:    graphql.NewNonNull(graphql.String),
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("upstream timeout") },
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		panic(err)
	}
	return schema
}

func run(schema graphql.Schema, title, q string, vars map[string]any) *graphql.Result {
	res := graphql.Do(graphql.Params{Schema: schema, RequestString: q, VariableValues: vars})
	out, _ := json.Marshal(res)
	fmt.Printf("\n# %s\n%s\n-> %s\n", title, q, out)
	return res
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()

	res := run(schema, "1. only ask for what you need", `{ books { title year } }`, nil)
	must(!res.HasErrors() && authorResolverCalls.Load() == 0, "author resolver must not run")
	fmt.Println("author resolver calls:", authorResolverCalls.Load())

	res = run(schema, "2. arguments + nested relationship", `{ books(genre: SCIFI, publishedAfter: 1980) { title author { name } } }`, nil)
	must(len(res.Data.(map[string]any)["books"].([]any)) == 1, "one scifi book after 1980")
	fmt.Println("author resolver calls:", authorResolverCalls.Load())

	res = run(schema, "3. variables", `query ($id: Int!) { book(id: $id) { title genre } }`, map[string]any{"id": 2})
	must(res.Data.(map[string]any)["book"].(map[string]any)["genre"] == "FANTASY", "variables")

	res = run(schema, "4. unknown id -> null, no error", `{ book(id: 99) { title } }`, nil)
	must(!res.HasErrors() && res.Data.(map[string]any)["book"] == nil, "nullable")

	res = run(schema, "5. invalid enum value is a VALIDATION error", `{ books(genre: HORROR) { title } }`, nil)
	must(res.HasErrors() && res.Data == nil, "enum validation")

	res = run(schema, "6a. nullable field fails: partial data", `{ flaky books { title } }`, nil)
	must(res.HasErrors() && res.Data.(map[string]any)["books"] != nil, "partial data")

	res = run(schema, "6b. NON-NULL field fails: data becomes null", `{ strict books { title } }`, nil)
	must(res.HasErrors() && res.Data == nil, "null bubbles")

	res = run(schema, "7. introspection", `{ __type(name: "Book") { fields { name } } }`, nil)
	must(!res.HasErrors(), "introspection")
	fmt.Println("\nOK")
}
