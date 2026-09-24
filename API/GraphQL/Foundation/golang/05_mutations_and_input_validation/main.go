/*
FOUNDATION LEVEL 05 - Mutations: changing something, and refusing bad input
==============================================================================
Everything so far only READ. A mutation is how a client changes state. In
REST the verb carried that meaning (GET vs POST/PUT/DELETE, level 06 of
REST/Foundation). GraphQL has no verbs: every request is one HTTP POST, and
what makes an operation a write is that it lives on the `Mutation` type
instead of `Query`. That is a CONVENTION the engine enforces in exactly one
way - mutation fields run one after another, in the order written, while
query fields may run in parallel.

Two kinds of validation show up here, and telling them apart is the point:

 1. SCHEMA validation - "title is required, and must be a String". The
    engine does this against your input type, before your resolver runs.
    You write zero code for it.
 2. BUSINESS validation - "title must not be blank, and must be under 40
    characters". No type system can express that, so your resolver does it
    and returns an error itself.

You will learn
  - how to declare a Mutation type and an input object type (NewInputObject)
  - why writes take a single `input:` object rather than ten loose arguments
  - that missing/wrong-typed input fields are rejected by the schema for free
  - that your own rules live in the resolver, and how to fail clearly from
    there (return nil, errors.New(...))
  - that a mutation returns a normal object type, so the client can select
    fields off the thing it just created - no second round trip

Run it   go run ./GraphQL/Foundation/golang/05_mutations_and_input_validation
*/
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"sort"
	"strings"

	"github.com/graphql-go/graphql"
)

type Post struct {
	ID    string
	Title string
	Body  *string // a pointer, because this one is genuinely nullable
}

var (
	posts  = map[string]Post{}
	nextID = 1
)

func buildSchema() graphql.Schema {
	postType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Post",
		Fields: graphql.Fields{
			"id":    {Type: graphql.NewNonNull(graphql.ID)},
			"title": {Type: graphql.NewNonNull(graphql.String)},
			"body":  {Type: graphql.String},
		},
	})

	// An input object is a SEPARATE kind of type from an output object: it can
	// only contain scalars and other inputs, never fields with resolvers.
	// Grouping the write's fields into one input means adding a field later
	// does not change the mutation's signature for existing clients.
	newPostInput := graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "NewPost",
		Fields: graphql.InputObjectConfigFieldMap{
			"title": {Type: graphql.NewNonNull(graphql.String)}, // required
			"body":  {Type: graphql.String},                     // optional
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"posts": {
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(postType))),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					ids := make([]string, 0, len(posts))
					for id := range posts {
						ids = append(ids, id)
					}
					sort.Strings(ids) // maps are unordered in Go; the demo wants a stable order
					out := make([]Post, 0, len(ids))
					for _, id := range ids {
						out = append(out, posts[id])
					}
					return out, nil
				},
			},
		},
	})

	mutation := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"createPost": {
				// Returning the created object lets the client select fields
				// off it in the same request - REST's "201 + Location, now go
				// GET it" collapsed into one step.
				Type: graphql.NewNonNull(postType),
				Args: graphql.FieldConfigArgument{
					"input": {Type: graphql.NewNonNull(newPostInput)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// By this line the engine has already guaranteed: "input"
					// exists, input.title is present, and it is a string.
					// Everything below is a rule the TYPE SYSTEM CANNOT
					// EXPRESS, so it has to live here.
					input := p.Args["input"].(map[string]any)
					title := strings.TrimSpace(input["title"].(string))
					if title == "" {
						// Returning an error from a resolver is how you report
						// a business rule failure. It lands in errors[] with
						// this field's path.
						return nil, errors.New("title must not be blank")
					}
					if len(title) > 40 {
						return nil, errors.New("title must be 40 characters or fewer")
					}

					post := Post{ID: fmt.Sprintf("p%d", nextID), Title: title}
					if body, ok := input["body"].(string); ok {
						post.Body = &body
					}
					nextID++
					posts[post.ID] = post
					return post, nil
				},
			},
			"deletePost": {
				Type: graphql.NewNonNull(graphql.Boolean),
				Args: graphql.FieldConfigArgument{
					"id": {Type: graphql.NewNonNull(graphql.ID)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					id := p.Args["id"].(string)
					if _, ok := posts[id]; !ok {
						return false, nil
					}
					delete(posts, id)
					return true, nil
				},
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query, Mutation: mutation})
	if err != nil {
		log.Fatal(err)
	}
	return schema
}

