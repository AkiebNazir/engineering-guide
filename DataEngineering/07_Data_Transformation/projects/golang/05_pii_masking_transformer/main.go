package main

import (
	"crypto/sha256"
	"fmt"
	"strings"
)

func maskEmail(email string) string {
	parts := strings.Split(email, "@")
	if len(parts) == 2 {
		return string(parts[0][0]) + "***@" + parts[1]
	}
	return email
}

func hashSSN(ssn string) string {
	h := sha256.New()
	h.Write([]byte(ssn))
	return fmt.Sprintf("%x", h.Sum(nil))
}

func main() {
	email := "alice@example.com"
	ssn := "123-456-7890"

	fmt.Println("Masked Email:", maskEmail(email))
	fmt.Println("Hashed SSN:", hashSSN(ssn))
}
