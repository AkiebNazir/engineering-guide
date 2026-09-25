import os

base_py = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/08_Data_Governance_and_Quality/projects/python"
base_go = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/08_Data_Governance_and_Quality/projects/golang"

py_files = {
    "01_data_quality_assertions/main.py": """import pandas as pd
import numpy as np

def run_data_quality_checks(df):
    errors = []
    if df['id'].isnull().any():
        errors.append("Assertion Failed: 'id' contains nulls.")
    if not df['id'].is_unique:
        errors.append("Assertion Failed: 'id' is not unique.")
    if (df['age'] < 0).any():
        errors.append("Assertion Failed: 'age' contains negative values.")
    return errors

df = pd.DataFrame({'id': [1, 2, 2], 'age': [25, -5, 30]})
print("Running Data Quality Assertions...")
errors = run_data_quality_checks(df)
if errors:
    for e in errors:
        print(e)
else:
    print("All checks passed!")
""",
    "02_lineage_tracker/main.py": """class LineageNode:
    def __init__(self, name):
        self.name = name
        self.downstream = []

    def add_downstream(self, node):
        self.downstream.append(node)

    def print_lineage(self, level=0):
        print("  " * level + "-> " + self.name)
        for child in self.downstream:
            child.print_lineage(level + 1)

raw = LineageNode("raw_transactions")
stg = LineageNode("stg_transactions")
fct = LineageNode("fct_daily_sales")
mart = LineageNode("mart_finance_dashboard")

raw.add_downstream(stg)
stg.add_downstream(fct)
fct.add_downstream(mart)

print("Data Lineage Graph:")
raw.print_lineage()
""",
    "03_metadata_catalog_builder/main.py": """import json

catalog = {
    "tables": [
        {
            "name": "fct_sales",
            "owner": "data_engineering@company.com",
            "description": "Daily aggregated sales facts.",
            "columns": [
                {"name": "date", "type": "DATE", "description": "Transaction date"},
                {"name": "total_amount", "type": "FLOAT", "description": "Sum of sales"}
            ]
        }
    ]
}

with open('catalog.json', 'w') as f:
    json.dump(catalog, f, indent=4)

print("Generated metadata catalog: catalog.json")
""",
    "04_anomaly_alerting/main.py": """import numpy as np

def detect_anomaly(current_value, historical_mean, historical_std, threshold=3):
    z_score = abs((current_value - historical_mean) / historical_std)
    if z_score > threshold:
        return f"ALERT: Anomaly detected! Value {current_value} is {z_score:.2f} std devs away from mean."
    return "Status Normal."

historical_data = [100, 105, 95, 110, 90, 102]
mean = np.mean(historical_data)
std = np.std(historical_data)

print(detect_anomaly(500, mean, std))  # Sudden spike
print(detect_anomaly(100, mean, std))  # Normal
""",
    "05_schema_validation_gate/main.py": """def validate_schema(row, expected_schema):
    for col, expected_type in expected_schema.items():
        if col not in row:
            return False, f"Missing column: {col}"
        if not isinstance(row[col], expected_type):
            return False, f"Type mismatch for {col}: expected {expected_type}, got {type(row[col])}"
    return True, "Valid"

schema = {"id": int, "name": str, "is_active": bool}
good_row = {"id": 1, "name": "Alice", "is_active": True}
bad_row = {"id": "two", "name": "Bob", "is_active": "yes"}

print("Good Row:", validate_schema(good_row, schema))
print("Bad Row:", validate_schema(bad_row, schema))
"""
}

go_files = {
    "01_data_quality_assertions/main.go": """package main

import "fmt"

type Row struct {
	ID  int
	Age int
}

func checkQuality(data []Row) []string {
	var errors []string
	seenIDs := make(map[int]bool)

	for _, row := range data {
		if seenIDs[row.ID] {
			errors = append(errors, fmt.Sprintf("Duplicate ID found: %d", row.ID))
		}
		seenIDs[row.ID] = true

		if row.Age < 0 {
			errors = append(errors, fmt.Sprintf("Negative age found for ID %d", row.ID))
		}
	}
	return errors
}

func main() {
	data := []Row{{1, 25}, {2, -5}, {2, 30}}
	errors := checkQuality(data)

	if len(errors) > 0 {
		for _, e := range errors {
			fmt.Println("Assertion Failed:", e)
		}
	} else {
		fmt.Println("All data quality checks passed!")
	}
}
""",
    "02_lineage_tracker/main.go": """package main

import (
	"fmt"
	"strings"
)

type Node struct {
	Name       string
	Downstream []*Node
}

func (n *Node) PrintLineage(level int) {
	fmt.Printf("%s-> %s\n", strings.Repeat("  ", level), n.Name)
	for _, child := range n.Downstream {
		child.PrintLineage(level + 1)
	}
}

func main() {
	raw := &Node{Name: "raw_transactions"}
	stg := &Node{Name: "stg_transactions"}
	fct := &Node{Name: "fct_daily_sales"}

	raw.Downstream = append(raw.Downstream, stg)
	stg.Downstream = append(stg.Downstream, fct)

	fmt.Println("Data Lineage Graph:")
	raw.PrintLineage(0)
}
""",
    "03_metadata_catalog_builder/main.go": """package main

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
""",
    "04_anomaly_alerting/main.go": """package main

import (
	"fmt"
	"math"
)

func detectAnomaly(val, mean, std float64, threshold float64) string {
	zScore := math.Abs((val - mean) / std)
	if zScore > threshold {
		return fmt.Sprintf("ALERT: Anomaly! Value %.2f is %.2f std devs away.", val, zScore)
	}
	return "Status Normal."
}

func main() {
	mean := 100.0
	std := 5.0
	fmt.Println(detectAnomaly(500.0, mean, std, 3.0)) // Spike
	fmt.Println(detectAnomaly(102.0, mean, std, 3.0)) // Normal
}
""",
    "05_schema_validation_gate/main.go": """package main

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
"""
}

for filepath, content in py_files.items():
    with open(os.path.join(base_py, filepath), "w") as f:
        f.write(content)

for filepath, content in go_files.items():
    with open(os.path.join(base_go, filepath), "w") as f:
        f.write(content)

print("Generated Topic 08 code!")
