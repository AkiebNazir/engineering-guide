package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

func main() {
	file, err := os.Create("dirty_data.csv")
	if err != nil {
		panic(err)
	}
	defer file.Close()
	file.WriteString("id,name,price,date\n")
	file.WriteString("1, Alice ,10.5,2023-01-01\n")
	file.WriteString("2,Bob,invalid,01/02/2023\n")
	file.WriteString("3,Charlie,20,bad_date\n")
	file.WriteString("4,,30,2023-01-04\n")

	f, err := os.Open("dirty_data.csv")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

	out, _ := os.Create("cleaned_data.csv")
	defer out.Close()
	writer := csv.NewWriter(out)
	defer writer.Flush()

	fmt.Println("Cleaned Data:")
	for i, rec := range records {
		if i == 0 {
			writer.Write(rec)
			fmt.Println(rec)
			continue
		}
		
		// Clean name
		name := strings.TrimSpace(rec[1])
		if name == "" {
			name = "Unknown"
		}
		
		// Clean price
		price, err := strconv.ParseFloat(rec[2], 64)
		priceStr := rec[2]
		if err != nil {
			priceStr = "0.0" // default value
		} else {
			priceStr = fmt.Sprintf("%.2f", price)
		}
		
		// Clean date
		dateStr := rec[3]
		parsedDate, err1 := time.Parse("2006-01-02", dateStr)
		parsedDate2, err2 := time.Parse("01/02/2006", dateStr)
		if err1 == nil {
			dateStr = parsedDate.Format("2006-01-02")
		} else if err2 == nil {
			dateStr = parsedDate2.Format("2006-01-02")
		} else {
			continue // skip row with invalid date
		}

		cleaned := []string{rec[0], name, priceStr, dateStr}
		writer.Write(cleaned)
		fmt.Println(cleaned)
	}
}
