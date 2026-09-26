package main

import (
	"crypto/sha256"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
)

// MaskEmail masks all characters in the local part except the first one.
func MaskEmail(email string) string {
	parts := strings.SplitN(email, "@", 2)
	if len(parts) != 2 || len(parts[0]) == 0 {
		return email
	}
	return string(parts[0][0]) + "***@" + parts[1]
}

// HashSSN returns a salted SHA-256 hash of the SSN.
func HashSSN(ssn, salt string) string {
	if ssn == "" {
		return ""
	}
	h := sha256.New()
	h.Write([]byte(ssn + salt))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// ProcessStream reads CSV records from an io.Reader, masks PII, and writes to an io.Writer.
func ProcessStream(r io.Reader, w io.Writer, salt string) error {
	reader := csv.NewReader(r)
	writer := csv.NewWriter(w)
	defer writer.Flush()

	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("failed to read header: %w", err)
	}

	emailIdx, ssnIdx := -1, -1
	for i, col := range header {
		switch strings.ToLower(col) {
		case "email":
			emailIdx = i
		case "ssn":
			ssnIdx = i
		}
	}

	if err := writer.Write(header); err != nil {
		return err
	}

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("Error reading record: %v", err)
			continue
		}

		if emailIdx != -1 && len(record) > emailIdx {
			record[emailIdx] = MaskEmail(record[emailIdx])
		}
		if ssnIdx != -1 && len(record) > ssnIdx {
			record[ssnIdx] = HashSSN(record[ssnIdx], salt)
		}

		if err := writer.Write(record); err != nil {
			return fmt.Errorf("failed to write record: %w", err)
		}
	}

	return nil
}

func main() {
	salt := os.Getenv("PII_HASH_SALT")
	if salt == "" {
		salt = "DEFAULT_PROD_SALT_999"
	}

	inputCSV := `user,email,ssn
Alice,alice@example.com,123-456-7890
Bob,bob.smith@test.com,987-654-3210`

	log.Println("Starting PII Masking Transformer...")
	
	r := strings.NewReader(inputCSV)
	
	if err := ProcessStream(r, os.Stdout, salt); err != nil {
		log.Fatalf("Stream processing failed: %v", err)
	}
	
	log.Println("PII Masking complete.")
}
