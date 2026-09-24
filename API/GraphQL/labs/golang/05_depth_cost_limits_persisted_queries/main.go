/*
LAB 05 (advanced) - Defending a GraphQL API: depth limit, cost limit, persisted queries
=======================================================================================
You will learn

  - the core danger: the CLIENT writes the query, so a tiny request can demand enormous work

    { users(first:100) { friends(first:100) { friends(first:100) { friends(first:100) { name } } } } }
    100 x 100 x 100 x 100 = 100,000,000 rows from ~100 bytes of query

  - DEFENCE 1  depth limit    : reject queries nested deeper than N (also stops cyclic abuse)

  - DEFENCE 2  cost analysis  : price each field (lists multiply by `first`), reject over a budget
    Both run on the PARSED document BEFORE any resolver runs - rejection is nearly free.

  - DEFENCE 3  persisted queries: the server only executes queries it already knows, by sha256 hash.

  - allowlist mode  : first-party apps ship a fixed set; anything else is refused

  - APQ (automatic) : unknown hash -> client resends {query, hash}; server checks the hash matches
    and remembers it. Saves bandwidth and enables GET + CDN caching.

  - walking the AST (graphql-go/language/ast): fields, fragment spreads, inline fragments

Run it   go run ./GraphQL/labs/golang/05_depth_cost_limits_persisted_queries
*/
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"strconv"
	"sync"

	"github.com/graphql-go/graphql"
	"github.com/graphql-go/graphql/language/ast"
	"github.com/graphql-go/graphql/language/parser"
	"github.com/graphql-go/graphql/language/source"
)

// -------------------------------------------------------- query analysis ----
// depth returns how deeply the selection set nests, following fragments.
func depth(sel *ast.SelectionSet, frags map[string]*ast.FragmentDefinition, seen map[string]bool) int {
	if sel == nil {
		return 0
	}
	max := 0
	for _, s := range sel.Selections {
		d := 0
		switch n := s.(type) {
		case *ast.Field:
			d = 1 + depth(n.SelectionSet, frags, seen)
		case *ast.InlineFragment:
			d = depth(n.SelectionSet, frags, seen)
		case *ast.FragmentSpread:
			if f := frags[n.Name.Value]; f != nil && !seen[n.Name.Value] { // seen[] stops fragment cycles
				seen[n.Name.Value] = true
				d = depth(f.SelectionSet, frags, seen)
				delete(seen, n.Name.Value)
			}
		}
		if d > max {
			max = d
		}
	}
	return max
}

// cost prices a selection set: every field costs 1; a field that takes `first`/`limit`
// multiplies the cost of everything beneath it by that number.
func cost(sel *ast.SelectionSet, vars map[string]any, frags map[string]*ast.FragmentDefinition) int {
	if sel == nil {
		return 0
	}
	total := 0
	for _, s := range sel.Selections {
		switch n := s.(type) {
		case *ast.Field:
			mult := 1
			for _, a := range n.Arguments {
				if a.Name.Value == "first" || a.Name.Value == "limit" {
					mult = intValue(a.Value, vars)
				}
			}
			total += 1 + mult*cost(n.SelectionSet, vars, frags)
		case *ast.InlineFragment:
			total += cost(n.SelectionSet, vars, frags)
		case *ast.FragmentSpread:
			if f := frags[n.Name.Value]; f != nil {
				total += cost(f.SelectionSet, vars, frags)
			}
		}
	}
	return total
}

func intValue(v ast.Value, vars map[string]any) int {
	switch t := v.(type) {
	case *ast.IntValue:
		n, _ := strconv.Atoi(t.Value)
		return n
	case *ast.Variable:
		if n, ok := vars[t.Name.Value].(int); ok {
			return n
		}
	}
	return 1
}

type Limits struct{ MaxDepth, MaxCost int }

// Check parses the query and returns (depth, cost) or an error explaining the rejection.
func (l Limits) Check(query string, vars map[string]any) (int, int, error) {
	doc, err := parser.Parse(parser.ParseParams{Source: source.NewSource(&source.Source{Body: []byte(query)})})
	if err != nil {
		return 0, 0, err
	}
	frags := map[string]*ast.FragmentDefinition{}
	for _, d := range doc.Definitions {
		if f, ok := d.(*ast.FragmentDefinition); ok {
			frags[f.Name.Value] = f
		}
	}
	dep, cst := 0, 0
	for _, d := range doc.Definitions {
		if op, ok := d.(*ast.OperationDefinition); ok {
			if x := depth(op.SelectionSet, frags, map[string]bool{}); x > dep {
				dep = x
			}
			cst += cost(op.SelectionSet, vars, frags)
		}
	}
	if dep > l.MaxDepth {
		return dep, cst, fmt.Errorf("query depth %d exceeds the limit of %d", dep, l.MaxDepth)
	}
	if cst > l.MaxCost {
		return dep, cst, fmt.Errorf("query cost %d exceeds the budget of %d", cst, l.MaxCost)
	}
	return dep, cst, nil
}

// ------------------------------------------------------ persisted queries ---
type PersistedStore struct {
	mu      sync.RWMutex
	queries map[string]string // sha256 hex -> query text
}

func hashOf(q string) string { h := sha256.Sum256([]byte(q)); return hex.EncodeToString(h[:]) }

