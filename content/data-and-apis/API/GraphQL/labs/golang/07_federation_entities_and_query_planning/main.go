/*
LAB 07 (advanced) - Federation from the inside: _entities by hand, a router, partial failure
=============================================================================================
Python lab 07 used strawberry.federation, which writes the federation plumbing for you. This lab
writes that plumbing BY HAND in graphql-go (which has no federation support), so nothing is magic,
then builds a small router over two subgraphs.

	client --> ROUTER --(parallel)--> products subgraph   Query.topProducts, Product @key(upc)
	              |   --(parallel)--> reviews subgraph    Query.reviewCount
	              +--- then _entities ---> reviews         Product.reviews  (batched, one call)

You will learn

  - the federation subgraph contract, written out:
    _service { sdl }                         a string: the subgraph's schema with @key directives
    _entities(representations: [_Any!]!)     returns [_Entity]! in the SAME ORDER as the input
    scalar _Any                              arbitrary JSON: {"__typename":"Product","upc":"p1"}
    union _Entity                            every type that has a @key in this subgraph

  - batching INSIDE the subgraph: _entities receives all N keys at once, so it can do ONE
    "WHERE upc IN (...)" query instead of N (lab 03's DataLoader rule, across services)

  - composition by parsing each subgraph's SDL with graphql-go's parser (ast.ObjectDefinition,
    @key directive, field owners)

  - planning + execution: independent ROOT fetches run in PARALLEL; entity fetches run after
    the fetch that produced their keys; the router injects __typename + key fields and strips
    them from the final response

  - PARTIAL FAILURE: when the reviews subgraph is down the router still returns products, sets
    the missing fields to null and adds an error with a `path` and the subgraph name

  - the security hole every federated setup must close: _entities lets a caller fetch ANY
    entity by key, skipping whatever checks the router did. Subgraphs must accept only router
    traffic (network policy, mTLS, or a router-signed header as in Gateway lab 02)

Run it   go run ./GraphQL/labs/golang/07_federation_entities_and_query_planning
*/
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/graphql-go/graphql"
	"github.com/graphql-go/graphql/language/ast"
	"github.com/graphql-go/graphql/language/parser"
	"github.com/graphql-go/graphql/language/printer"
	"github.com/graphql-go/graphql/language/source"
)

// ======================================================= federation building blocks ===
var anyScalar = graphql.NewScalar(graphql.ScalarConfig{
	Name:         "_Any",
	Serialize:    func(v interface{}) interface{} { return v },
	ParseValue:   func(v interface{}) interface{} { return v }, // representations arrive as variables
	ParseLiteral: func(v ast.Value) interface{} { return nil },
})

var serviceType = graphql.NewObject(graphql.ObjectConfig{Name: "_Service", Fields: graphql.Fields{
	"sdl": {Type: graphql.NewNonNull(graphql.String)},
}})

// federate adds _service and _entities to a subgraph's Query fields.
// resolveBatch receives ALL representations of one request and returns one result per input.
func federate(q graphql.Fields, sdl string, entities []*graphql.Object,
	resolveBatch func([]map[string]interface{}) []interface{}) {
	entityUnion := graphql.NewUnion(graphql.UnionConfig{
		Name:  "_Entity",
		Types: entities,
		ResolveType: func(p graphql.ResolveTypeParams) *graphql.Object {
			name := p.Value.(map[string]interface{})["__typename"]
			for _, e := range entities {
				if e.Name() == name {
					return e
				}
			}
			return nil
		},
	})
	q["_service"] = &graphql.Field{Type: graphql.NewNonNull(serviceType),
		Resolve: func(graphql.ResolveParams) (interface{}, error) { return map[string]interface{}{"sdl": sdl}, nil }}
	q["_entities"] = &graphql.Field{
		Type: graphql.NewNonNull(graphql.NewList(entityUnion)),
		Args: graphql.FieldConfigArgument{"representations": {Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(anyScalar)))}},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			var reps []map[string]interface{}
			for _, r := range p.Args["representations"].([]interface{}) {
				reps = append(reps, r.(map[string]interface{}))
			}
			return resolveBatch(reps), nil
		},
	}
}

