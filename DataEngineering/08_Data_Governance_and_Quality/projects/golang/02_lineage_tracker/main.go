package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// OpenLineage Core Types
// In a real project, you might generate these from the OpenLineage JSON schemas.

type SchemaField struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type SchemaDatasetFacet struct {
	Fields []SchemaField `json:"fields"`
}

type DatasetFacets struct {
	Schema *SchemaDatasetFacet `json:"schema,omitempty"`
}

type Dataset struct {
	Namespace string        `json:"namespace"`
	Name      string        `json:"name"`
	Facets    DatasetFacets `json:"facets"`
}

type Job struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
}

type Run struct {
	RunID string `json:"runId"`
}

type RunEvent struct {
	EventType string    `json:"eventType"`
	EventTime string    `json:"eventTime"`
	Run       Run       `json:"run"`
	Job       Job       `json:"job"`
	Inputs    []Dataset `json:"inputs,omitempty"`
	Outputs   []Dataset `json:"outputs,omitempty"`
	Producer  string    `json:"producer"`
}

// emitLineage simulates pushing an OpenLineage event to a backend (like Marquez)
func emitLineage(event RunEvent, endpoint string) error {
	payload, err := json.MarshalIndent(event, "", "  ")
	if err != nil {
		return err
	}

	// For demonstration, we print the payload that would be sent.
	fmt.Printf("Emitting OpenLineage Event to %s:\n%s\n\n", endpoint, string(payload))

	// In a real scenario:
	/*
	req, _ := http.NewRequest("POST", endpoint, bytes.NewBuffer(payload))
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}
	*/
	return nil
}

func main() {
	producerURL := "https://github.com/OpenLineage/OpenLineage/tree/main/integration/golang-custom"
	backendURL := "http://localhost:5000/api/v1/lineage" // Example Marquez HTTP endpoint

	// Define datasets
	inputDB := Dataset{
		Namespace: "postgres://oltp-db-prod:5432",
		Name:      "public.raw_transactions",
		Facets: DatasetFacets{
			Schema: &SchemaDatasetFacet{
				Fields: []SchemaField{
					{Name: "txn_id", Type: "INT"},
					{Name: "amount", Type: "DECIMAL"},
				},
			},
		},
	}

	outputWarehouse := Dataset{
		Namespace: "snowflake://warehouse-prod",
		Name:      "sales_mart.fct_daily_sales",
	}

	// Define Job & Run
	job := Job{
		Namespace: "golang_microservices",
		Name:      "daily_aggregator_worker",
	}
	runID := uuid.New().String()

	// 1. Emit START event
	startEvent := RunEvent{
		EventType: "START",
		EventTime: time.Now().UTC().Format(time.RFC3339),
		Run:       Run{RunID: runID},
		Job:       job,
		Inputs:    []Dataset{inputDB},
		Producer:  producerURL,
	}

	if err := emitLineage(startEvent, backendURL); err != nil {
		log.Fatalf("Failed to emit START event: %v", err)
	}

	// Simulate work...
	fmt.Println("Running data processing logic...")
	time.Sleep(1 * time.Second)

	// 2. Emit COMPLETE event
	completeEvent := RunEvent{
		EventType: "COMPLETE",
		EventTime: time.Now().UTC().Format(time.RFC3339),
		Run:       Run{RunID: runID},
		Job:       job,
		Outputs:   []Dataset{outputWarehouse},
		Producer:  producerURL,
	}

	if err := emitLineage(completeEvent, backendURL); err != nil {
		log.Fatalf("Failed to emit COMPLETE event: %v", err)
	}
}
