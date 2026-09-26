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
	inPath := flag.String("in", "server.log", "Input log file")
	outPath := flag.String("out", "anomalies.csv", "Output anomalies file")
	threshold := flag.Int("threshold", 10, "Threshold for 404 errors")
	workers := flag.Int("workers", 4, "Number of concurrent parser workers")
	flag.Parse()

	file, err := os.Open(*inPath)
	if err != nil {
		log.Printf("Failed to open %s: %v. Please provide a valid input.", *inPath, err)
		return
	}
	defer file.Close()

	// Pattern: 192.168.1.1 - - [10/Oct/2023:13:55:36 -0700] "GET /index.html HTTP/1.1" 404 2326
	logPattern := regexp.MustCompile(`^(\d{1,3}(?:\.\d{1,3}){3}).*?"\s+(\d{3})\s+`)

	lines := make(chan string, 1000)
	type result struct {
		ip     string
		status string
	}
	results := make(chan result, 1000)

	var wg sync.WaitGroup

	// Start parser workers
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for line := range lines {
				matches := logPattern.FindStringSubmatch(line)
				if len(matches) == 3 {
					results <- result{ip: matches[1], status: matches[2]}
				}
			}
		}()
	}

	// Read lines
	go func() {
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			lines <- scanner.Text()
		}
		if err := scanner.Err(); err != nil {
			log.Printf("error reading file: %v", err)
		}
		close(lines)
	}()

	// Wait for workers to finish
	go func() {
		wg.Wait()
		close(results)
	}()

	// Aggregate errors
	errorCounts := make(map[string]int)
	for res := range results {
		if res.status == "404" {
			errorCounts[res.ip]++
		}
	}

	// Write output
	outFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("failed to create output: %v", err)
	}
	defer outFile.Close()

	outFile.WriteString("ip,error_count\n")
	anomaliesFound := 0
	for ip, count := range errorCounts {
		if count > *threshold {
			outFile.WriteString(fmt.Sprintf("%s,%d\n", ip, count))
			anomaliesFound++
		}
	}

	log.Printf("Anomaly detection complete. Found %d anomalies.", anomaliesFound)
}
