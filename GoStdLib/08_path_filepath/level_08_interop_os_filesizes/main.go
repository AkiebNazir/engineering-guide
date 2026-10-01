/*
LEVEL 08 (advanced) - interop: filepath.WalkDir + os to total real file sizes

You will learn
  - fs.DirEntry.Info() gets an fs.FileInfo without a separate os.Stat call
  - combining WalkDir (this package) with os.WriteFile/os.MkdirTemp (../01_os)
    to build and then measure a real directory tree on disk

Run: go run ./GoStdLib/08_path_filepath/level_08_interop_os_filesizes
*/

package main

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "gostdlib-filepath-08-*")
	if err != nil {
		panic(fmt.Sprintf("MkdirTemp failed: %v", err))
	}
	defer os.RemoveAll(dir)

	sizes := map[string]int{
		"a.bin":     100,
		"b.bin":     250,
		"sub/c.bin": 75,
	}
	wantTotal := 0
	for rel, n := range sizes {
		full := filepath.Join(dir, rel)
		if err := os.MkdirAll(filepath.Dir(full), 0755); err != nil {
			panic(fmt.Sprintf("MkdirAll failed: %v", err))
		}
		if err := os.WriteFile(full, make([]byte, n), 0644); err != nil {
			panic(fmt.Sprintf("WriteFile(%q) failed: %v", rel, err))
		}
		wantTotal += n
	}

	var total int64
	var fileCount int
	err = filepath.WalkDir(dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		info, err := d.Info() // FileInfo from the directory entry, no extra os.Stat syscall
		if err != nil {
			return fmt.Errorf("Info() for %s: %w", path, err)
		}
		total += info.Size()
		fileCount++
		return nil
	})
	if err != nil {
		panic(fmt.Sprintf("WalkDir failed: %v", err))
	}

	if fileCount != len(sizes) {
		panic(fmt.Sprintf("walked %d files, want %d", fileCount, len(sizes)))
	}
	if total != int64(wantTotal) {
		panic(fmt.Sprintf("total size = %d, want %d", total, wantTotal))
	}

	fmt.Printf("summed %d files across the tree: %d bytes total\n", fileCount, total)
	fmt.Println("OK")
}
