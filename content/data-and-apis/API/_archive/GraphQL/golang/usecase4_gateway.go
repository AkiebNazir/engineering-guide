package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"github.com/graphql-go/graphql"
)

// LegacyRESTUser represents the payload from an old REST API
type LegacyRESTUser struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

var userType = graphql.NewObject(graphql.ObjectConfig{
	Name: "User",
	Fields: graphql.Fields{
		"id":   &graphql.Field{Type: graphql.Int},
		"name": &graphql.Field{Type: graphql.String},
	},
})

var rootQuery = graphql.NewObject(graphql.ObjectConfig{
	Name: "RootQuery",
	Fields: graphql.Fields{
		"user": &graphql.Field{
			Type: userType,
			Args: graphql.FieldConfigArgument{
				"id": &graphql.ArgumentConfig{Type: graphql.String},
			},
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				id := p.Args["id"].(string)
				// Wrapping a legacy REST API call
				url := fmt.Sprintf("https://jsonplaceholder.typicode.com/users/%s", id)
				resp, err := http.Get(url)
				if err != nil {
					return nil, err
				}
				defer resp.Body.Close()

				var user LegacyRESTUser
				json.NewDecoder(resp.Body).Decode(&user)
				return user, nil
			},
		},
	},
})

func main() {
	schema, _ := graphql.NewSchema(graphql.SchemaConfig{Query: rootQuery})

	query := `{ user(id: "1") { id name } }`
	result := graphql.Do(graphql.Params{
		Schema:        schema,
		RequestString: query,
	})

	fmt.Printf("Gateway Result fetching from REST: %v\n", result.Data)
}
