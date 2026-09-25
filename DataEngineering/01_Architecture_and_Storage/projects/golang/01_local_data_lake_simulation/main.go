package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

type Record struct {
	ID        int       `json:"id"`
	Data      string    `json:"data"`
	Timestamp time.Time `json:"timestamp"`
}

func main() {
	baseDir := "data_lake/raw"
	year, month := 2023, 10
	partitionDir := filepath.Join(baseDir, fmt.Sprintf("year=%d/month=%02d", year, month))

	if err := os.MkdirAll(partitionDir, 0755); err != nil {
		panic(err)
	}

	records := []Record{
		{ID: 1, Data: "Event A", Timestamp: time.Now()},
		{ID: 2, Data: "Event B", Timestamp: time.Now()},
	}

	file, err := os.Create(filepath.Join(partitionDir, "data.json"))
	if err != nil {
		panic(err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	if err := encoder.Encode(records); err != nil {
		panic(err)
	}
	fmt.Println("Data lake simulation complete. Data written to:", partitionDir)
}
