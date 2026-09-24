/*
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Middleware (level 08) is the mechanism and context (level 07) is the carrier;
authentication is the first real thing to put in them. It answers exactly ONE
question: "do we recognize this caller at all?" It says NOTHING about what
that caller may do - that is level 10, authorization, and keeping the two
apart is the whole reason they are separate levels.

The shape, which never changes in real systems:

 1. the transport hands you a credential - by convention the HTTP header
    `Authorization: Bearer <token>` (level 11 reads it off a real request;
    here we pass it in beside the query, because there is no HTTP yet)
 2. middleware resolves it into an identity ONCE, before execution
 3. it puts that identity (or nothing) in the context
 4. a protected field's resolver checks the context and refuses if absent

There is no 401 to send: GraphQL has no per-field status codes, and the HTTP
response - when there is one - is a 200 carrying `errors` (level 06). The
community convention that replaces the status code is an `extensions.code` on
the error, and `UNAUTHENTICATED` is the agreed name for this one.

Note where the check lives: in the FIELD, not in the middleware. One request
may mix public and protected fields, and rejecting the whole request because
one field needed a token would be wrong. Level 06's partial responses are
exactly what makes this work.

You will learn
  - the `Authorization: Bearer <token>` convention, and resolving it once
  - that authentication middleware IDENTIFIES but does not reject - the
    protected field decides
  - errors[].extensions.code = "UNAUTHENTICATED" as GraphQL's 401-equivalent,
    which in graphql-go means returning an error with an Extensions() method
  - that a missing and an INVALID token are the same outcome, on purpose: never
    tell an attacker which half of the guess was right
  - that public fields in the same request still return real data

Run it   go run ./GraphQL/Foundation/golang/09_authentication_bearer_tokens
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/graphql-go/graphql"
)

type identity struct {
	User string
	Role string
}

// A stand-in for "who is allowed in". A real service verifies a signed JWT or
// looks the token up in a store - see ../labs/golang. The SHAPE of everything
// below is identical either way.
var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

type ctxKey string

const userCtxKey ctxKey = "user"

// graphqlError is an error that also carries `extensions`. graphql-go copies
// the map into the response when a resolver returns one of these, which is
// how a GraphQL API expresses "this is the 401 kind of failure".
type graphqlError struct {
	message    string
	extensions map[string]any
}

func (e graphqlError) Error() string              { return e.message }
func (e graphqlError) Extensions() map[string]any { return e.extensions }
func unauthenticated() error {
	// One deliberately vague message for both "no token" and "bad token".
	return graphqlError{message: "not authenticated", extensions: map[string]any{"code": "UNAUTHENTICATED"}}
}

// currentUser is used by every protected resolver: either it returns the
// identity that authentication middleware put in the context, or it refuses.
func currentUser(ctx context.Context) (identity, error) {
	user, ok := ctx.Value(userCtxKey).(identity)
	if !ok {
		return identity{}, unauthenticated()
	}
	return user, nil
}

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"publicNotice": {
				// No check at all: anyone may read this, token or not.
				Type:    graphql.NewNonNull(graphql.String),
				Resolve: func(graphql.ResolveParams) (any, error) { return "the service is up", nil },
			},
			"me": {
				Type: graphql.String, // nullable, so one failure does not wipe the response
				Resolve: func(p graphql.ResolveParams) (any, error) {
					user, err := currentUser(p.Context)
					if err != nil {
						return nil, err
					}
					return fmt.Sprintf("%s (%s)", user.User, user.Role), nil
				},
			},
			"secretReport": {
				Type: graphql.String,
				Resolve: func(p graphql.ResolveParams) (any, error) {
					user, err := currentUser(p.Context)
					if err != nil {
						return nil, err
					}
					return "revenue is fine, " + user.User, nil
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

type request struct {
	Query   string
	Headers map[string]string
}

type execute func(request) *graphql.Result

// ---- the authentication middleware -------------------------------------
// It runs once per request, BEFORE execution. It resolves the credential and
// records the result - it never rejects, because it cannot know whether the
// query even touches a protected field.
func withAuthentication(next func(request, context.Context) *graphql.Result) execute {
	return func(req request) *graphql.Result {
		ctx := context.Background()
		header := req.Headers["Authorization"]
		note := "anonymous"
		if token, ok := strings.CutPrefix(header, "Bearer "); ok {
			if user, known := tokens[token]; known { // unknown token -> still anonymous
				ctx = context.WithValue(ctx, userCtxKey, user)
				note = "identified as " + user.User
			}
		}
		if header == "" {
			header = "<none>"
		}
		fmt.Printf("  [auth] Authorization: %-26s -> %s\n", header, note)
		return next(req, ctx)
	}
}

func main() {
	schema := buildSchema()

	runQuery := func(req request, ctx context.Context) *graphql.Result {
		return graphql.Do(graphql.Params{Schema: schema, RequestString: req.Query, Context: ctx})
	}
	execute := withAuthentication(runQuery)

	run := func(title, query, token string) *graphql.Result {
		headers := map[string]string{}
		if token != "" {
			headers["Authorization"] = "Bearer " + token
		}
		fmt.Printf("\n# %s\n", title)
		fmt.Printf("query    : %s\n", query)
		result := execute(request{Query: query, Headers: headers})
		out, _ := json.Marshal(result)
		fmt.Printf("response : %s\n", out)
		return result
	}

	must := func(ok bool, what string) {
		if !ok {
			panic("FAILED: " + what)
		}
	}
	codeOf := func(result *graphql.Result, i int) string {
		code, _ := result.Errors[i].Extensions["code"].(string)
		return code
	}

	result := run("1. a public field needs nothing", "{ publicNotice }", "")
	must(result.Data.(map[string]any)["publicNotice"] == "the service is up", "public field")
	must(!result.HasErrors(), "no errors")

	result = run("2. a protected field with NO token -> UNAUTHENTICATED", "{ me }", "")
	must(result.Data.(map[string]any)["me"] == nil, "me is null")
	must(result.Errors[0].Message == "not authenticated", "vague message")
	must(codeOf(result, 0) == "UNAUTHENTICATED", "the 401-equivalent code")
	fmt.Println("   -> there is no HTTP status here to set; the error IS the 401")

	result = run("3. a token that is not recognized -> the SAME answer, deliberately", "{ me }", "not-a-real-token")
	must(result.Data.(map[string]any)["me"] == nil, "me is null")
	must(codeOf(result, 0) == "UNAUTHENTICATED", "same code as a missing token")
	fmt.Println("   -> 'no token' and 'wrong token' must be indistinguishable to the caller")

	result = run("4. a valid token -> the field resolves", "{ me }", "alice-token")
	must(result.Data.(map[string]any)["me"] == "alice (admin)" && !result.HasErrors(), "alice")

	result = run("5. a different valid token -> a different identity, same code", "{ me secretReport }", "bob-token")
	data := result.Data.(map[string]any)
	must(data["me"] == "bob (viewer)" && data["secretReport"] == "revenue is fine, bob", "bob")
	fmt.Println("   -> note bob, a 'viewer', could read the secret report. Nothing so far stops him.")
	fmt.Println("      That is level 10's job: authentication is not authorization.")

	// The partial-response rule from level 06 is what makes per-field auth usable.
	result = run("6. one request mixing public and protected fields, unauthenticated",
		"{ publicNotice me secretReport }", "")
	data = result.Data.(map[string]any)
	must(data["publicNotice"] == "the service is up", "the public field still answered")
	must(data["me"] == nil && data["secretReport"] == nil, "both protected fields are null")
	must(len(result.Errors) == 2, "one error per protected field")
	fmt.Println("   -> the public field still answered. Rejecting the whole request would have been wrong.")

	fmt.Println("\nOK")
}
