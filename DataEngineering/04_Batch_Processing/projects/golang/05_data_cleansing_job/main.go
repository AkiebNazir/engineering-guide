package main

import (
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

// Record represents a single row
type Record []string

func main() {
	bucket := flag.String("bucket", "", "S3 bucket for input data")
	key := flag.String("key", "", "S3 key for dirty CSV data")
	outPath := flag.String("out", "cleaned_data.csv", "Local path for cleaned data")
	workers := flag.Int("workers", 4, "Number of concurrent workers for cleansing")
	flag.Parse()

	if *bucket == "" || *key == "" {
		log.Println("Note: Bucket and key not provided. Run with -bucket <bucket> -key <key>")
		log.Println("Demonstrating real-world concurrency and S3 streaming, exiting early.")
		return
	}

	ctx := context.Background()
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatalf("failed to load AWS config: %v", err)
	}

	s3Client := s3.NewFromConfig(cfg)

	log.Printf("Streaming %s/%s from S3...", *bucket, *key)
	resp, err := s3Client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: bucket,
		Key:    key,
	})
	if err != nil {
		log.Fatalf("failed to fetch object from S3: %v", err)
	}
	defer resp.Body.Close()

	reader := csv.NewReader(resp.Body)

	// Read header
	header, err := reader.Read()
	if err != nil {
		log.Fatalf("failed to read header: %v", err)
	}

	outFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("failed to create output file: %v", err)
	}
	defer outFile.Close()

	writer := csv.NewWriter(outFile)
	defer writer.Flush()
	if err := writer.Write(header); err != nil {
		log.Fatalf("failed to write header: %v", err)
	}

	// Channels for pipeline
	jobs := make(chan Record, 100)
	results := make(chan Record, 100)

	var wg sync.WaitGroup

	// Start workers
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for rec := range jobs {
				cleaned := cleanRecord(rec)
				if cleaned != nil {
					results <- cleaned
				}
			}
		}()
	}

	// Read and send to jobs channel
	go func() {
		for {
			rec, err := reader.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Printf("error reading record: %v", err)
				continue
			}
			jobs <- rec
		}
		close(jobs)
	}()

	// Wait for workers to finish and close results
	go func() {
		wg.Wait()
		close(results)
	}()

	// Write results
	processedCount := 0
	for rec := range results {
		if err := writer.Write(rec); err != nil {
			log.Printf("error writing record: %v", err)
		}
		processedCount++
	}

	log.Printf("Data cleansing complete. Cleaned records written: %d", processedCount)
}

func cleanRecord(rec Record) Record {
	if len(rec) < 4 {
		return nil
	}

	// Clean name
	name := strings.TrimSpace(rec[1])
	if name == "" {
		name = "Unknown"
	}

	// Clean price
	priceStr := rec[2]
	if price, err := strconv.ParseFloat(priceStr, 64); err != nil {
		priceStr = "0.00" // Default for invalid price
	} else {
		priceStr = fmt.Sprintf("%.2f", price)
	}

	// Clean date (trying multiple formats)
	dateStr := rec[3]
	parsedDate, err1 := time.Parse("2006-01-02", dateStr)
	if err1 != nil {
		parsedDate, err1 = time.Parse("01/02/2006", dateStr)
	}

	if err1 != nil {
		// If date is invalid, drop the record entirely
		return nil
	}
	
	// Normalize date
	dateStr = parsedDate.Format("2006-01-02")

	return Record{rec[0], name, priceStr, dateStr}
}
