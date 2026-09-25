package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Column struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Description string `json:"description"`
}

type Table struct {
	Name        string   `json:"name"`
	Owner       string   `json:"owner"`
	Columns     []Column `json:"columns"`
}

func main() {
	catalog := map[string][]Table{
		"tables": {
			{
				Name:  "fct_sales",
				Owner: "data_engineering@company.com",
				Columns: []Column{
					{"date", "DATE", "Transaction date"},
					{"amount", "FLOAT", "Total sale amount"},
				},
			},
		},
	}

	file, _ := os.Create("catalog.json")
	defer file.Close()
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	encoder.Encode(catalog)
	fmt.Println("Generated metadata catalog: catalog.json")
}