func run(schema graphql.Schema, title, query string, vars map[string]any) *graphql.Result {
	result := graphql.Do(graphql.Params{Schema: schema, RequestString: query, VariableValues: vars})
	out, _ := json.Marshal(result)
	fmt.Printf("\n# %s\n", title)
	fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
	if vars != nil {
		varsJSON, _ := json.Marshal(vars)
		fmt.Printf("variables: %s\n", varsJSON)
	}
	fmt.Printf("response : %s\n", out)
	return result
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

const createMutation = `
mutation Create($input: NewPost!) {
  createPost(input: $input) { id title body }
}`

func main() {
	schema := buildSchema()

	fmt.Println("=== the schema, as SDL: note `input NewPost` is its own kind of type ===")
	fmt.Println(`input NewPost {
  title: String!
  body: String
}

type Mutation {
  createPost(input: NewPost!): Post!
  deletePost(id: ID!): Boolean!
}`)

	result := run(schema, "1. a write that succeeds, selecting fields off the new object",
		createMutation, map[string]any{"input": map[string]any{"title": "Hello GraphQL", "body": "first post"}})
	created := result.Data.(map[string]any)["createPost"].(map[string]any)
	must(created["id"] == "p1" && created["title"] == "Hello GraphQL", "created post")

	result = run(schema, "2. it really changed state: query it back", "{ posts { id title } }", nil)
	must(len(result.Data.(map[string]any)["posts"].([]any)) == 1, "one post stored")

	// Kind 1: the schema rejects it. Our resolver never ran.
	before := len(posts)
	result = run(schema, "3. required input field missing -> SCHEMA validation, resolver never runs",
		createMutation, map[string]any{"input": map[string]any{"body": "no title here"}})
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, "title"), "the error names the missing field")
	must(len(posts) == before, "nothing was created")

	result = run(schema, "4. an input field the schema does not have -> same mechanism, same free rejection",
		createMutation, map[string]any{"input": map[string]any{"title": "ok", "nope": 1}})
	must(result.Data == nil && result.HasErrors(), "unknown input field rejected")
	must(len(posts) == before, "nothing was created")

	// Kind 2: schema-valid, but against OUR rules. The resolver must say so.
	result = run(schema, "5. schema-valid but blank -> BUSINESS validation, from inside the resolver",
		createMutation, map[string]any{"input": map[string]any{"title": "   "}})
	// createPost is Post! (non-null), so the null wipes `data` - see level 06.
	must(result.Data == nil, "non-null field failing nulls data")
	must(result.Errors[0].Message == "title must not be blank", "our own message")
	must(fmt.Sprint(result.Errors[0].Path) == "[createPost]", "the error names the field that failed")
	must(len(posts) == before, "nothing was created")
	fmt.Println("   -> the type system can say 'a String is required'; only you can say 'not whitespace'")

	result = run(schema, "6. the other business rule",
		createMutation, map[string]any{"input": map[string]any{"title": strings.Repeat("x", 41)}})
	must(result.Errors[0].Message == "title must be 40 characters or fewer", "length rule")

	// Mutation fields are executed SERIALLY, top to bottom - the reason writes
	// live on their own type at all. Here the delete is guaranteed to happen
	// after the create.
	result = run(schema, "7. two writes in one request run in order, top to bottom",
		`mutation {
		   a: createPost(input: {title: "second"}) { id }
		   removed: deletePost(id: "p1")
		 }`, nil)
	data := result.Data.(map[string]any)
	must(data["a"].(map[string]any)["id"] == "p2" && data["removed"] == true, "serial writes")

	result = run(schema, "8. the state after both writes", "{ posts { id title } }", nil)
	list := result.Data.(map[string]any)["posts"].([]any)
	must(len(list) == 1 && list[0].(map[string]any)["id"] == "p2", "only the second post remains")

	fmt.Println("\nOK")
}
