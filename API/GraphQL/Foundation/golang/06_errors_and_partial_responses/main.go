/*
FOUNDATION LEVEL 06 - Errors: why a GraphQL response can be half-successful
===============================================================================
This is the level where GraphQL stops resembling REST at all, so it is worth
slowing down for.

In REST, one request has ONE outcome: a 200 or a 500, success or failure,
never both. In GraphQL one request asks for many fields, each resolved by a
different function, possibly hitting different services. If two fields work
and one fails, "the request" is neither successful nor failed. So the
response carries BOTH: `data` with whatever resolved, and `errors` with a
list of what did not - each entry naming its `path` in the response tree.

The rule that decides how much damage one failure does is nullability:

  - a NULLABLE field (String) that fails becomes null, an entry is added to
    `errors`, and its siblings are untouched -> partial data.
  - a NON-NULL field (String!) that fails cannot be null. So the engine
    nulls its PARENT instead. If the parent is also non-null, it nulls the
    grandparent, and so on. This is "null propagation", and at the top level
    it wipes `data` entirely.

That is why `!` is a promise, not decoration: promise only what cannot fail.

One more thing that trips people up: the HTTP status for all of this is
normally 200. The transport delivered the message fine; the message just
happens to describe failures (levels 11-13 show that literally).

You will learn
  - that `data` and `errors` can both be populated in one response
  - how to read an error's `path` to find which field failed
  - partial data: one nullable field failing does not harm its siblings
  - null propagation: a failing NON-NULL field nulls its parent instead
  - the three distinct failure moments: parse -> validate -> execute, and that
    only execution errors can ever produce partial data

Run it   go run ./GraphQL/Foundation/golang/06_errors_and_partial_responses
*/
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"strings"

	"github.com/graphql-go/graphql"
)

type profile struct {
	Name string
}

func buildSchema() graphql.Schema {
	profileType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Profile",
		Fields: graphql.Fields{
			"name": {Type: graphql.NewNonNull(graphql.String)},
			"avatar": {
				// NULLABLE and failing: becomes null, siblings survive.
				Type:    graphql.String,
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("avatar service timed out") },
			},
			"handle": {
				// NON-NULL and failing: cannot be null, so Profile itself gets nulled.
				Type:    graphql.NewNonNull(graphql.String),
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("handle service timed out") },
			},
		},
	})

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"healthy": {
				Type:    graphql.NewNonNull(graphql.Boolean),
				Resolve: func(graphql.ResolveParams) (any, error) { return true, nil },
			},
			"version": {
				Type:    graphql.NewNonNull(graphql.String),
				Resolve: func(graphql.ResolveParams) (any, error) { return "3.1.0", nil },
			},
			"flaky": {
				Type:    graphql.String, // nullable
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("upstream cache is down") },
			},
			"strict": {
				Type:    graphql.NewNonNull(graphql.String), // non-null
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("upstream cache is down") },
			},
			"profile": {
				Type:    profileType, // nullable, so propagation can stop here
				Resolve: func(graphql.ResolveParams) (any, error) { return profile{Name: "Ada"}, nil },
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
	fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
	fmt.Printf("response : %s\n", out)
	return result
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// paths collects every error's path, so the demo can assert on them.
func paths(result *graphql.Result) []string {
	out := []string{}
	for _, e := range result.Errors {
		parts := make([]string, 0, len(e.Path))
		for _, p := range e.Path {
			parts = append(parts, fmt.Sprint(p))
		}
		out = append(out, strings.Join(parts, "."))
	}
	return out
}

func main() {
	schema := buildSchema()

	// ---- failure moment 1: PARSE. The text is not a GraphQL document. ----
	result := run(schema, "1. a syntax error: nothing is even understood, let alone run", "{ healthy ")
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, "Syntax Error"), "syntax error")

	// ---- failure moment 2: VALIDATE. Valid text, but it contradicts the schema. ----
	result = run(schema, "2. a validation error: understood, but not allowed by the schema", "{ healthy nope }")
	must(result.Data == nil, "data is null")
	must(strings.Contains(result.Errors[0].Message, `Cannot query field "nope"`), "validation error")
	fmt.Println("   -> parse and validate errors are all-or-nothing: `data` is null, no resolver ran")

	// ---- failure moment 3: EXECUTE. This is the only one that can be partial. ----
	result = run(schema, "3. THE INTERESTING ONE: a nullable field fails, its siblings do not care",
		"{ healthy version flaky }")
	data := result.Data.(map[string]any)
	must(data["healthy"] == true && data["version"] == "3.1.0" && data["flaky"] == nil, "partial data")
	must(fmt.Sprint(paths(result)) == "[flaky]", "the error names flaky")
	fmt.Println("   -> data AND errors, together. `healthy` and `version` are real answers.")
	fmt.Println("   -> a REST client would have seen one 500 and thrown the good data away")

	result = run(schema, "4. the same failure on a NON-NULL field: the null bubbles up and wipes data",
		"{ healthy version strict }")
	must(result.Data == nil, "data is wiped")
	must(fmt.Sprint(paths(result)) == "[strict]", "the error names strict")
	fmt.Println("   -> `strict: String!` promised a value; the only place to put the null was `data` itself")

	// Nested: the propagation stops at the first nullable ancestor.
	result = run(schema, "5. nested, nullable child: only that leaf is lost", "{ profile { name avatar } }")
	prof := result.Data.(map[string]any)["profile"].(map[string]any)
	must(prof["name"] == "Ada" && prof["avatar"] == nil, "only the leaf is null")
	must(fmt.Sprint(paths(result)) == "[profile.avatar]", "the path says exactly where")
	fmt.Println("   -> the path says exactly where: profile.avatar")

	result = run(schema, "6. nested, NON-NULL child: the whole parent object is nulled instead",
		"{ healthy profile { name handle } }")
	data = result.Data.(map[string]any)
	must(data["healthy"] == true && data["profile"] == nil, "the parent was nulled, healthy survived")
	must(fmt.Sprint(paths(result)) == "[profile.handle]", "path")
	fmt.Println("   -> `profile` is nullable, so the damage stopped there: `healthy` still answered")

	// Several failures, several errors: the list is not capped at one.
	result = run(schema, "7. two independent failures -> two entries in errors", "{ flaky profile { avatar } }")
	must(len(result.Errors) == 2, "two errors")
	got := paths(result)
	must((got[0] == "flaky" && got[1] == "profile.avatar") || (got[0] == "profile.avatar" && got[1] == "flaky"),
		"both paths reported")
	fmt.Println("   -> every failing field reports itself; the client decides what is fatal")

	fmt.Println("\nOK")
}
