package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"sync"
)

// Record represents a single row in the CSV
type Record struct {
	ID    string
	Name  string
	Score int
}

func main() {
	// Open input file (mocked by creating a sample file)
	createSampleCSV("input.csv")

	inputFile, err := os.Open("input.csv")
	if err != nil {
		log.Fatalf("Failed to open input file: %v", err)
	}
	defer inputFile.Close()

	// Create output file
	outputFile, err := os.Create("output.csv")
	if err != nil {
		log.Fatalf("Failed to create output file: %v", err)
	}
	defer outputFile.Close()

	reader := csv.NewReader(inputFile)
	writer := csv.NewWriter(outputFile)
	defer writer.Flush()

	// Read header
	header, err := reader.Read()
	if err != nil {
		log.Fatalf("Failed to read header: %v", err)
	}
	writer.Write(header)

	// Channels for concurrency
	recordsChan := make(chan Record, 100)
	filteredChan := make(chan Record, 100)

	var wg sync.WaitGroup
	// Start 4 worker goroutines to filter records (Score > 50)
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for rec := range recordsChan {
				if rec.Score > 50 {
					filteredChan <- rec
				}
			}
		}()
	}

	// Goroutine to read CSV and send to recordsChan
	go func() {
		for {
			row, err := reader.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Printf("Error reading row: %v", err)
				continue
			}
			
			score, _ := strconv.Atoi(row[2])
			recordsChan <- Record{ID: row[0], Name: row[1], Score: score}
		}
		close(recordsChan)
	}()

	// Goroutine to wait for workers and close filteredChan
	go func() {
		wg.Wait()
		close(filteredChan)
	}()

	// Read filtered records and write to output
	for rec := range filteredChan {
		err := writer.Write([]string{rec.ID, rec.Name, strconv.Itoa(rec.Score)})
		if err != nil {
			log.Printf("Error writing row: %v", err)
		}
	}
	fmt.Println("Processing complete. Check output.csv")
}

func createSampleCSV(filename string) {
	content := "ID,Name,Score\n1,Alice,85\n2,Bob,45\n3,Charlie,92\n4,Dave,30\n"
	os.WriteFile(filename, []byte(content), 0644)
}
