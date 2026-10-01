package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/graphql-go/graphql"
)

// --- Models & Mock DB ---
type User struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

type Post struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	AuthorID string `json:"author_id"`
}

var usersDB = map[string]User{
	"u1": {ID: "u1", Name: "Alice", Email: "alice@example.com"},
	"u2": {ID: "u2", Name: "Bob", Email: "bob@example.com"},
}

var postsDB = map[string]Post{
	"p1": {ID: "p1", Title: "GraphQL is awesome", AuthorID: "u1"},
	"p2": {ID: "p2", Title: "REST vs GraphQL", AuthorID: "u2"},
}

// --- Middleware (Authentication) ---
func AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := r.Header.Get("Authorization")
		// In production, validate JWT here
		userID := ""
		if token == "Bearer admin-token" {
			userID = "u1" // Mock identified user
		}

		// Inject user into context
		ctx := context.WithValue(r.Context(), "userID", userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// --- GraphQL Types ---
var userType = graphql.NewObject(graphql.ObjectConfig{
	Name: "User",
	Fields: graphql.Fields{
		"id":    &graphql.Field{Type: graphql.String},
		"name":  &graphql.Field{Type: graphql.String},
		"email": &graphql.Field{Type: graphql.String},
	},
})

var postType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Post",
	Fields: graphql.Fields{
		"id":    &graphql.Field{Type: graphql.String},
		"title": &graphql.Field{Type: graphql.String},
		// Advanced: Resolving nested fields
		"author": &graphql.Field{
			Type: userType,
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				if post, ok := p.Source.(Post); ok {
					return usersDB[post.AuthorID], nil
				}
				return nil, nil
			},
		},
	},
})

// --- Queries ---
var queryType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Query",
	Fields: graphql.Fields{
		// 1. Get a specific post by ID (Arguments)
		"post": &graphql.Field{
			Type: postType,
			Args: graphql.FieldConfigArgument{
				"id": &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.String)},
			},
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				id := p.Args["id"].(string)
				post, exists := postsDB[id]
				if !exists {
					return nil, fmt.Errorf("post not found")
				}
				return post, nil
			},
		},
		// 2. Get all posts
		"posts": &graphql.Field{
			Type: graphql.NewList(postType),
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				var result []Post
				for _, v := range postsDB {
					result = append(result, v)
				}
				return result, nil
			},
		},
	},
})

// --- Mutations ---
var mutationType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Mutation",
	Fields: graphql.Fields{
		"createPost": &graphql.Field{
			Type: postType,
			Args: graphql.FieldConfigArgument{
				"title": &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.String)},
			},
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				// Access Context (Authentication check)
				ctx := p.Context
				userID, ok := ctx.Value("userID").(string)
				if !ok || userID == "" {
					return nil, fmt.Errorf("unauthorized: must provide valid Bearer token")
				}

				newPost := Post{
					ID:       fmt.Sprintf("p%d", len(postsDB)+1),
					Title:    p.Args["title"].(string),
					AuthorID: userID,
				}
				postsDB[newPost.ID] = newPost
				return newPost, nil
			},
		},
	},
})

func main() {
	// Compile Schema
	schemaConfig := graphql.SchemaConfig{Query: queryType, Mutation: mutationType}
	schema, err := graphql.NewSchema(schemaConfig)
	if err != nil {
		log.Fatalf("failed to create new schema, error: %v", err)
	}

	// HTTP Handler
	graphqlHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			Query     string                 `json:"query"`
			Operation string                 `json:"operationName"`
			Variables map[string]interface{} `json:"variables"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Error parsing JSON request body", 400)
			return
		}

		// Execute GraphQL request with the HTTP Context (containing auth data)
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			VariableValues: req.Variables,
			OperationName:  req.Operation,
			Context:        r.Context(),
		})

		json.NewEncoder(w).Encode(result)
	})

	// Mount middleware and start server
	http.Handle("/graphql", AuthMiddleware(graphqlHandler))
	log.Println("GraphQL server running on :8080/graphql")
	http.ListenAndServe(":8080", nil)
}