// ================================================================= products subgraph ===
const productsSDL = `
type Product @key(fields: "upc") { upc: String! name: String! price: Int! }
type Query { topProducts(first: Int): [Product!]! }`

var productRows = []map[string]interface{}{
	{"upc": "p1", "name": "Kettle", "price": 3999}, {"upc": "p2", "name": "Toaster", "price": 2999},
	{"upc": "p3", "name": "Blender", "price": 5999},
}

func productsSchema() graphql.Schema {
	product := graphql.NewObject(graphql.ObjectConfig{Name: "Product", Fields: graphql.Fields{
		"upc": {Type: graphql.NewNonNull(graphql.String)}, "name": {Type: graphql.NewNonNull(graphql.String)},
		"price": {Type: graphql.NewNonNull(graphql.Int)},
	}})
	q := graphql.Fields{"topProducts": {
		Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(product))),
		Args: graphql.FieldConfigArgument{"first": {Type: graphql.Int, DefaultValue: 10}},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			n := min(p.Args["first"].(int), len(productRows))
			return productRows[:n], nil
		},
	}}
	federate(q, productsSDL, []*graphql.Object{product}, func(reps []map[string]interface{}) []interface{} {
		out := make([]interface{}, len(reps))
		for i, r := range reps {
			for _, row := range productRows {
				if row["upc"] == r["upc"] {
					out[i] = merge(map[string]interface{}{"__typename": "Product"}, row)
				}
			}
		}
		return out
	})
	s, err := graphql.NewSchema(graphql.SchemaConfig{Query: graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: q})})
	if err != nil {
		panic(err)
	}
	return s
}

// ================================================================== reviews subgraph ===
const reviewsSDL = `
type Product @key(fields: "upc") { upc: String! reviews: [Review!]! }
type Review { body: String! stars: Int! }
type Query { reviewCount: Int! }`

var reviewRows = []map[string]interface{}{
	{"upc": "p1", "body": "boils fast", "stars": 5}, {"upc": "p1", "body": "loud", "stars": 3},
	{"upc": "p2", "body": "burns toast", "stars": 2}, {"upc": "p3", "body": "smoothies!", "stars": 5},
}

var reviewDBQueries atomic.Int32

func reviewsSchema() graphql.Schema {
	review := graphql.NewObject(graphql.ObjectConfig{Name: "Review", Fields: graphql.Fields{
		"body": {Type: graphql.NewNonNull(graphql.String)}, "stars": {Type: graphql.NewNonNull(graphql.Int)},
	}})
	product := graphql.NewObject(graphql.ObjectConfig{Name: "Product", Fields: graphql.Fields{
		"upc":     {Type: graphql.NewNonNull(graphql.String)},
		"reviews": {Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(review)))},
	}})
	q := graphql.Fields{"reviewCount": {Type: graphql.NewNonNull(graphql.Int),
		Resolve: func(graphql.ResolveParams) (interface{}, error) { return len(reviewRows), nil }}}
	federate(q, reviewsSDL, []*graphql.Object{product}, func(reps []map[string]interface{}) []interface{} {
		// ONE query for every product in the batch: SELECT * FROM reviews WHERE upc IN (...)
		reviewDBQueries.Add(1)
		byUPC := map[interface{}][]map[string]interface{}{}
		for _, r := range reviewRows {
			byUPC[r["upc"]] = append(byUPC[r["upc"]], r)
		}
		out := make([]interface{}, len(reps)) // same order as the input: the router zips by index
		for i, r := range reps {
			out[i] = map[string]interface{}{"__typename": "Product", "upc": r["upc"], "reviews": byUPC[r["upc"]]}
		}
		return out
	})
	s, err := graphql.NewSchema(graphql.SchemaConfig{Query: graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: q})})
	if err != nil {
		panic(err)
	}
	return s
}

