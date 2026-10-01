// REAL-WORLD EXAMPLE: gqlgen (External 1)
// Demonstrates: Schema-first generation, Context handling for Auth, Nested Resolvers.
// NOTE: This is the implementation file. In a real project, gqlgen generates the boilerplate.

package main

import (
	"context"
	"fmt"
	"net/http"
	"strconv"

	// "github.com/99designs/gqlgen/graphql/handler"
	// "my-project/graph/generated"
	// "my-project/graph/model"
)

// --- MOCK DEFINITIONS TO MAKE FILE COMPILE-ABLE CONCEPTUALLY ---
type User struct {
	ID   string
	Name string
}
type Post struct {
	ID       string
	Title    string
	AuthorID string
}
// ---------------------------------------------------------------

// Resolver is the dependency injection container
type Resolver struct {
	Users map[string]*User
	Posts map[string]*Post
}

// queryResolver implements the Query interface
type queryResolver struct{ *Resolver }

func (r *queryResolver) GetUser(ctx context.Context, id string) (*User, error) {
	// 1. Context Auth Check
	token := ctx.Value("auth-token")
	if token != "secret" {
		return nil, fmt.Errorf("unauthorized")
	}

	// 2. Fetch Data
	if user, ok := r.Users[id]; ok {
		return user, nil
	}
	return nil, fmt.Errorf("user not found")
}

// userResolver implements nested fields on the User type
type userResolver struct{ *Resolver }

func (r *userResolver) Posts(ctx context.Context, obj *User) ([]*Post, error) {
	// Nested resolver: Fetches posts specifically for this user
	var result []*Post
	for _, p := range r.Posts {
		if p.AuthorID == obj.ID {
			result = append(result, p)
		}
	}
	return result, nil
}

// mutationResolver implements the Mutation interface
type mutationResolver struct{ *Resolver }

func (r *mutationResolver) CreateUser(ctx context.Context, name string) (*User, error) {
	id := strconv.Itoa(len(r.Users) + 1)
	user := &User{ID: id, Name: name}
	r.Users[id] = user
	return user, nil
}

// func main() {
// 	srv := handler.NewDefaultServer(generated.NewExecutableSchema(generated.Config{Resolvers: &Resolver{...}}))
// 	http.Handle("/graphql", AuthMiddleware(srv))
// 	http.ListenAndServe(":8080", nil)
// }
