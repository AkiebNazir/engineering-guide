/*
LEVEL 08 (interop) - encoding/csv with os and path/filepath together

You will learn
  - a real directory-of-CSV-files pipeline: os.WriteFile to create fixtures,
    os.ReadDir to list them, filepath.Join/Ext to filter and build paths
  - each file is opened with os.Open and handed straight to csv.NewReader -
    csv.Reader only needs an io.Reader, it does not care that it is a file
  - aggregating across multiple files with the streaming Read() idiom from
    level 3, now applied file-by-file instead of record-by-record in one file

Run: go run ./GoStdLib/10_encoding_csv/level_08_os_interop
*/

package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strconv"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-csv-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	files := map[string]string{
		"jan.csv":   "day,units\n1,10\n2,5\n",
		"feb.csv":   "day,units\n1,7\n",
		"notes.txt": "this is not a csv file and must be skipped\n",
	}
	for name, content := range files {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0644); err != nil {
			panic(fmt.Sprintf("WriteFile(%s) failed: %v", name, err))
		}
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		panic(fmt.Sprintf("ReadDir failed: %v", err))
	}

	var csvFiles []string
	for _, e := range entries {
		if !e.IsDir() && filepath.Ext(e.Name()) == ".csv" {
			csvFiles = append(csvFiles, e.Name())
		}
	}
	sort.Strings(csvFiles) // ReadDir order is already sorted, but be explicit about the guarantee we rely on

	total := 0
	filesRead := 0
	for _, name := range csvFiles {
		f, err := os.Open(filepath.Join(dir, name))
		if err != nil {
			panic(fmt.Sprintf("Open(%s) failed: %v", name, err))
		}

		r := csv.NewReader(f)
		if _, err := r.Read(); err != nil { // header
			panic(fmt.Sprintf("reading header of %s failed: %v", name, err))
		}
		for {
			rec, err := r.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				panic(fmt.Sprintf("Read failed in %s: %v", name, err))
			}
			units, err := strconv.Atoi(rec[1])
			if err != nil {
				panic(fmt.Sprintf("Atoi(%q) failed: %v", rec[1], err))
			}
			total += units
		}
		if err := f.Close(); err != nil {
			panic(fmt.Sprintf("Close(%s) failed: %v", name, err))
		}
		filesRead++
	}

	if filesRead != 2 {
		panic(fmt.Sprintf("filesRead = %d, want 2 (notes.txt must be skipped)", filesRead))
	}
	if total != 22 { // 10+5+7
		panic(fmt.Sprintf("total = %d, want 22", total))
	}

	fmt.Printf("aggregated %d units across %d CSV files: %v\n", total, filesRead, csvFiles)
	fmt.Println("OK")
}