// ================================================================ subgraph over HTTP ===
type gqlRequest struct {
	Query     string                 `json:"query"`
	Variables map[string]interface{} `json:"variables,omitempty"`
}

// subgraphHandler serves a schema. requireRouter=true accepts only calls carrying the router's secret.
func subgraphHandler(s graphql.Schema, down *atomic.Bool, requireRouter bool) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if down != nil && down.Load() {
			http.Error(w, "unavailable", http.StatusServiceUnavailable)
			return
		}
		if requireRouter && r.Header.Get("X-Router-Token") != routerToken {
			http.Error(w, "subgraphs accept router traffic only", http.StatusForbidden)
			return
		}
		var req gqlRequest
		json.NewDecoder(r.Body).Decode(&req)
		res := graphql.Do(graphql.Params{Schema: s, RequestString: req.Query, VariableValues: req.Variables})
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(res)
	})
}

const routerToken = "router-secret-from-a-vault"

var subgraphCalls sync.Map // subgraph -> *atomic.Int32

func post(sub, url, query string, vars map[string]interface{}) (map[string]interface{}, error) {
	c, _ := subgraphCalls.LoadOrStore(sub, &atomic.Int32{})
	c.(*atomic.Int32).Add(1)
	body, _ := json.Marshal(gqlRequest{query, vars})
	req, _ := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Router-Token", routerToken)
	resp, err := (&http.Client{Timeout: 2 * time.Second}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("subgraph %s returned %d", sub, resp.StatusCode)
	}
	var out struct {
		Data   map[string]interface{} `json:"data"`
		Errors []interface{}          `json:"errors"`
	}
	json.NewDecoder(resp.Body).Decode(&out)
	if len(out.Errors) > 0 {
		return nil, fmt.Errorf("subgraph %s: %v", sub, out.Errors[0])
	}
	return out.Data, nil
}

// ======================================================================= composition ===
type Supergraph struct {
	owner map[string]string   // "Type.field" -> subgraph
	ftype map[string]string   // "Type.field" -> named type
	keys  map[string][]string // "Type@subgraph" -> key fields
	urls  map[string]string
}

func namedType(t ast.Type) string {
	switch n := t.(type) {
	case *ast.NonNull:
		return namedType(n.Type)
	case *ast.List:
		return namedType(n.Type)
	case *ast.Named:
		return n.Name.Value
	}
	return ""
}

func parseDoc(s string) *ast.Document {
	d, err := parser.Parse(parser.ParseParams{Source: source.NewSource(&source.Source{Body: []byte(s)})})
	if err != nil {
		panic(err)
	}
	return d
}

func compose(urls map[string]string) Supergraph {
	sg := Supergraph{map[string]string{}, map[string]string{}, map[string][]string{}, urls}
	names := make([]string, 0, len(urls))
	for n := range urls {
		names = append(names, n)
	}
	sort.Strings(names) // deterministic ownership for fields defined twice (key fields)
	for _, sub := range names {
		data, err := post(sub, urls[sub], "{ _service { sdl } }", nil)
		if err != nil {
			panic(err)
		}
		sdl := data["_service"].(map[string]interface{})["sdl"].(string)
		for _, def := range parseDoc(sdl).Definitions {
			od, ok := def.(*ast.ObjectDefinition)
			if !ok {
				continue
			}
			t := od.Name.Value
			for _, d := range od.Directives {
				if d.Name.Value == "key" {
					sg.keys[t+"@"+sub] = strings.Fields(d.Arguments[0].Value.GetValue().(string))
				}
			}
			for _, f := range od.Fields {
				c := t + "." + f.Name.Value
				sg.ftype[c] = namedType(f.Type)
				if _, taken := sg.owner[c]; !taken {
					sg.owner[c] = sub
				}
			}
		}
	}
	return sg
}

