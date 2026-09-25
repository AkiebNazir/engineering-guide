package main

import "fmt"

func validateSchema(row map[string]interface{}) (bool, string) {
	if _, ok := row["id"].(int); !ok {
		return false, "Invalid type for 'id', expected int"
	}
	if _, ok := row["name"].(string); !ok {
		return false, "Invalid type for 'name', expected string"
	}
	return true, "Valid"
}

func main() {
	goodRow := map[string]interface{}{"id": 1, "name": "Alice"}
	badRow := map[string]interface{}{"id": "two", "name": "Bob"}

	if ok, msg := validateSchema(goodRow); ok {
		fmt.Println("Good Row:", msg)
	}
	if ok, msg := validateSchema(badRow); !ok {
		fmt.Println("Bad Row Error:", msg)
	}
}
