// REAL-WORLD EXAMPLE: graphql-go (External 2)
// Demonstrates: Code-first schema, Object types, Input Arguments, Sub-selection.
package main

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/graphql-go/graphql"
)

type Product struct {
	ID    string  `json:"id"`
	Name  string  `json:"name"`
	Price float64 `json:"price"`
}

var db = map[string]Product{
	"1": {ID: "1", Name: "Laptop", Price: 1200.50},
	"2": {ID: "2", Name: "Mouse", Price: 25.00},
}

var productType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Product",
	Fields: graphql.Fields{
		"id":    &graphql.Field{Type: graphql.String},
		"name":  &graphql.Field{Type: graphql.String},
		"price": &graphql.Field{Type: graphql.Float},
	},
})

var queryType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Query",
	Fields: graphql.Fields{
		"product": &graphql.Field{
			Type:        productType,
			Description: "Get product by ID",
			Args: graphql.FieldConfigArgument{
				"id": &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.String)},
			},
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				id := p.Args["id"].(string)
				
				// Optional: Check Context for Auth
				authHeader := p.Context.Value("Authorization")
				if authHeader == nil {
					// return nil, fmt.Errorf("Unauthorized")
				}

				if prod, ok := db[id]; ok {
					return prod, nil
				}
				return nil, nil // Return null if not found (per GraphQL spec)
			},
		},
		"products": &graphql.Field{
			Type:        graphql.NewList(productType),
			Description: "Get all products",
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				var list []Product
				for _, prod := range db {
					list = append(list, prod)
				}
				return list, nil
			},
		},
	},
})

var mutationType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Mutation",
	Fields: graphql.Fields{
		"createProduct": &graphql.Field{
			Type: productType,
			Args: graphql.FieldConfigArgument{
				"name":  &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.String)},
				"price": &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.Float)},
			},
			Resolve: func(p graphql.ResolveParams) (interface{}, error) {
				name := p.Args["name"].(string)
				price := p.Args["price"].(float64)

				id := strconv.Itoa(len(db) + 1)
				newProd := Product{ID: id, Name: name, Price: price}
				db[id] = newProd
				return newProd, nil
			},
		},
	},
})

func main() {
	schema, _ := graphql.NewSchema(graphql.SchemaConfig{
		Query:    queryType,
		Mutation: mutationType,
	})

	http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		// Basic Auth extraction logic could go here and be passed via context
		
		var req struct {
			Query     string                 `json:"query"`
			Operation string                 `json:"operationName"`
			Variables map[string]interface{} `json:"variables"`
		}
		json.NewDecoder(r.Body).Decode(&req)

		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			OperationName:  req.Operation,
			VariableValues: req.Variables,
			Context:        r.Context(), // Pass HTTP context down to resolvers!
		})
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})

	http.ListenAndServe(":8080", nil)
}
