package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/xitongsys/parquet-go-source/local"
	"github.com/xitongsys/parquet-go/parquet"
	"github.com/xitongsys/parquet-go/writer"
)

type Record struct {
	ID    int64  `parquet:"name=id, type=INT64"`
	Value string `parquet:"name=value, type=UTF8, encoding=PLAIN_DICTIONARY"`
}

func main() {
	numRecords := 10000
	csvFile := "data.csv"
	pqFile := "data.parquet"

	// CSV benchmark
	start := time.Now()
	cf, _ := os.Create(csvFile)
	cw := csv.NewWriter(cf)
	for i := 0; i < numRecords; i++ {
		cw.Write([]string{strconv.Itoa(i), fmt.Sprintf("value-%d", i)})
	}
	cw.Flush()
	cf.Close()
	csvTime := time.Since(start)

	// Parquet benchmark
	start = time.Now()
	fw, _ := local.NewLocalFileWriter(pqFile)
	pw, _ := writer.NewParquetWriter(fw, new(Record), 4)
	pw.RowGroupSize = 128 * 1024 * 1024
	pw.CompressionType = parquet.CompressionCodec_SNAPPY
	for i := 0; i < numRecords; i++ {
		pw.Write(Record{ID: int64(i), Value: fmt.Sprintf("value-%d", i)})
	}
	pw.WriteStop()
	fw.Close()
	pqTime := time.Since(start)

	cs, _ := os.Stat(csvFile)
	ps, _ := os.Stat(pqFile)

	fmt.Printf("CSV file: %v time, %d bytes\n", csvTime, cs.Size())
	fmt.Printf("Parquet file: %v time, %d bytes\n", pqTime, ps.Size())
}
