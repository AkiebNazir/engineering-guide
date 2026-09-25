package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"regexp"
	"sync"
)

func main() {
	// Create sample log file
	logFilename := "sample.log"
	createSampleLog(logFilename)

	file, err := os.Open(logFilename)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	defer file.Close()

	// Regex to extract error messages
	errRegex := regexp.MustCompile(`ERROR:\s+(.*)`)

	linesChan := make(chan string, 100)
	errChan := make(chan string, 100)

	var wg sync.WaitGroup
	// Start 4 worker goroutines for log parsing
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for line := range linesChan {
				matches := errRegex.FindStringSubmatch(line)
				if len(matches) > 1 {
					errChan <- matches[1] // Extract the actual error message
				}
			}
		}()
	}

	// Read lines and distribute to workers
	go func() {
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			linesChan <- scanner.Text()
		}
		close(linesChan)
	}()

	// Wait for workers to finish
	go func() {
		wg.Wait()
		close(errChan)
	}()

	// Aggregate error counts
	errorCounts := make(map[string]int)
	for errMsg := range errChan {
		errorCounts[errMsg]++
	}

	fmt.Println("Error Summary:")
	for msg, count := range errorCounts {
		fmt.Printf("- %s: %d\n", msg, count)
	}
}

func createSampleLog(filename string) {
	content := `INFO: Application started
ERROR: Connection timeout
INFO: User logged in
ERROR: Database unreachable
WARN: High memory usage
ERROR: Connection timeout
INFO: Job completed
ERROR: Database unreachable
ERROR: Database unreachable`
	os.WriteFile(filename, []byte(content), 0644)
}
