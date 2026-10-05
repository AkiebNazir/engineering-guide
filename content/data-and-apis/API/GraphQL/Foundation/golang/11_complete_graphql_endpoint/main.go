/*
FOUNDATION LEVEL 11 - CAPSTONE: the whole thing, behind one real HTTP endpoint
=================================================================================
No new GraphQL ideas here. This is levels 00-10 assembled - schema, arguments,
variables, nested types, a mutation, partial errors, context, middleware,
authentication, authorization - plus the one piece that was deliberately
missing all along: a real network endpoint in front of the engine.

That piece is smaller than you expect, which is the last lesson of Foundation:

	ONE url            POST /graphql            (no route per resource)
	ONE method         POST                     (no verb vocabulary)
	request body       {"query": "...", "variables": {...}}
	response body      {"data": ..., "errors": [...]}
	status             200, even when `errors` is populated

Everything a REST API expresses in URLs and status codes, GraphQL expresses
inside that one body. The HTTP layer here has one job: turn bytes into
{query, variables}, build the context from the request (crucially, the
Authorization header), call the engine, write JSON back. It contains no
business logic at all - and level 13 shows those bytes with nothing but a TCP
socket, to prove there is no magic left.

Status codes that DO still apply, because they are about the transport rather
than the query: 404 for the wrong path, 405 for the wrong method, 400 for a
body that is not even JSON. Once the body parses, GraphQL takes over.

You will learn
  - the exact HTTP contract of a GraphQL endpoint - all four lines of it
  - where the context comes from in a real request (headers, not thin air)
  - that authentication/authorization live in the schema, not in the router
  - why a field-level failure is still HTTP 200, and what that means for clients
  - that this file is a complete, protected, real GraphQL service

Run it         go run ./GraphQL/Foundation/golang/11_complete_graphql_endpoint
Keep serving   go run ./GraphQL/Foundation/golang/11_complete_graphql_endpoint -serve   (curl -s localhost:8080/graphql -H 'Authorization: Bearer alice-token' -d '{"query":"{ reports { id title } }"}')
*/
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"sort"
	"strings"
	"time"

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

type reportRow struct {
	ID    string
	Title string
	Owner string
}

var (
	reports = map[string]reportRow{
		"r1": {ID: "r1", Title: "Q1 uptime", Owner: "alice"},
		"r2": {ID: "r2", Title: "Q2 uptime", Owner: "bob"},
	}
	nextID = 3
)

type ctxKey string

const (
	userCtxKey      ctxKey = "user"
	requestIDCtxKey ctxKey = "requestID"
)

type graphqlError struct {
	message    string
	extensions map[string]any
}

func (e graphqlError) Error() string              { return e.message }
func (e graphqlError) Extensions() map[string]any { return e.extensions }

// ---- the two checks from levels 09 and 10, unchanged ----------------------
func authenticate(ctx context.Context) (identity, error) {
	user, ok := ctx.Value(userCtxKey).(identity)
	if !ok {
		return identity{}, graphqlError{"not authenticated", map[string]any{"code": "UNAUTHENTICATED"}}
	}
	return user, nil
}

func requireRole(ctx context.Context, role string) (identity, error) {
	user, err := authenticate(ctx)
	if err != nil {
		return identity{}, err
	}
	if user.Role != role {
		return identity{}, graphqlError{
			fmt.Sprintf("forbidden: this operation requires the '%s' role", role),
			map[string]any{"code": "FORBIDDEN", "requiredRole": role},
		}
	}
	return user, nil
}