var (
	ErrNotFound = errors.New("PersistedQueryNotFound")
	ErrRefused  = errors.New("PersistedQueryNotSupported: only registered queries are allowed")
)

// Resolve turns a request into the query text to run.
//
//	allowlist=true : only pre-registered hashes may run; raw queries are refused
//	allowlist=false: APQ - unknown hash -> ErrNotFound so the client resends query+hash
func (s *PersistedStore) Resolve(hash, query string, allowlist bool) (string, error) {
	if hash == "" {
		if allowlist {
			return "", ErrRefused
		}
		return query, nil
	}
	s.mu.RLock()
	known, ok := s.queries[hash]
	s.mu.RUnlock()
	if ok {
		return known, nil
	}
	if allowlist {
		return "", ErrRefused
	}
	if query == "" {
		return "", ErrNotFound
	}
	if hashOf(query) != hash { // never trust the client's claim: verify it
		return "", errors.New("provided sha256Hash does not match query")
	}
	s.mu.Lock()
	s.queries[hash] = query
	s.mu.Unlock()
	return query, nil
}

// ------------------------------------------------------------------ schema --
var resolverCalls int

func buildSchema() graphql.Schema {
	var userType *graphql.Object
	userType = graphql.NewObject(graphql.ObjectConfig{Name: "User", Fields: graphql.FieldsThunk(func() graphql.Fields {
		return graphql.Fields{
			"name": {Type: graphql.String},
			"friends": {
				Type: graphql.NewList(userType),
				Args: graphql.FieldConfigArgument{"first": {Type: graphql.Int}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					resolverCalls++
					return []map[string]any{}, nil
				},
			},
		}
	})})
	q := graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: graphql.Fields{
		"users": {
			Type: graphql.NewList(userType),
			Args: graphql.FieldConfigArgument{"first": {Type: graphql.Int}},
			Resolve: func(graphql.ResolveParams) (any, error) {
				resolverCalls++
				return []map[string]any{{"name": "ana"}}, nil
			},
		},
	}})
	s, _ := graphql.NewSchema(graphql.SchemaConfig{Query: q})
	return s
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	limits := Limits{MaxDepth: 5, MaxCost: 1000}
	schema := buildSchema()

	try := func(label, query string, vars map[string]any) error {
		d, c, err := limits.Check(query, vars)
		if err != nil {
			fmt.Printf("%-28s depth=%d cost=%-10d REJECTED: %v\n", label, d, c, err)
			return err
		}
		res := graphql.Do(graphql.Params{Schema: schema, RequestString: query, VariableValues: vars})
		fmt.Printf("%-28s depth=%d cost=%-10d allowed (errors=%v)\n", label, d, c, res.HasErrors())
		return nil
	}

	fmt.Println("== limits ==")
	resolverCalls = 0
	must(try("normal", `{ users(first: 10) { name friends(first: 5) { name } } }`, nil) == nil, "normal query passes")

	before := resolverCalls
	deep := `{ users { friends { friends { friends { friends { friends { name } } } } } } }`
	must(try("too deep (7 levels)", deep, nil) != nil, "depth limit")

	wide := `{ users(first:100) { friends(first:100) { friends(first:100) { name } } } }`
	must(try("too expensive (100^3)", wide, nil) != nil, "cost limit")

	viaVar := `query($n:Int){ users(first:$n) { friends(first:$n) { friends(first:$n) { name } } } }`
	must(try("variables can't hide it", viaVar, map[string]any{"n": 100}) != nil, "cost through variables")

	fragAttack := `query { users(first:100) { ...F } } fragment F on User { friends(first:100) { ...G } } fragment G on User { friends(first:100) { name } }`
	must(try("fragments can't hide it", fragAttack, nil) != nil, "cost through fragments")
	fmt.Println("resolvers run for rejected queries:", resolverCalls-before, "(rejected before executing)")

	fmt.Println("\n== persisted queries ==")
	store := &PersistedStore{queries: map[string]string{}}
	q := `{ users(first: 10) { name } }`
	h := hashOf(q)

	_, err := store.Resolve(h, "", false)
	fmt.Println("APQ 1: hash only, unknown        ->", err)
	must(errors.Is(err, ErrNotFound), "unknown hash asks for the query")

	_, err = store.Resolve(h, "{ users(first: 1000) { name } }", false)
	fmt.Println("APQ 2: hash does not match query ->", err)
	must(err != nil, "forged hash rejected")

	got, err := store.Resolve(h, q, false)
	fmt.Println("APQ 3: hash + query              ->", got, err)
	must(err == nil, "registered")

	got, err = store.Resolve(h, "", false)
	fmt.Println("APQ 4: hash only, now known      ->", got, err)
	must(err == nil && got == q, "served from the store")

	locked := &PersistedStore{queries: map[string]string{h: q}}
	_, err = locked.Resolve("", "{ users(first: 1000) { name } }", true)
	fmt.Println("allowlist: raw query             ->", err)
	must(errors.Is(err, ErrRefused), "raw queries refused in allowlist mode")
	got, err = locked.Resolve(h, "", true)
	fmt.Println("allowlist: registered hash       ->", got, err)
	must(err == nil, "registered hash accepted")
	fmt.Println("OK")
}
