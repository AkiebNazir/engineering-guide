/*
LAB 02 (basic) - Serving GraphQL over net/http
==============================================
You will learn
  - what a GraphQL HTTP request really is:  ONE JSON body with three keys
    { "query": "...", "variables": {...}, "operationName": "..." }
  - operationName: choosing ONE operation out of a document that contains several
  - the status-code contract:
    malformed request / wrong content    -> 4xx   (the request never reached GraphQL)
    parsed but a field failed            -> 200 + {"errors":[...]}
  - GET works for queries (cacheable!) but must NEVER run mutations
  - carrying HTTP context into resolvers: middleware puts the caller in r.Context(),
    graphql.Params{Context: r.Context()} hands it to every resolver
  - bounding the request body

Run it   go run ./GraphQL/labs/golang/02_http_handler_and_variables
*/
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"

	"github.com/graphql-go/graphql"
	"github.com/graphql-go/graphql/language/ast"
	"github.com/graphql-go/graphql/language/parser"
)

// ---------------------------------------------------------------- schema ----
type ctxKey struct{}

func viewer(ctx context.Context) string { s, _ := ctx.Value(ctxKey{}).(string); return s }

var (
	mu      sync.Mutex
	counter int
)

func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: graphql.Fields{
		"hello": {
			Type: graphql.String,
			Args: graphql.FieldConfigArgument{"name": {Type: graphql.String, DefaultValue: "world"}},
			Resolve: func(p graphql.ResolveParams) (any, error) {
				return fmt.Sprintf("hello %s (asked by %q)", p.Args["name"], viewer(p.Context)), nil
			},
		},
		"counter": {Type: graphql.Int, Resolve: func(graphql.ResolveParams) (any, error) { mu.Lock(); defer mu.Unlock(); return counter, nil }},
	}})
	mutation := graphql.NewObject(graphql.ObjectConfig{Name: "Mutation", Fields: graphql.Fields{
		"increment": {Type: graphql.Int, Resolve: func(graphql.ResolveParams) (any, error) { mu.Lock(); defer mu.Unlock(); counter++; return counter, nil }},
	}})
	s, err := graphql.NewSchema(graphql.SchemaConfig{Query: query, Mutation: mutation})
	if err != nil {
		panic(err)
	}
	return s
}

// ---------------------------------------------------------------- handler ---
type gqlRequest struct {
	Query         string         `json:"query"`
	Variables     map[string]any `json:"variables"`
	OperationName string         `json:"operationName"`
}

func Handler(schema graphql.Schema) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req gqlRequest
		switch r.Method {
		case http.MethodPost:
			r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, `{"errors":[{"message":"body must be JSON with a \"query\" key"}]}`, http.StatusBadRequest)
				return
			}
		case http.MethodGet: // GET is cacheable and link-able, so it must be SAFE: queries only
			req.Query, req.OperationName = r.URL.Query().Get("query"), r.URL.Query().Get("operationName")
			if v := r.URL.Query().Get("variables"); v != "" {
				json.Unmarshal([]byte(v), &req.Variables)
			}
			if isMutation(req.Query, req.OperationName) {
				w.Header().Set("Allow", "POST")
				http.Error(w, `{"errors":[{"message":"mutations must use POST"}]}`, http.StatusMethodNotAllowed)
				return
			}
		default:
			w.Header().Set("Allow", "GET, POST")
			http.Error(w, "", http.StatusMethodNotAllowed)
			return
		}
		if strings.TrimSpace(req.Query) == "" {
			http.Error(w, `{"errors":[{"message":"no query provided"}]}`, http.StatusBadRequest)
			return
		}
		res := graphql.Do(graphql.Params{
			Schema: schema, RequestString: req.Query, VariableValues: req.Variables,
			OperationName: req.OperationName, Context: r.Context(), // <- request context reaches resolvers
		})
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(res) // 200 even when res.Errors is set: that is the GraphQL convention
	})
}

// isMutation parses the document and checks the operation that WOULD run.
func isMutation(query, opName string) bool {
	doc, err := parser.Parse(parser.ParseParams{Source: query})
	if err != nil {
		return false // let the executor report the syntax error
	}
	for _, def := range doc.Definitions {
		if op, ok := def.(*ast.OperationDefinition); ok && op.Operation == "mutation" {
			if opName == "" || (op.Name != nil && op.Name.Value == opName) {
				return true
			}
		}
	}
	return false
}

// Middleware that "authenticates" and stores the caller in the context.
func withViewer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		who := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), ctxKey{}, who)))
	})
}

// ------------------------------------------------------------------- demo ---
func main() {
	mux := http.NewServeMux()
	mux.Handle("/graphql", withViewer(Handler(buildSchema())))
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	go http.Serve(ln, mux)
	base := "http://" + ln.Addr().String() + "/graphql"

	post := func(body string) (int, string) {
		req, _ := http.NewRequest("POST", base, strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer alice")
		res, err := http.DefaultClient.Do(req)
		if err != nil {
			panic(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, strings.TrimSpace(string(b))
	}
	must := func(ok bool, what string) {
		if !ok {
			panic("FAILED: " + what)
		}
	}
	show := func(label string, st int, body string) { fmt.Printf("%-34s -> %d %s\n", label, st, body) }

	st, b := post(`{"query":"query($n:String){ hello(name:$n) }","variables":{"n":"Go"}}`)
	show("POST with variables", st, b)
	must(st == 200 && strings.Contains(b, `hello Go (asked by \"alice\")`), "variables + context reach the resolver")

	doc := `query Read { counter }  mutation Bump { increment }`
	st, b = post(`{"query":` + jsonStr(doc) + `,"operationName":"Bump"}`)
	show("operationName=Bump", st, b)
	must(strings.Contains(b, `"increment":1`), "picked the mutation")
	st, b = post(`{"query":` + jsonStr(doc) + `}`)
	show("no operationName (ambiguous)", st, b)
	must(st == 200 && strings.Contains(b, "errors"), "ambiguous document is an error")

	st, b = post(`not json`)
	show("malformed body", st, b)
	must(st == 400, "400 for garbage")

	st, b = post(`{"query":"{ nope }"}`)
	show("unknown field", st, b[:60]+"...")
	must(st == 200 && strings.Contains(b, "errors"), "validation errors are HTTP 200")

	get := func(q string) (int, string) {
		res, err := http.Get(base + "?query=" + url.QueryEscape(q))
		if err != nil {
			panic(err)
		}
		defer res.Body.Close()
		b, _ := io.ReadAll(res.Body)
		return res.StatusCode, strings.TrimSpace(string(b))
	}
	st, b = get("{ counter }")
	show("GET query", st, b)
	must(st == 200 && strings.Contains(b, `"counter":1`), "GET query")
	st, _ = get("mutation { increment }")
	show("GET mutation", st, "")
	must(st == 405, "mutations refused over GET")
	fmt.Println("OK")
}

func jsonStr(s string) string { b, _ := json.Marshal(s); return string(b) }
