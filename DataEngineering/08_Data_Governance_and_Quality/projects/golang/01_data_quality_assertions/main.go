package main

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