// ========================================================================== planning ===
type Fetch struct {
	Sub, Type string // Type == "" for a root fetch
	Path      []string
	Selection string
	Children  []*Fetch
}

func isKey(sg Supergraph, typ, sub, field string) bool {
	for _, k := range sg.keys[typ+"@"+sub] {
		if k == field {
			return true
		}
	}
	return false
}

func planSel(sg Supergraph, sels []ast.Selection, typ, sub string, path []string) (string, []*Fetch) {
	var parts []string
	var deps []*Fetch
	remote := map[string][]ast.Selection{}
	var remoteOrder []string
	for _, s := range sels {
		f := s.(*ast.Field)
		name := f.Name.Value
		owner := sg.owner[typ+"."+name]
		if owner != sub && !isKey(sg, typ, sub, name) {
			if _, seen := remote[owner]; !seen {
				remoteOrder = append(remoteOrder, owner)
			}
			remote[owner] = append(remote[owner], s)
			continue
		}
		args := ""
		if len(f.Arguments) > 0 {
			var as []string
			for _, a := range f.Arguments {
				as = append(as, printer.Print(a).(string))
			}
			args = "(" + strings.Join(as, ", ") + ")"
		}
		if f.SelectionSet != nil {
			text, d := planSel(sg, f.SelectionSet.Selections, sg.ftype[typ+"."+name], sub, append(append([]string{}, path...), name))
			parts = append(parts, fmt.Sprintf("%s%s { %s }", name, args, text))
			deps = append(deps, d...)
		} else {
			parts = append(parts, name+args)
		}
	}
	for _, owner := range remoteOrder {
		parts = append(parts, append([]string{"__typename"}, sg.keys[typ+"@"+sub]...)...)
		text, d := planSel(sg, remote[owner], typ, owner, path)
		deps = append(deps, &Fetch{owner, typ, path, text, d})
	}
	return strings.Join(parts, " "), deps
}

func plan(sg Supergraph, query string) []*Fetch {
	op := parseDoc(query).Definitions[0].(*ast.OperationDefinition)
	byOwner := map[string][]ast.Selection{}
	var order []string
	for _, s := range op.SelectionSet.Selections {
		o := sg.owner["Query."+s.(*ast.Field).Name.Value]
		if _, ok := byOwner[o]; !ok {
			order = append(order, o)
		}
		byOwner[o] = append(byOwner[o], s)
	}
	var out []*Fetch
	for _, sub := range order {
		text, deps := planSel(sg, byOwner[sub], "Query", sub, nil)
		out = append(out, &Fetch{sub, "", nil, text, deps})
	}
	return out
}

func showPlan(fs []*Fetch, depth int) {
	for _, f := range fs {
		where := "Query"
		if f.Type != "" {
			where = "_entities " + f.Type + " at " + strings.Join(f.Path, ".")
		}
		prefix := "Parallel "
		if depth > 0 {
			prefix = strings.Repeat("    ", depth) + "then "
		}
		fmt.Printf("   %sFetch(%s) %s: { %s }\n", prefix, f.Sub, where, f.Selection)
		showPlan(f.Children, depth+1)
	}
}

// ========================================================================= execution ===
func merge(dst, src map[string]interface{}) map[string]interface{} {
	for k, v := range src {
		dst[k] = v
	}
	return dst
}

func objectsAt(data map[string]interface{}, path []string) []map[string]interface{} {
	level := []interface{}{data}
	for _, k := range path {
		var next []interface{}
		for _, o := range level {
			m, _ := o.(map[string]interface{})
			switch v := m[k].(type) {
			case []interface{}:
				next = append(next, v...)
			case nil:
			default:
				next = append(next, v)
			}
		}
		level = next
	}
	var out []map[string]interface{}
	for _, o := range level {
		if m, ok := o.(map[string]interface{}); ok {
			out = append(out, m)
		}
	}
	return out
}

type gqlError struct {
	Message    string            `json:"message"`
	Path       []string          `json:"path"`
	Extensions map[string]string `json:"extensions"`
}

