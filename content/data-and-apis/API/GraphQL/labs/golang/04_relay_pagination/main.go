/*
LAB 04 (advanced) - Relay-style cursor pagination ("connections")
=================================================================
You will learn

  - why lists need pagination: an unbounded `items` field is a denial-of-service waiting to happen

  - the Relay connection shape used by GitHub, Shopify, Facebook:

    posts(first: 3, after: "cursor") {
    totalCount
    edges { cursor node { id title } }     <- each item travels with ITS OWN cursor
    pageInfo { hasNextPage endCursor }
    }

  - cursors are OPAQUE strings (base64 here). Clients never build them; the server can change what
    is inside (an offset today, a keyset tomorrow) without breaking anyone.

  - keyset semantics: "give me items AFTER this id", stable even when rows are inserted

  - server-side limits: `first` is required and capped, negative values rejected

  - the "fetch one extra row" trick to compute hasNextPage without a COUNT

Run it   go run ./GraphQL/labs/golang/04_relay_pagination
*/
package main

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/graphql-go/graphql"
)

type Post struct {
	ID    int
	Title string
}

var posts []Post // ordered by ID ascending

const maxPageSize = 50

func encodeCursor(id int) string {
	return base64.StdEncoding.EncodeToString([]byte("post:" + strconv.Itoa(id)))
}

func decodeCursor(c string) (int, error) {
	raw, err := base64.StdEncoding.DecodeString(c)
	id, ok := strings.CutPrefix(string(raw), "post:")
	if err != nil || !ok {
		return 0, errors.New("invalid cursor")
	}
	return strconv.Atoi(id)
}

// page implements:  SELECT * FROM posts WHERE id > :after ORDER BY id LIMIT :first+1
func page(first int, after string) (edges []map[string]any, hasNext bool, err error) {
	if first < 1 || first > maxPageSize {
		return nil, false, fmt.Errorf("first must be between 1 and %d", maxPageSize)
	}
	afterID := 0
	if after != "" {
		if afterID, err = decodeCursor(after); err != nil {
			return nil, false, err
		}
	}
	var rows []Post
	for _, p := range posts {
		if p.ID > afterID {
			rows = append(rows, p)
			if len(rows) == first+1 { // one extra row tells us there is a next page
				break
			}
		}
	}
	if hasNext = len(rows) > first; hasNext {
		rows = rows[:first]
	}
	for _, p := range rows {
		edges = append(edges, map[string]any{"cursor": encodeCursor(p.ID), "node": p})
	}
	return edges, hasNext, nil
}

func buildSchema() graphql.Schema {
	postType := graphql.NewObject(graphql.ObjectConfig{Name: "Post", Fields: graphql.Fields{
		"id": {Type: graphql.NewNonNull(graphql.Int)}, "title": {Type: graphql.NewNonNull(graphql.String)},
	}})
	edgeType := graphql.NewObject(graphql.ObjectConfig{Name: "PostEdge", Fields: graphql.Fields{
		"cursor": {Type: graphql.NewNonNull(graphql.String)}, "node": {Type: graphql.NewNonNull(postType)},
	}})
	pageInfo := graphql.NewObject(graphql.ObjectConfig{Name: "PageInfo", Fields: graphql.Fields{
		"hasNextPage": {Type: graphql.NewNonNull(graphql.Boolean)}, "endCursor": {Type: graphql.String},
	}})
	connection := graphql.NewObject(graphql.ObjectConfig{Name: "PostConnection", Fields: graphql.Fields{
		"totalCount": {Type: graphql.NewNonNull(graphql.Int)},
		"edges":      {Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(edgeType)))},
		"pageInfo":   {Type: graphql.NewNonNull(pageInfo)},
	}})
	query := graphql.NewObject(graphql.ObjectConfig{Name: "Query", Fields: graphql.Fields{
		"posts": {
			Type: graphql.NewNonNull(connection),
			Args: graphql.FieldConfigArgument{
				"first": {Type: graphql.NewNonNull(graphql.Int)}, // REQUIRED: no accidental "give me everything"
				"after": {Type: graphql.String},
			},
			Resolve: func(p graphql.ResolveParams) (any, error) {
				after, _ := p.Args["after"].(string)
				edges, hasNext, err := page(p.Args["first"].(int), after)
				if err != nil {
					return nil, err
				}
				var end any
				if n := len(edges); n > 0 {
					end = edges[n-1]["cursor"]
				}
				return map[string]any{
					"totalCount": len(posts),
					"edges":      edges,
					"pageInfo":   map[string]any{"hasNextPage": hasNext, "endCursor": end},
				}, nil
			},
		},
	}})
	s, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		panic(err)
	}
	return s
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	for i := 1; i <= 8; i++ {
		posts = append(posts, Post{i, fmt.Sprintf("post-%d", i)})
	}
	schema := buildSchema()
	const q = `query($first: Int!, $after: String) {
	  posts(first: $first, after: $after) {
	    totalCount
	    edges { cursor node { id title } }
	    pageInfo { hasNextPage endCursor }
	  }
	}`
	fetch := func(first int, after any) *graphql.Result {
		return graphql.Do(graphql.Params{Schema: schema, RequestString: q, VariableValues: map[string]any{"first": first, "after": after}})
	}

	fmt.Println("-- walk the whole list, 3 at a time --")
	var ids []int
	var cursor any
	for pageNo := 1; ; pageNo++ {
		res := fetch(3, cursor)
		must(!res.HasErrors(), fmt.Sprint(res.Errors))
		conn := res.Data.(map[string]any)["posts"].(map[string]any)
		var titles []string
		for _, e := range conn["edges"].([]any) {
			n := e.(map[string]any)["node"].(map[string]any)
			ids, titles = append(ids, n["id"].(int)), append(titles, n["title"].(string))
		}
		info := conn["pageInfo"].(map[string]any)
		fmt.Printf("page %d: %v  hasNextPage=%v endCursor=%v\n", pageNo, titles, info["hasNextPage"], info["endCursor"])
		if !info["hasNextPage"].(bool) {
			break
		}
		cursor = info["endCursor"]
	}
	must(fmt.Sprint(ids) == "[1 2 3 4 5 6 7 8]", "every row exactly once")

	fmt.Println("-- a row is inserted at the front mid-walk: no duplicates --")
	first := fetch(3, nil).Data.(map[string]any)["posts"].(map[string]any)
	end := first["pageInfo"].(map[string]any)["endCursor"]
	posts = append([]Post{{0, "new-front-row"}}, posts...) // OFFSET pagination would now repeat post-3
	second := fetch(3, end).Data.(map[string]any)["posts"].(map[string]any)
	firstOfSecond := second["edges"].([]any)[0].(map[string]any)["node"].(map[string]any)["id"]
	fmt.Println("second page starts at id", firstOfSecond, "(expected 4)")
	must(firstOfSecond == 4, "keyset pagination is stable")

	fmt.Println("-- guard rails --")
	for _, c := range []struct {
		name  string
		first int
		after any
	}{{"first=0", 0, nil}, {"first=1000", 1000, nil}, {"forged cursor", 3, "not-a-cursor"}} {
		res := fetch(c.first, c.after)
		b, _ := json.Marshal(res.Errors[0].Message)
		fmt.Printf("%-14s -> error %s\n", c.name, b)
		must(res.HasErrors(), c.name)
	}
	fmt.Println("OK")
}
