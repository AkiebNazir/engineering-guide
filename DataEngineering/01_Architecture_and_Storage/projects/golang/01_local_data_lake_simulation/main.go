package main

import (
	"fmt"
	"log"
	"math/rand"
	"path/filepath"
	"time"

	"github.com/xitongsys/parquet-go-source/local"
	"github.com/xitongsys/parquet-go/parquet"
	"github.com/xitongsys/parquet-go/writer"
)

// EventRecord defines the structure of our data lake events.
type EventRecord struct {
	ID        int64  `parquet:"name=id, type=INT64"`
	Event     string `parquet:"name=event, type=UTF8, encoding=PLAIN_DICTIONARY"`
	Timestamp int64  `parquet:"name=timestamp, type=INT64, logicaltype=TIMESTAMP_MILLIS"`
}

func main() {
	baseDir := "data_lake/raw"
	year, month, day := 2023, 10, 1
	partitionDir := filepath.Join(baseDir, fmt.Sprintf("year=%d/month=%02d/day=%02d", year, month, day))

	// Create partition directory structure
	// This would typically be handled by a storage layer (S3) or an abstraction like PyArrow
	// but here we manually create the directories for local simulation.
	
	// Create local Parquet file writer
	filePath := filepath.Join(partitionDir, "events.parquet")
	fw, err := local.NewLocalFileWriter(filePath)
	if err != nil {
		log.Fatalf("Failed to create local file: %v", err)
	}
	defer fw.Close()

	// Initialize Parquet writer
	pw, err := writer.NewParquetWriter(fw, new(EventRecord), 4)
	if err != nil {
		log.Fatalf("Failed to create Parquet writer: %v", err)
	}

	pw.RowGroupSize = 128 * 1024 * 1024 // 128 MB
	pw.CompressionType = parquet.CompressionCodec_SNAPPY

	events := []string{"login", "logout", "purchase", "view"}

	// Generate and write synthetic data
	for i := 0; i < 1000; i++ {
		record := EventRecord{
			ID:        int64(i),
			Event:     events[rand.Intn(len(events))],
			Timestamp: time.Now().UnixMilli(),
		}
		if err := pw.Write(record); err != nil {
			log.Fatalf("Write error: %v", err)
		}
	}

	if err := pw.WriteStop(); err != nil {
		log.Fatalf("WriteStop error: %v", err)
	}

	fmt.Println("Data lake simulation complete. Parquet data written to:", filePath)
}