// ---- the schema: levels 01-06 --------------------------------------------
func buildSchema() graphql.Schema {
	ownerType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Owner",
		Fields: graphql.Fields{
			"name": {Type: graphql.NewNonNull(graphql.String)},
			"role": {Type: graphql.NewNonNull(graphql.String)},
		},
	})

	reportType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Report",
		Fields: graphql.Fields{
			"id":    {Type: graphql.NewNonNull(graphql.ID)},
			"title": {Type: graphql.NewNonNull(graphql.String)},
			"owner": {
				// Level 04's resolver chain: p.Source is the parent report.
				Type: graphql.NewNonNull(ownerType),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					name := p.Source.(reportRow).Owner
					role := "unknown"
					if user, ok := tokens[name+"-token"]; ok {
						role = user.Role
					}
					return struct {
						Name string
						Role string
					}{name, role}, nil
				},
			},
		},
	})

	newReportInput := graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "NewReport",
		Fields: graphql.InputObjectConfigFieldMap{
			"title": {Type: graphql.NewNonNull(graphql.String)},
		},
	})

	sortedReports := func() []reportRow {
		ids := make([]string, 0, len(reports))
		for id := range reports {
			ids = append(ids, id)
		}
		sort.Strings(ids)
		out := make([]reportRow, 0, len(ids))
		for _, id := range ids {
			out = append(out, reports[id])
		}
		return out
	}

	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"reports": {
				// Public: no token needed (level 09 - the check is per field).
				Type:    graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(reportType))),
				Resolve: func(graphql.ResolveParams) (any, error) { return sortedReports(), nil },
			},
			"report": {
				Type: reportType,
				Args: graphql.FieldConfigArgument{"id": {Type: graphql.NewNonNull(graphql.ID)}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					row, ok := reports[p.Args["id"].(string)]
					if !ok {
						return nil, nil
					}
					return row, nil
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
			"requestId": {
				// Level 07: comes from the context, which the HTTP layer built.
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (any, error) {
					id, _ := p.Context.Value(requestIDCtxKey).(string)
					return id, nil
				},
			},
		},
	})

	mutation := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"createReport": {
				Type: reportType,
				Args: graphql.FieldConfigArgument{
					"input": {Type: graphql.NewNonNull(newReportInput)},
				},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					user, err := authenticate(p.Context) // level 09
					if err != nil {
						return nil, err
					}
					input := p.Args["input"].(map[string]any)
					title := strings.TrimSpace(input["title"].(string))
					if title == "" { // level 05's business rule
						return nil, graphqlError{"title must not be blank",
							map[string]any{"code": "BAD_USER_INPUT"}}
					}
					row := reportRow{ID: fmt.Sprintf("r%d", nextID), Title: title, Owner: user.User}
					nextID++
					reports[row.ID] = row
					return row, nil
				},
			},
			"deleteReport": {
				Type: graphql.Boolean,
				Args: graphql.FieldConfigArgument{"id": {Type: graphql.NewNonNull(graphql.ID)}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					if _, err := requireRole(p.Context, "admin"); err != nil { // level 10
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

// ---- the HTTP layer: the only genuinely new code in this file -------------
type graphqlRequest struct {
	Query         string         `json:"query"`
	Variables     map[string]any `json:"variables"`
	OperationName string         `json:"operationName"`
}

func sendJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(payload)
}

func graphqlHandler(schema graphql.Schema) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Transport-level failures still deserve real status codes: this one
		// is not about the query, it is about the request never reaching it.
		if r.Method != http.MethodPost {
			sendJSON(w, http.StatusMethodNotAllowed, map[string]any{
				"errors": []map[string]string{{"message": "use POST /graphql"}}})
			return
		}

		var req graphqlRequest
		body, _ := io.ReadAll(r.Body)
		if err := json.Unmarshal(body, &req); err != nil || strings.TrimSpace(req.Query) == "" {
			// Not even a GraphQL request yet, so answer in HTTP's own terms.
			sendJSON(w, http.StatusBadRequest, map[string]any{
				"errors": []map[string]string{{"message": `body must be JSON with a "query" key`}}})
			return
		}

		// THE CONTEXT (level 07), built from this request and nothing else.
		// Note it starts from r.Context(), so a client disconnecting cancels
		// the resolvers too. This is where the Authorization header (level 09)
		// enters the schema.
		ctx := r.Context()
		var who string
		if token, ok := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer "); ok {
			if user, known := tokens[token]; known {
				ctx = context.WithValue(ctx, userCtxKey, user)
				who = user.User
			}
		}
		if who == "" {
			who = "-"
		}
		ctx = context.WithValue(ctx, requestIDCtxKey, fmt.Sprintf("req-%d", time.Now().UnixMilli()%100000))

		// Level 08's middleware, doing its two jobs around the engine.
		defer func() {
			if rec := recover(); rec != nil { // our own bugs, never the client's to read
				fmt.Printf("  [recovery] %v\n", rec)
				sendJSON(w, http.StatusInternalServerError, map[string]any{
					"errors": []map[string]string{{"message": "internal server error"}}})
			}
		}()

		started := time.Now()
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			VariableValues: req.Variables,
			OperationName:  req.OperationName,
			Context:        ctx,
		})
		fmt.Printf("  [log] POST /graphql user=%s errors=%d %.1fms\n",
			who, len(result.Errors), float64(time.Since(started).Microseconds())/1000)

		// 200 even with errors: the transport succeeded, the message reports
		// what happened inside it. Clients MUST read `errors`, not the status.
		sendJSON(w, http.StatusOK, result)
	}
}

