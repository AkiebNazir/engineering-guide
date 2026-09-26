package main

import (
	"fmt"
	"log"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v5"
)

// defineSchema compiles a JSON schema from a string.
// In production, this would be loaded from a Schema Registry.
func defineSchema() (*jsonschema.Schema, error) {
	schemaStr := `{
		"$schema": "https://json-schema.org/draft/2020-12/schema",
		"title": "User Event",
		"type": "object",
		"properties": {
			"event_id": {
				"type": "string",
				"minLength": 10
			},
			"user_id": {
				"type": "integer",
				"minimum": 1
			},
			"is_active": {
				"type": "boolean"
			}
		},
		"required": ["event_id", "user_id", "is_active"]
	}`

	compiler := jsonschema.NewCompiler()
	if err := compiler.AddResource("schema.json", strings.NewReader(schemaStr)); err != nil {
		return nil, err
	}
	
	return compiler.Compile("schema.json")
}

// processEvent validates a raw JSON string against the compiled schema.
func processEvent(schema *jsonschema.Schema, rawJSON string) {
	fmt.Printf("\nProcessing payload:\n%s\n", rawJSON)

	// jsonschema expects an unmarshaled map[string]interface{} or []interface{}
	// Or we can validate directly from a string using string reader
	v, err := jsonschema.UnmarshalJSON(strings.NewReader(rawJSON))
	if err != nil {
		fmt.Printf("❌ Invalid JSON format: %v\n", err)
		return
	}

	err = schema.Validate(v)
	if err != nil {
		fmt.Println("❌ Schema Validation Failed. Routing to DLQ...")
		// Print detailed validation errors
		fmt.Printf("Validation Errors:\n%#v\n", err)
	} else {
		fmt.Println("✅ Schema Validation Passed! Proceeding to ingest event.")
	}
}

func main() {
	schema, err := defineSchema()
	if err != nil {
		log.Fatalf("Failed to compile JSON schema: %v", err)
	}

	// Good Payload
	goodPayload := `{
		"event_id": "evt_123456789",
		"user_id": 42,
		"is_active": true,
		"platform": "web"
	}`

	// Bad Payload: missing required user_id, invalid type for is_active, event_id too short
	badPayload := `{
		"event_id": "evt_123",
		"is_active": "yes"
	}`

	processEvent(schema, goodPayload)
	processEvent(schema, badPayload)
}
