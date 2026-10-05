/*
LAB 03 (advanced) - Building a DataLoader from scratch (generics + thunks)
==========================================================================
You will learn

  - the N+1 problem in Go:  Post.author runs once per post  ->  1 + N queries

  - graphql-go lets a resolver return a THUNK (func() (any, error)) instead of a value.
    The executor first calls every resolver of a list (each one only QUEUES its key and returns
    a thunk), THEN runs the thunks. That gap is exactly the batching window.

  - a small generic Loader[K, V]:
    Load(key)  -> records the key, returns a thunk
    first thunk to run -> calls the batch function ONCE for all queued keys
    other thunks       -> read their answer from that batch

  - per-request cache: 50 posts by 5 authors -> the batch asks for 5 keys, not 50

  - the rule that never changes: build the loader PER REQUEST (put it in the context)

    Load(1) Load(2) Load(1) Load(3) ...   <- all queued during the list resolution
    |
    ONE batch: WHERE id IN (1,2,3)
    |
    each thunk gets ITS value back

Run it   go run ./GraphQL/labs/golang/03_dataloader_batching
*/
package main

import (
	"context"
	"fmt"
	"sort"
	"sync"

	"github.com/graphql-go/graphql"
)

// ------------------------------------------------------------ the loader ----
type Loader[K comparable, V any] struct {
	batch func(keys []K) (map[K]V, error) // fetch many at once; return whatever was found

	mu      sync.Mutex
	cache   map[K]V // per-loader (= per-request) cache
	queued  []K
	queuedS map[K]bool
	round   *round[K, V] // the batch that queued keys are waiting on
}

type round[K comparable, V any] struct {
	once sync.Once
	keys []K
	err  error
}

func NewLoader[K comparable, V any](batch func([]K) (map[K]V, error)) *Loader[K, V] {
	return &Loader[K, V]{batch: batch, cache: map[K]V{}, queuedS: map[K]bool{}}
}

// Load queues the key and returns a thunk. It does NOT hit the database.
func (l *Loader[K, V]) Load(key K) func() (any, error) {
	l.mu.Lock()
	if _, hit := l.cache[key]; !hit && !l.queuedS[key] { // dedupe: same key queued once
		l.queued = append(l.queued, key)
		l.queuedS[key] = true
	}
	if l.round == nil {
		l.round = &round[K, V]{}
	}
	r := l.round
	l.mu.Unlock()

	return func() (any, error) {
		r.once.Do(func() { // the FIRST thunk to run dispatches the whole batch
			l.mu.Lock()
			r.keys, l.queued, l.queuedS, l.round = l.queued, nil, map[K]bool{}, nil
			l.mu.Unlock()
			if len(r.keys) == 0 {
				return
			}
			found, err := l.batch(r.keys)
			l.mu.Lock()
			for k, v := range found {
				l.cache[k] = v
			}
			l.mu.Unlock()
			r.err = err
		})
		l.mu.Lock()
		defer l.mu.Unlock()
		if r.err != nil {
			return nil, r.err
		}
		if v, ok := l.cache[key]; ok {
			return v, nil
		}
		return nil, fmt.Errorf("key %v not found", key)
	}
}

// -------------------------------------------------------------- fake data ---
type Author struct {
	ID   int
	Name string
}
type Post struct {
	ID, AuthorID int
	Title        string
}

var sqlLog []string // every "round trip"

func fetchAuthors(ids []int) (map[int]Author, error) {
	sort.Ints(ids)
	sqlLog = append(sqlLog, fmt.Sprintf("SELECT * FROM authors WHERE id IN %v", ids))
	out := map[int]Author{}
	for _, id := range ids {
		out[id] = Author{id, fmt.Sprintf("author-%d", id)}
	}
	return out, nil
}

func allPosts() []Post {
	sqlLog = append(sqlLog, "SELECT * FROM posts LIMIT 50")
	var ps []Post
	for i := 1; i <= 50; i++ {
		ps = append(ps, Post{i, i%5 + 1, fmt.Sprintf("post-%d", i)})
	}
	return ps
}

// ------------------------------------------------------------ the schema ----
type loaderKey struct{}

func buildSchema(useLoader bool) graphql.Schema {
	authorType := graphql.NewObject(graphql.ObjectConfig{Name: "Author", Fields: graphql.Fields{
		"id": {Type: graphql.Int}, "name": {Type: graphql.String},
	}})
	postType := graphql.NewObject(graphql.ObjectConfig{Name: "Post", Fields: graphql.Fields{
		"title": {Type: graphql.String},
		"author": {Type: authorType, Resolve: func(p graphql.ResolveParams) (any, error) {
			id := p.Source.(Post).AuthorID
			if !useLoader { // NAIVE: one query per post
				m, _ := fetchAuthors([]int{id})
				return m[id], nil
			}
			loader := p.Context.Value(loaderKey{}).(*Loader[int, Author])
			return loader.Load(id), nil // returns a thunk; nothing is fetched yet
		}},
	}})
	q := graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: graphql.Fields{
		"posts": {Type: graphql.NewList(postType), Resolve: func(graphql.ResolveParams) (any, error) { return allPosts(), nil }},
	}})
	s, _ := graphql.NewSchema(graphql.SchemaConfig{Query: q})
	return s
}

func execute(schema graphql.Schema, ctx context.Context) *graphql.Result {
	return graphql.Do(graphql.Params{Schema: schema, RequestString: `{ posts { title author { name } } }`, Context: ctx})
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	sqlLog = nil
	res := execute(buildSchema(false), context.Background())
	fmt.Printf("NAIVE     : %2d round trips (1 + N)\n", len(sqlLog))
	must(!res.HasErrors() && len(sqlLog) == 51, "naive is N+1")

	sqlLog = nil
	ctx := context.WithValue(context.Background(), loaderKey{}, NewLoader(fetchAuthors)) // PER REQUEST
	res = execute(buildSchema(true), ctx)
	fmt.Printf("DATALOADER: %2d round trips\n", len(sqlLog))
	for _, l := range sqlLog {
		fmt.Println("     ", l)
	}
	must(!res.HasErrors() && len(sqlLog) == 2, "batched into one query")

	posts := res.Data.(map[string]any)["posts"].([]any)
	first := posts[0].(map[string]any)
	fmt.Println("first post ->", first["title"], "by", first["author"].(map[string]any)["name"])
	must(first["author"].(map[string]any)["name"] == "author-2", "each post got ITS author")

	// A second request must use a NEW loader: the first loader's cache is now warm.
	sqlLog = nil
	execute(buildSchema(true), context.WithValue(context.Background(), loaderKey{}, NewLoader(fetchAuthors)))
	must(len(sqlLog) == 2, "fresh loader, fresh queries (no cross-request caching)")
	fmt.Println("OK")
}