// ---- the client side of the demo ----------------------------------------
type callResult struct {
	Status  int
	Data    map[string]any
	Errors  []map[string]any
	RawBody string
}

func post(base, path, method, query string, vars map[string]any, token string) callResult {
	payload, _ := json.Marshal(graphqlRequest{Query: query, Variables: vars})
	req, err := http.NewRequest(method, base+path, bytes.NewReader(payload))
	if err != nil {
		log.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	raw, _ := io.ReadAll(res.Body)

	var parsed struct {
		Data   map[string]any   `json:"data"`
		Errors []map[string]any `json:"errors"`
	}
	json.Unmarshal(raw, &parsed)
	return callResult{Status: res.StatusCode, Data: parsed.Data, Errors: parsed.Errors,
		RawBody: strings.TrimSpace(string(raw))}
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func codeOf(res callResult) string {
	if len(res.Errors) == 0 {
		return ""
	}
	ext, _ := res.Errors[0]["extensions"].(map[string]any)
	code, _ := ext["code"].(string)
	return code
}

func main() {
	serve := flag.Bool("serve", false, "keep serving on :8080 instead of running the demo")
	flag.Parse()

	schema := buildSchema()
	mux := http.NewServeMux()
	mux.HandleFunc("/graphql", graphqlHandler(schema)) // ONE path, and only one

	if *serve {
		log.Println("listening on http://localhost:8080/graphql")
		log.Println(`try: curl -s localhost:8080/graphql -d '{"query":"{ reports { id title } }"}'`)
		log.Println(`     curl -s localhost:8080/graphql -H 'Authorization: Bearer alice-token' \`)
		log.Println(`       -d '{"query":"mutation($id:ID!){ deleteReport(id:$id) }","variables":{"id":"r1"}}'`)
		log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
	}

	// port 0 = "operating system, hand me any free port", so this demo never
	// collides with anything already listening on 8080.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String()

	run := func(title, query string, vars map[string]any, token, path, method string) callResult {
		res := post(base, path, method, query, vars, token)
		as := token
		if as == "" {
			as = "<anonymous>"
		}
		varsJSON, _ := json.Marshal(vars)
		fmt.Printf("\n# %s\n", title)
		fmt.Printf("%s %s as %s\n", method, path, as)
		fmt.Printf("body     : {\"query\": %q, \"variables\": %s}\n", strings.Join(strings.Fields(query), " "), varsJSON)
		fmt.Printf("-> HTTP %d %s\n", res.Status, res.RawBody)
		return res
	}

	res := run("1. a public query over real HTTP", "{ reports { id title owner { name role } } }", nil, "", "/graphql", "POST")
	must(res.Status == 200, "HTTP 200")
	list := res.Data["reports"].([]any)
	must(len(list) == 2, "two reports")
	owner := list[0].(map[string]any)["owner"].(map[string]any)
	must(owner["name"] == "alice" && owner["role"] == "admin", "nested owner")

	res = run("2. context built from the request: a server-side request id", "{ requestId }", nil, "", "/graphql", "POST")
	must(strings.HasPrefix(res.Data["requestId"].(string), "req-"), "request id from context")

	res = run("3. a protected field, anonymous -> HTTP 200 + UNAUTHENTICATED", "{ reports { id } me }", nil, "", "/graphql", "POST")
	must(res.Status == 200, "the transport worked perfectly; only the field failed")
	must(res.Data["me"] == nil && len(res.Data["reports"].([]any)) == 2, "partial data")
	must(codeOf(res) == "UNAUTHENTICATED", "401-equivalent")
	fmt.Println("   -> a client checking only the status code would call this a success. Read `errors`.")

	res = run("4. the same query with a token", "{ me }", nil, "bob-token", "/graphql", "POST")
	must(res.Data["me"] == "bob (viewer)", "authenticated read")

	const createMutation = `mutation Create($input: NewReport!) { createReport(input: $input) { id title owner { name } } }`
	res = run("5. an authenticated mutation, as bob", createMutation,
		map[string]any{"input": map[string]any{"title": "Q3 uptime"}}, "bob-token", "/graphql", "POST")
	created := res.Data["createReport"].(map[string]any)
	must(created["id"] == "r3", "created r3")
	must(created["owner"].(map[string]any)["name"] == "bob", "owned by its creator")

	res = run("6. the same mutation with blank input -> BAD_USER_INPUT", createMutation,
		map[string]any{"input": map[string]any{"title": "   "}}, "bob-token", "/graphql", "POST")
	must(codeOf(res) == "BAD_USER_INPUT", "business rule violated")

	const deleteMutation = `mutation Delete($id: ID!) { deleteReport(id: $id) }`
	res = run("7. an admin-only mutation, as bob (viewer) -> FORBIDDEN", deleteMutation,
		map[string]any{"id": "r1"}, "bob-token", "/graphql", "POST")
	must(codeOf(res) == "FORBIDDEN", "403-equivalent")

	res = run("8. the same mutation as alice (admin) -> allowed", deleteMutation,
		map[string]any{"id": "r1"}, "alice-token", "/graphql", "POST")
	must(res.Data["deleteReport"] == true, "deleted")

	res = run("9. and the state changed", "{ reports { id title } }", nil, "", "/graphql", "POST")
	list = res.Data["reports"].([]any)
	must(len(list) == 2, "two reports remain")
	must(list[0].(map[string]any)["id"] == "r2" && list[1].(map[string]any)["id"] == "r3", "r1 is gone")

	// Transport-level failures: these are NOT GraphQL's business.
	res = run("10. wrong path -> a real 404 (not a GraphQL error)", "{ reports { id } }", nil, "", "/api/reports", "POST")
	must(res.Status == 404, "404 from the router, before GraphQL is involved")

	res = run("11. wrong method -> a real 405", "{ reports { id } }", nil, "", "/graphql", "GET")
	must(res.Status == 405, "405")

	fmt.Println("\n# 12. a body that is not JSON -> a real 400")
	badRequest, _ := http.NewRequest("POST", base+"/graphql", strings.NewReader("this is not json"))
	badResponse, err := http.DefaultClient.Do(badRequest)
	if err != nil {
		log.Fatal(err)
	}
	badBody, _ := io.ReadAll(badResponse.Body)
	badResponse.Body.Close()
	fmt.Printf("-> HTTP %d %s\n", badResponse.StatusCode, strings.TrimSpace(string(badBody)))
	must(badResponse.StatusCode == 400, "400")
	fmt.Println("   -> once the body parses, every other outcome is 200 + {data, errors}")

	fmt.Println("\nOK")
}
