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

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type SalesRecord struct {
	Date    string
	Product string
	Amount  float64
}

func main() {
	bucket := flag.String("bucket", "", "S3 bucket containing the sales data")
	key := flag.String("key", "", "S3 key for the sales data CSV")
	outPath := flag.String("out", "aggregated_sales.csv", "Local output path for aggregated data")
	flag.Parse()

	if *bucket == "" || *key == "" {
		log.Println("Note: Bucket and key not provided. Run with -bucket <bucket> -key <key>")
		log.Println("Demonstrating real-world AWS S3 usage, exiting early as no input is provided.")
		return
	}

	ctx := context.Background()

	// Load AWS config
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatalf("unable to load SDK config, %v", err)
	}

	s3Client := s3.NewFromConfig(cfg)

	// Stream file from S3
	log.Printf("Downloading %s/%s from S3...", *bucket, *key)
	resp, err := s3Client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: bucket,
		Key:    key,
	})
	if err != nil {
		log.Fatalf("failed to get object, %v", err)
	}
	defer resp.Body.Close()

	reader := csv.NewReader(resp.Body)
	
	// Read header
	if _, err := reader.Read(); err != nil {
		log.Fatalf("failed to read header, %v", err)
	}

	// Aggregate map: map[date]map[product]amount
	aggregated := make(map[string]map[string]float64)

	log.Println("Processing records...")
	recordCount := 0
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("error reading record: %v", err)
			continue
		}

		date := record[0]
		product := record[1]
		amount, err := strconv.ParseFloat(record[2], 64)
		if err != nil {
			continue // skip invalid amounts
		}

		if aggregated[date] == nil {
			aggregated[date] = make(map[string]float64)
		}
		aggregated[date][product] += amount
		recordCount++
	}

	log.Printf("Processed %d records. Writing output to %s...", recordCount, *outPath)

	outFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("failed to create output file: %v", err)
	}
	defer outFile.Close()

	writer := csv.NewWriter(outFile)
	defer writer.Flush()

	// Write header
	writer.Write([]string{"date", "product", "total_amount"})

	for date, products := range aggregated {
		for product, total := range products {
			writer.Write([]string{
				date,
				product,
				fmt.Sprintf("%.2f", total),
			})
		}
	}

	log.Println("Aggregation completed successfully.")
}
