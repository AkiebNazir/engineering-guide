package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
)

// Flattener provides mechanisms to flatten deeply nested JSON structures.
type Flattener struct {
	Separator string
}

// NewFlattener creates a new Flattener with a specified separator.
func NewFlattener(separator string) *Flattener {
	return &Flattener{
		Separator: separator,
	}
}

// FlattenMap takes a nested map and flattens it.
func (f *Flattener) FlattenMap(prefix string, nested map[string]interface{}, flat map[string]interface{}) {
	for k, v := range nested {
		newKey := k
		if prefix != "" {
			newKey = prefix + f.Separator + k
		}

		switch child := v.(type) {
		case map[string]interface{}:
			f.FlattenMap(newKey, child, flat)
		case []interface{}:
			for i, item := range child {
				arrKey := fmt.Sprintf("%s%s%d", newKey, f.Separator, i)
				switch arrChild := item.(type) {
				case map[string]interface{}:
					f.FlattenMap(arrKey, arrChild, flat)
				default:
					flat[arrKey] = arrChild
				}
			}
		default:
			flat[newKey] = v
		}
	}
}

// FlattenJSONBytes takes a raw JSON byte slice and returns a flattened map.
func (f *Flattener) FlattenJSONBytes(data []byte) (map[string]interface{}, error) {
	var nested map[string]interface{}
	if err := json.Unmarshal(data, &nested); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	flat := make(map[string]interface{})
	f.FlattenMap("", nested, flat)
	return flat, nil
}

func main() {
	rawJSON := []byte(`{
		"user_id": 1024,
		"profile": {
			"name": "Alice",
			"age": 30,
			"contact": {
				"email": "alice@example.com",
				"phone": "555-1234"
			}
		},
		"tags": ["premium", "active"]
	}`)

	flattener := NewFlattener("_")
	
	flatData, err := flattener.FlattenJSONBytes(rawJSON)
	if err != nil {
		log.Fatalf("Error flattening JSON: %v", err)
	}

	output, err := json.MarshalIndent(flatData, "", "  ")
	if err != nil {
		log.Fatalf("Error marshaling flattened data: %v", err)
	}

	fmt.Println("Flattened JSON Output:")
	os.Stdout.Write(output)
	fmt.Println()
}