type executor struct {
	sg     Supergraph
	mu     sync.Mutex
	data   map[string]interface{}
	errors []gqlError
}

func (e *executor) fail(f *Fetch, err error, fields []string) {
	e.mu.Lock()
	defer e.mu.Unlock()
	for _, fld := range fields {
		e.errors = append(e.errors, gqlError{err.Error(), append(append([]string{}, f.Path...), fld),
			map[string]string{"code": "SUBGRAPH_UNAVAILABLE", "serviceName": f.Sub}})
	}
}

func topFields(selection string) []string { // first-level field names of a planned selection
	var out []string
	depth := 0
	for _, tok := range strings.Fields(selection) {
		switch {
		case tok == "{":
			depth++
		case tok == "}":
			depth--
		case depth == 0 && !strings.HasPrefix(tok, "__"):
			out = append(out, strings.SplitN(tok, "(", 2)[0])
		}
	}
	return out
}

func (e *executor) run(f *Fetch) {
	url := e.sg.urls[f.Sub]
	if f.Type == "" {
		data, err := post(f.Sub, url, "{ "+f.Selection+" }", nil)
		if err != nil {
			e.fail(f, err, topFields(f.Selection))
			return
		}
		e.mu.Lock()
		merge(e.data, data)
		e.mu.Unlock()
	} else {
		e.mu.Lock()
		targets := objectsAt(e.data, f.Path)
		e.mu.Unlock()
		var reps []interface{}
		for _, t := range targets {
			rep := map[string]interface{}{"__typename": f.Type}
			for _, k := range e.sg.keys[f.Type+"@"+f.Sub] {
				rep[k] = t[k]
			}
			reps = append(reps, rep)
		}
		q := fmt.Sprintf("query($r: [_Any!]!) { _entities(representations: $r) { ... on %s { %s } } }", f.Type, f.Selection)
		data, err := post(f.Sub, url, q, map[string]interface{}{"r": reps})
		if err != nil {
			e.mu.Lock()
			for _, t := range targets { // null the fields this subgraph should have provided
				for _, fld := range topFields(f.Selection) {
					t[fld] = nil
				}
			}
			e.mu.Unlock()
			e.fail(f, err, topFields(f.Selection))
			return
		}
		e.mu.Lock()
		for i, got := range data["_entities"].([]interface{}) { // zip by index: order is the contract
			merge(targets[i], got.(map[string]interface{}))
		}
		e.mu.Unlock()
	}
	for _, c := range f.Children {
		e.run(c)
	}
}

func project(v interface{}, sel *ast.SelectionSet) interface{} {
	switch x := v.(type) {
	case []interface{}:
		out := make([]interface{}, len(x))
		for i := range x {
			out[i] = project(x[i], sel)
		}
		return out
	case map[string]interface{}:
		if sel == nil {
			return x
		}
		out := map[string]interface{}{}
		for _, s := range sel.Selections {
			f := s.(*ast.Field)
			out[f.Name.Value] = project(x[f.Name.Value], f.SelectionSet) // missing -> null, as GraphQL requires
		}
		return out
	}
	return v
}

func execute(sg Supergraph, query string) (map[string]interface{}, []gqlError, time.Duration) {
	e := &executor{sg: sg, data: map[string]interface{}{}}
	start := time.Now()
	var wg sync.WaitGroup
	for _, f := range plan(sg, query) { // root fetches are independent: run them in parallel
		wg.Add(1)
		go func(f *Fetch) { defer wg.Done(); e.run(f) }(f)
	}
	wg.Wait()
	op := parseDoc(query).Definitions[0].(*ast.OperationDefinition)
	return project(e.data, op.SelectionSet).(map[string]interface{}), e.errors, time.Since(start)
}

func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

func calls(sub string) int32 {
	c, ok := subgraphCalls.Load(sub)
	if !ok {
		return 0
	}
	return c.(*atomic.Int32).Load()
}

