package main

import (
	"fmt"
	"log"
	"time"

	"github.com/go-playground/validator/v10"
)

// UserRecord represents a data row from a source system (e.g., Kafka or a CSV)
// We use struct tags to define our data quality rules.
type UserRecord struct {
	ID         int       `validate:"required,gt=0"`
	Age        int       `validate:"required,gte=0,lte=120"`
	Email      string    `validate:"omitempty,email"`
	SignupDate time.Time `validate:"required"`
}

func main() {
	// Initialize the validator
	validate := validator.New()

	// Simulate incoming records
	records := []UserRecord{
		{ID: 1, Age: 25, Email: "alice@example.com", SignupDate: time.Now()},
		{ID: -2, Age: 30, Email: "invalid-email", SignupDate: time.Now()}, // Invalid ID, invalid email
		{ID: 3, Age: -5, Email: "bob@example.com", SignupDate: time.Now()},  // Invalid age
	}

	fmt.Println("Running Data Quality Assertions...")

	// In a real pipeline, we might process these concurrently and push invalid records to a Dead Letter Queue (DLQ)
	for i, record := range records {
		err := validate.Struct(record)
		if err != nil {
			fmt.Printf("Record %d (ID %d) failed data quality checks:\n", i, record.ID)
			
			// Cast error to validator.ValidationErrors to inspect individual field failures
			if validationErrors, ok := err.(validator.ValidationErrors); ok {
				for _, fieldErr := range validationErrors {
					fmt.Printf(" - Field '%s' failed validation '%s' (value: %v)\n", 
						fieldErr.Field(), fieldErr.Tag(), fieldErr.Value())
				}
			} else {
				log.Printf(" - Unknown validation error: %v", err)
			}
			// Here you would route this record to a DLQ topic or table
		} else {
			fmt.Printf("Record %d (ID %d) passed checks.\n", i, record.ID)
			// Proceed with downstream processing
		}
	}
}
