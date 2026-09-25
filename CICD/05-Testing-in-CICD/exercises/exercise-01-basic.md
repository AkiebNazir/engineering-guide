# Exercise 01: Go Table-Driven Tests 🟢

## 🎯 Objective
Learn how to write idiomatic Go unit tests using the table-driven testing pattern.

## 📋 Prerequisites
- Go installed on your local machine.

## 📝 Instructions

1. Create a directory named `calculator` and initialize a Go module.
2. Inside `calculator`, create a file named `calc.go` with a function that calculates the discount on an item.
3. Create a test file named `calc_test.go` and implement a table-driven test to cover various discount scenarios.

### Step 1: Write the Code
Create `calc.go`:

```go
package calculator

import "errors"

// CalculatePrice applies a percentage discount to a price.
func CalculatePrice(originalPrice float64, discountPercentage float64) (float64, error) {
	if originalPrice < 0 {
		return 0, errors.New("price cannot be negative")
	}
	if discountPercentage < 0 || discountPercentage > 100 {
		return 0, errors.New("discount must be between 0 and 100")
	}
	
	discountAmount := originalPrice * (discountPercentage / 100)
	finalPrice := originalPrice - discountAmount
	
	return finalPrice, nil
}
```

### Step 2: Write the Test
Create `calc_test.go`:

```go
package calculator

import "testing"

func TestCalculatePrice(t *testing.T) {
	// 1. Define the table structure
	tests := []struct {
		name               string
		price              float64
		discount           float64
		expectedPrice      float64
		expectError        bool
	}{
		// 2. Populate the test cases
		{"standard discount", 100.0, 20.0, 80.0, false},
		{"no discount", 50.0, 0.0, 50.0, false},
		{"100% discount", 200.0, 100.0, 0.0, false},
		{"negative price", -10.0, 10.0, 0.0, true},
		{"invalid discount over 100", 100.0, 150.0, 0.0, true},
		{"negative discount", 100.0, -10.0, 0.0, true},
	}

	// 3. Iterate over the tests and run subtests
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := CalculatePrice(tt.price, tt.discount)
			
			// Check error expectations
			if (err != nil) != tt.expectError {
				t.Fatalf("expected error: %v, got: %v", tt.expectError, err)
			}
			
			// Check result expectation
			if result != tt.expectedPrice {
				t.Errorf("expected price %v, got %v", tt.expectedPrice, result)
			}
		})
	}
}
```

### Step 3: Run the tests
Execute the tests with verbose output:
```bash
go test -v .
```

## 💡 Hints
- `t.Fatalf` stops the current test immediately (good for unexpected errors).
- `t.Errorf` logs the error but continues the test execution (good for checking multiple values).
- The anonymous struct pattern is the standard way to define test tables in Go.

## ✅ Expected Output
```
=== RUN   TestCalculatePrice
=== RUN   TestCalculatePrice/standard_discount
=== RUN   TestCalculatePrice/no_discount
=== RUN   TestCalculatePrice/100%_discount
=== RUN   TestCalculatePrice/negative_price
=== RUN   TestCalculatePrice/invalid_discount_over_100
=== RUN   TestCalculatePrice/negative_discount
--- PASS: TestCalculatePrice (0.00s)
    --- PASS: TestCalculatePrice/standard_discount (0.00s)
    --- PASS: TestCalculatePrice/no_discount (0.00s)
    --- PASS: TestCalculatePrice/100%_discount (0.00s)
    --- PASS: TestCalculatePrice/negative_price (0.00s)
    --- PASS: TestCalculatePrice/invalid_discount_over_100 (0.00s)
    --- PASS: TestCalculatePrice/negative_discount (0.00s)
PASS
ok      command-line-arguments  0.134s
```

## 🧠 Key Takeaway
Table-driven tests make it incredibly easy to add new test cases without writing boilerplate code for each one. They are the backbone of Go unit testing.
