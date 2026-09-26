package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"regexp"
	"sync"
)

func main() {
	inPath := flag.String("in", "application.log", "Input log file")
	workers := flag.Int("workers", 4, "Number of worker goroutines")
	flag.Parse()

	file, err := os.Open(*inPath)
	if err != nil {
		log.Printf("Failed to open %s: %v. Please provide a valid log file.", *inPath, err)
		return
	}
	defer file.Close()

	// Regex to extract error messages, accommodating variations in log format
	errRegex := regexp.MustCompile(`(?:ERROR|ERR)[\s:]+(.+)`)

	linesChan := make(chan string, 1000)
	errChan := make(chan string, 1000)

	var wg sync.WaitGroup

	// Start worker goroutines
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for line := range linesChan {
				if matches := errRegex.FindStringSubmatch(line); len(matches) > 1 {
					errChan <- matches[1]
				}
			}
		}()
	}

	// Read lines concurrently
	go func() {
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			linesChan <- scanner.Text()
		}
		if err := scanner.Err(); err != nil {
			log.Printf("Error reading file: %v", err)
		}
		close(linesChan)
	}()

	// Close error channel when all workers finish
	go func() {
		wg.Wait()
		close(errChan)
	}()

	// Aggregate errors
	errorCounts := make(map[string]int)
	for errMsg := range errChan {
		errorCounts[errMsg]++
	}

	fmt.Println("Error Summary:")
	for msg, count := range errorCounts {
		fmt.Printf("[%d times] %s\n", count, msg)
	}
}
