package main

import (
	"encoding/json"
	"fmt"
)

func flatten(prefix string, nested map[string]interface{}, flat map[string]interface{}) {
	for k, v := range nested {
		newKey := k
		if prefix != "" {
			newKey = prefix + "_" + k
		}
		
		switch child := v.(type) {
		case map[string]interface{}:
			flatten(newKey, child, flat)
		default:
			flat[newKey] = v
		}
	}
}

func main() {
	raw := `{"user_id": 1, "profile": {"name": "Alice", "age": 30}}`
	var nested map[string]interface{}
	json.Unmarshal([]byte(raw), &nested)

	flat := make(map[string]interface{})
	flatten("", nested, flat)

	fmt.Println("Flattened Map:")
	for k, v := range flat {
		fmt.Printf("%s: %v
", k, v)
	}
}
