package main

import (
	"encoding/json"
	"net/http"

	"github.com/graphql-go/graphql"
)

var userType = graphql.NewObject(graphql.ObjectConfig{
	Name: "User",
	Fields: graphql.Fields{
		"id":   &graphql.Field{Type: graphql.String},
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
				id, ok := p.Args["id"].(string)
				if !ok {
					return nil, nil
				}
				// Mocked DB fetch
				return map[string]string{"id": id, "name": "Alice"}, nil
			},
		},
	},
})

func main() {
	schema, _ := graphql.NewSchema(graphql.SchemaConfig{
		Query: rootQuery,
	})

	http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			Query string `json:"query"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		result := graphql.Do(graphql.Params{
			Schema:        schema,
			RequestString: req.Query,
		})
		json.NewEncoder(w).Encode(result)
	})
	
	http.ListenAndServe(":8080", nil)
}
