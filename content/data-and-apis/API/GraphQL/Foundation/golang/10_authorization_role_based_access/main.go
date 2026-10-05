/*
FOUNDATION LEVEL 10 - Authorization: what an identified caller may do
=========================================================================
Level 09 ended on a deliberate cliffhanger: bob, a "viewer", was allowed to
read a secret report just because his token was valid. Authentication had
done its whole job correctly - it only ever claimed to answer "who is this?"

Authorization answers the second, separate question: "may THIS caller do THIS
particular thing?" Two questions, two checks, two failure modes, and mixing
them up is one of the most common security bugs there is:

  - UNAUTHENTICATED (level 09, HTTP's 401): we do not know you. Retrying
    with a credential could work.
  - FORBIDDEN (this level, HTTP's 403): we know exactly who you are, and
    the answer is still no. Retrying changes nothing.

Telling a caller "forbidden" when you meant "unauthenticated" sends them off
to debug the wrong thing; the reverse leaks that the resource exists.

The check itself is boring on purpose - a role comparison. What matters is
WHERE it lives: inside the field's resolver, right before the effect, after
authentication has already put the identity in the context. Not in the
client, not in the middleware, not in the gateway.

You will learn
  - the difference between authentication and authorization, in code
  - extensions.code = "FORBIDDEN" as the 403-equivalent, distinct from 401
  - a role check guarding one destructive mutation, with the other fields of
    the same schema untouched
  - that the deny path must not perform (or half-perform) the effect
  - that the error message names what is needed without leaking data

Run it   go run ./GraphQL/Foundation/golang/10_authorization_role_based_access
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"

	"github.com/graphql-go/graphql"
)

type identity struct {
	User string
	Role string
}

var tokens = map[string]identity{
	"alice-token": {User: "alice", Role: "admin"},
	"bob-token":   {User: "bob", Role: "viewer"},
}

var reports = map[string]string{"r1": "Q1 uptime", "r2": "Q2 uptime"}

type ctxKey string

const userCtxKey ctxKey = "user"

type graphqlError struct {
	message    string
	extensions map[string]any
}

func (e graphqlError) Error() string              { return e.message }
func (e graphqlError) Extensions() map[string]any { return e.extensions }

// ---- the two checks, side by side, so the difference is impossible to miss --

// authenticate is level 09, unchanged: who is this?
func authenticate(ctx context.Context) (identity, error) {
	user, ok := ctx.Value(userCtxKey).(identity)
	if !ok {
		return identity{}, graphqlError{
			message:    "not authenticated",
			extensions: map[string]any{"code": "UNAUTHENTICATED"},
		}
	}
	return user, nil
}

// requireRole is level 10: authentication FIRST (you cannot authorize an
// unknown caller), then the permission itself.
func requireRole(ctx context.Context, role string) (identity, error) {
	user, err := authenticate(ctx)
	if err != nil {
		return identity{}, err
	}
	if user.Role != role {
		return identity{}, graphqlError{
			message: fmt.Sprintf("forbidden: this operation requires the '%s' role", role),
			extensions: map[string]any{
				"code":         "FORBIDDEN",
				"requiredRole": role,
			},
		}
	}
	return user, nil
}

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"reports": {
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(graphql.String))),
				Resolve: func(graphql.ResolveParams) (any, error) {
					titles := make([]string, 0, len(reports))
					for _, title := range reports {
						titles = append(titles, title)
					}
					sort.Strings(titles) // maps are unordered in Go; the demo wants stability
					return titles, nil
				},
			},
			"me": {
				Type: graphql.String,
				Resolve: func(p graphql.ResolveParams) (any, error) {
					user, err := authenticate(p.Context)
					if err != nil {
						return nil, err
					}
					return fmt.Sprintf("%s (%s)", user.User, user.Role), nil
				},
			},
		},
	})

	mutation := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"addReport": {
				// Authenticated, but no role needed: any known caller may add one.
				Type: graphql.String,
				Args: graphql.FieldConfigArgument{
					"title": {Type: graphql.NewNonNull(graphql.String)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					if _, err := authenticate(p.Context); err != nil {
						return nil, err
					}
					id := fmt.Sprintf("r%d", len(reports)+1)
					reports[id] = p.Args["title"].(string)
					return id, nil
				},
			},
			"deleteReport": {
				Type: graphql.Boolean,
				Args: graphql.FieldConfigArgument{
					"id": {Type: graphql.NewNonNull(graphql.ID)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					// The check comes BEFORE the effect. Nothing is read,
					// deleted, or even confirmed to exist until the caller
					// has been cleared.
					if _, err := requireRole(p.Context, "admin"); err != nil {
						return nil, err
					}
					id := p.Args["id"].(string)
					if _, ok := reports[id]; !ok {
						return false, nil
					}
					delete(reports, id)
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

// withAuthentication is level 09's middleware, unchanged.
func withAuthentication(token string) context.Context {
	ctx := context.Background()
	if user, known := tokens[token]; known {
		ctx = context.WithValue(ctx, userCtxKey, user)
	}
	return ctx
}

const deleteMutation = "mutation Delete($id: ID!) { deleteReport(id: $id) }"

func main() {
	schema := buildSchema()

	run := func(title, query, token string, vars map[string]any) *graphql.Result {
		as := token
		if as == "" {
			as = "<anonymous>"
		}
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  query,
			VariableValues: vars,
			Context:        withAuthentication(token),
		})
		out, _ := json.Marshal(result)
		fmt.Printf("\n# %s\n", title)
		fmt.Printf("as       : %s\n", as)
		fmt.Printf("query    : %s\n", strings.Join(strings.Fields(query), " "))
		fmt.Printf("response : %s\n", out)
		return result
	}

	must := func(ok bool, what string) {
		if !ok {
			panic("FAILED: " + what)
		}
	}
	extOf := func(result *graphql.Result, key string) string {
		value, _ := result.Errors[0].Extensions[key].(string)
		return value
	}

	result := run("1. anonymous, a public read: fine", "{ reports }", "", nil)
	must(len(result.Data.(map[string]any)["reports"].([]any)) == 2, "public read")

	// Failure mode A: we do not know you. 401-equivalent.
	result = run("2. anonymous, deleting: UNAUTHENTICATED - we do not know you",
		deleteMutation, "", map[string]any{"id": "r1"})
	must(result.Data.(map[string]any)["deleteReport"] == nil, "not performed")
	must(extOf(result, "code") == "UNAUTHENTICATED", "401-equivalent")
	must(reports["r1"] == "Q1 uptime", "nothing was deleted")

	// Failure mode B: we know you perfectly well. 403-equivalent.
	result = run("3. bob (viewer), deleting: FORBIDDEN - we know you, and it is still no",
		deleteMutation, "bob-token", map[string]any{"id": "r1"})
	must(result.Data.(map[string]any)["deleteReport"] == nil, "not performed")
	must(extOf(result, "code") == "FORBIDDEN", "403-equivalent")
	must(extOf(result, "requiredRole") == "admin", "the error says what is needed")
	must(result.Errors[0].Message == "forbidden: this operation requires the 'admin' role", "clear message")
	must(reports["r1"] == "Q1 uptime", "the deny path must not perform the effect")
	fmt.Println("   -> a DIFFERENT code and a different message from case 2, on purpose:")
	fmt.Println("      bob retrying with a new token forever would never help him")

	// Bob is not powerless - he is a known caller, just not an admin. The
	// permission is per operation, not per user.
	result = run("4. bob, adding a report: allowed - authenticated is enough here",
		`mutation { addReport(title: "Q3 uptime") }`, "bob-token", nil)
	must(result.Data.(map[string]any)["addReport"] == "r3" && !result.HasErrors(), "bob may add")

	result = run("5. alice (admin), deleting: allowed", deleteMutation, "alice-token", map[string]any{"id": "r1"})
	must(result.Data.(map[string]any)["deleteReport"] == true && !result.HasErrors(), "alice may delete")
	_, stillThere := reports["r1"]
	must(!stillThere, "this time it really was deleted")

	// Same caller, same role, same code path - the id simply did not exist.
	// Note this is NOT an authorization failure, and must not look like one.
	result = run("6. alice, deleting something that is not there: false, not an error",
		deleteMutation, "alice-token", map[string]any{"id": "nope"})
	must(result.Data.(map[string]any)["deleteReport"] == false && !result.HasErrors(), "missing id is false")

	result = run("7. the state afterwards", "{ reports }", "", nil)
	titles := result.Data.(map[string]any)["reports"].([]any)
	must(len(titles) == 2 && titles[0] == "Q2 uptime" && titles[1] == "Q3 uptime", "final state")

	fmt.Println("\nOK")
}
