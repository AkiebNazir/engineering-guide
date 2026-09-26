package main

import (
	"encoding/csv"
	"flag"
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
	inPath := flag.String("in", "input.csv", "Input CSV file path")
	outPath := flag.String("out", "output.csv", "Output CSV file path")
	threshold := flag.Int("threshold", 50, "Score threshold to keep records")
	workers := flag.Int("workers", 4, "Number of worker goroutines")
	flag.Parse()

	inputFile, err := os.Open(*inPath)
	if err != nil {
		log.Printf("Failed to open input file %s: %v. Please provide a valid input.", *inPath, err)
		return
	}
	defer inputFile.Close()

	outputFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("Failed to create output file: %v", err)
	}
	defer outputFile.Close()

	reader := csv.NewReader(inputFile)
	writer := csv.NewWriter(outputFile)
	defer writer.Flush()

	// Read and write header
	header, err := reader.Read()
	if err != nil {
		log.Fatalf("Failed to read header: %v", err)
	}
	if err := writer.Write(header); err != nil {
		log.Fatalf("Failed to write header: %v", err)
	}

	recordsChan := make(chan Record, 1000)
	filteredChan := make(chan Record, 1000)

	var wg sync.WaitGroup

	// Start worker goroutines
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for rec := range recordsChan {
				if rec.Score > *threshold {
					filteredChan <- rec
				}
			}
		}()
	}

	// Goroutine to read CSV
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
			
			score, err := strconv.Atoi(row[2])
			if err != nil {
				log.Printf("Invalid score for ID %s: %v", row[0], err)
				continue
			}
			
			recordsChan <- Record{ID: row[0], Name: row[1], Score: score}
		}
		close(recordsChan)
	}()

	// Wait for workers to finish
	go func() {
		wg.Wait()
		close(filteredChan)
	}()

	// Write filtered records
	writtenCount := 0
	for rec := range filteredChan {
		err := writer.Write([]string{rec.ID, rec.Name, strconv.Itoa(rec.Score)})
		if err != nil {
			log.Printf("Error writing row: %v", err)
		} else {
			writtenCount++
		}
	}
	
	fmt.Printf("Processing complete. Wrote %d records to %s\n", writtenCount, *outPath)
}