func main() {
	var reviewsDown atomic.Bool
	products := httptest.NewServer(subgraphHandler(productsSchema(), nil, true))
	defer products.Close()
	reviews := httptest.NewServer(subgraphHandler(reviewsSchema(), &reviewsDown, true))
	defer reviews.Close()
	urls := map[string]string{"products": products.URL, "reviews": reviews.URL}

	fmt.Println("== 1. compose: read _service.sdl from each subgraph ==")
	sg := compose(urls)
	coords := make([]string, 0, len(sg.owner))
	for c := range sg.owner {
		coords = append(coords, c)
	}
	sort.Strings(coords)
	for _, c := range coords {
		if !strings.Contains(c, "._") {
			fmt.Printf("   %-20s -> %s\n", c, sg.owner[c])
		}
	}
	must(sg.owner["Product.reviews"] == "reviews" && sg.owner["Product.name"] == "products", "ownership")

	query := `{ topProducts(first: 3) { name reviews { body stars } } reviewCount }`
	fmt.Printf("\n== 2. plan %s ==\n", query)
	fetches := plan(sg, query)
	showPlan(fetches, 0)
	must(len(fetches) == 2 && len(fetches[0].Children) == 1, "two parallel roots + one entity fetch")

	fmt.Println("\n== 3. execute ==")
	subgraphCalls = sync.Map{}
	reviewDBQueries.Store(0)
	data, errs, took := execute(sg, query)
	out, _ := json.Marshal(data)
	fmt.Printf("   %s\n", out)
	fmt.Printf("   calls: products=%d reviews=%d; review DB queries=%d; took %v\n",
		calls("products"), calls("reviews"), reviewDBQueries.Load(), took.Round(time.Millisecond))
	must(len(errs) == 0, "no errors")
	first := data["topProducts"].([]interface{})[0].(map[string]interface{})
	_, leaked := first["upc"]
	must(!leaked && len(first["reviews"].([]interface{})) == 2, "keys stripped, reviews merged")
	must(calls("products") == 1 && calls("reviews") == 2 && reviewDBQueries.Load() == 1, "batched")
	fmt.Println("   3 products -> ONE _entities call -> ONE database query in the reviews subgraph")

	fmt.Println("\n== 4. partial failure: the reviews subgraph goes down ==")
	reviewsDown.Store(true)
	data, errs, _ = execute(sg, query)
	out, _ = json.Marshal(map[string]interface{}{"data": data, "errors": errs})
	fmt.Printf("   %s\n", out)
	must(data["topProducts"] != nil && first != nil, "products still served")
	must(len(errs) == 2, "one error per missing field")
	reviewsDown.Store(false)
	fmt.Println("   products still render; the client decides what a null `reviews` means.")
	fmt.Println("   (in a real schema, reviews must be NULLABLE in the supergraph for this to be legal)")

	fmt.Println("\n== 5. the _entities hole: calling a subgraph directly ==")
	body := `{"query":"query($r:[_Any!]!){ _entities(representations:$r){ ... on Product { name price } } }",` +
		`"variables":{"r":[{"__typename":"Product","upc":"p3"}]}}`
	open := httptest.NewServer(subgraphHandler(productsSchema(), nil, false))
	defer open.Close()
	r1, _ := http.Post(open.URL, "application/json", strings.NewReader(body))
	var leakedData map[string]interface{}
	json.NewDecoder(r1.Body).Decode(&leakedData)
	r1.Body.Close()
	r2, _ := http.Post(products.URL, "application/json", strings.NewReader(body))
	r2.Body.Close()
	fmt.Printf("   subgraph WITHOUT router check -> %v\n", leakedData["data"])
	fmt.Printf("   subgraph WITH router check    -> %d\n", r2.StatusCode)
	must(leakedData["data"] != nil && r2.StatusCode == http.StatusForbidden, "only router traffic")

	fmt.Println("\nOK")
}
