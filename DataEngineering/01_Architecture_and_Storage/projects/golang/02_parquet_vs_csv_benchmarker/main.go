package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/xitongsys/parquet-go-source/local"
	"github.com/xitongsys/parquet-go/parquet"
	"github.com/xitongsys/parquet-go/writer"
)

// Record represents a single row in our benchmark dataset.
// Parquet tags specify the schema, including efficient dictionary encoding for repeated strings.
type Record struct {
	ID       int64   `parquet:"name=id, type=INT64"`
	Value    float64 `parquet:"name=value, type=DOUBLE"`
	Category string  `parquet:"name=category, type=UTF8, encoding=PLAIN_DICTIONARY"`
}

func main() {
	numRecords := 1_000_000
	csvFile := "benchmark_data.csv"
	pqFile := "benchmark_data.parquet"

	fmt.Printf("Generating %d records for benchmark...\n", numRecords)

	// ==========================================
	// CSV Write Benchmark
	// ==========================================
	startCSV := time.Now()
	cf, err := os.Create(csvFile)
	if err != nil {
		log.Fatalf("Failed to create CSV file: %v", err)
	}
	
	cw := csv.NewWriter(cf)
	for i := 0; i < numRecords; i++ {
		// Simulating string conversion overhead for CSV
		record := []string{
			strconv.FormatInt(int64(i), 10),
			strconv.FormatFloat(float64(i)*1.5, 'f', -1, 64),
			"CategoryA",
		}
		if err := cw.Write(record); err != nil {
			log.Fatalf("Failed to write to CSV: %v", err)
		}
	}
	cw.Flush()
	if err := cf.Close(); err != nil {
		log.Fatalf("Failed to close CSV: %v", err)
	}
	csvTime := time.Since(startCSV)

	// ==========================================
	// Parquet Write Benchmark
	// ==========================================
	startPQ := time.Now()
	fw, err := local.NewLocalFileWriter(pqFile)
	if err != nil {
		log.Fatalf("Failed to create Parquet file: %v", err)
	}
	
	pw, err := writer.NewParquetWriter(fw, new(Record), 4) // 4 concurrent workers
	if err != nil {
		log.Fatalf("Failed to init Parquet writer: %v", err)
	}
	
	pw.RowGroupSize = 128 * 1024 * 1024 // 128MB
	pw.CompressionType = parquet.CompressionCodec_SNAPPY

	for i := 0; i < numRecords; i++ {
		rec := Record{
			ID:       int64(i),
			Value:    float64(i) * 1.5,
			Category: "CategoryA",
		}
		if err := pw.Write(rec); err != nil {
			log.Fatalf("Failed to write to Parquet: %v", err)
		}
	}
	
	if err := pw.WriteStop(); err != nil {
		log.Fatalf("Failed to stop Parquet writer: %v", err)
	}
	if err := fw.Close(); err != nil {
		log.Fatalf("Failed to close Parquet file: %v", err)
	}
	pqTime := time.Since(startPQ)

	// ==========================================
	// Size Benchmark
	// ==========================================
	cs, err := os.Stat(csvFile)
	if err != nil {
		log.Fatalf("Failed to stat CSV: %v", err)
	}
	ps, err := os.Stat(pqFile)
	if err != nil {
		log.Fatalf("Failed to stat Parquet: %v", err)
	}

	fmt.Printf("\n--- Write Benchmarks ---\n")
	fmt.Printf("CSV Write Time:     %v\n", csvTime)
	fmt.Printf("Parquet Write Time: %v\n", pqTime)

	fmt.Printf("\n--- File Size Benchmarks ---\n")
	fmt.Printf("CSV Size:     %.2f MB\n", float64(cs.Size())/(1024*1024))
	fmt.Printf("Parquet Size: %.2f MB\n", float64(ps.Size())/(1024*1024))

	// Cleanup
	_ = os.Remove(csvFile)
	_ = os.Remove(pqFile)
}
