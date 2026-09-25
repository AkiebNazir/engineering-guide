import os

base_py = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/07_Data_Transformation/projects/python"
base_go = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/07_Data_Transformation/projects/golang"

# Python files
py_files = {
    "01_sql_templating_engine/main.py": """from jinja2 import Template

sql_template = \"\"\"
SELECT
    {{ ', '.join(columns) }}
FROM {{ table_name }}
WHERE {% for condition in conditions %}
    {{ condition }}{% if not loop.last %} AND {% endif %}
{% endfor %}
\"\"\"

template = Template(sql_template)
query = template.render(
    columns=['id', 'name', 'amount'],
    table_name='raw_transactions',
    conditions=['amount > 100', "status = 'completed'"]
)

print("Generated SQL:")
print(query)
""",
    "02_json_flattening_script/main.py": """import pandas as pd
import json

nested_json = {
    "user_id": 1,
    "profile": {"name": "Alice", "age": 30},
    "location": {"city": "NYC", "zip": "10001"}
}

# Use pandas json_normalize to flatten deeply nested structures
df = pd.json_normalize(nested_json)
print("Flattened JSON to tabular format:")
print(df.to_csv(index=False))
""",
    "03_data_type_caster/main.py": """import pandas as pd

# Mock dirty data
data = {
    'date_str': ['2023-01-01T12:00:00Z', '2023-02-01T14:30:00Z'],
    'price_str': ['$1,200.50', '$45.00']
}
df = pd.DataFrame(data)

# Cast types
df['date_clean'] = pd.to_datetime(df['date_str'])
df['price_clean'] = df['price_str'].replace({'\$': '', ',': ''}, regex=True).astype(float)

print("Cleaned Types:")
print(df.dtypes)
print(df)
""",
    "04_currency_converter_pipeline/main.py": """import pandas as pd

data = {'tx_id': [1, 2], 'amount': [100.0, 50.0], 'currency': ['EUR', 'GBP']}
df = pd.DataFrame(data)

# Mock exchange rates to USD
rates = {'EUR': 1.1, 'GBP': 1.3}

df['usd_amount'] = df.apply(lambda row: row['amount'] * rates.get(row['currency'], 1.0), axis=1)

print("Standardized Currencies to USD:")
print(df)
""",
    "05_pii_masking_transformer/main.py": """import pandas as pd
import hashlib

def mask_email(email):
    parts = email.split('@')
    return f"{parts[0][0]}***@{parts[1]}"

def hash_ssn(ssn):
    return hashlib.sha256(ssn.encode()).hexdigest()

df = pd.DataFrame({
    'user': ['Alice', 'Bob'],
    'email': ['alice@example.com', 'bob@test.com'],
    'ssn': ['123-456-7890', '987-654-3210']
})

df['email_masked'] = df['email'].apply(mask_email)
df['ssn_hashed'] = df['ssn'].apply(hash_ssn)

print("Masked PII Data:")
print(df[['user', 'email_masked', 'ssn_hashed']])
"""
}

# Go files
go_files = {
    "01_sql_templating_engine/main.go": """package main

import (
	"os"
	"text/template"
)

func main() {
	sqlTmpl := `SELECT
{{range $i, $col := .Columns}}{{if $i}}, {{end}}{{$col}}{{end}}
FROM {{.Table}}
WHERE {{range $i, $cond := .Conditions}}{{if $i}} AND {{end}}{{$cond}}{{end}};
`
	tmpl, _ := template.New("sql").Parse(sqlTmpl)

	data := struct {
		Columns    []string
		Table      string
		Conditions []string
	}{
		Columns:    []string{"id", "name", "amount"},
		Table:      "raw_transactions",
		Conditions: []string{"amount > 100", "status = 'completed'"},
	}

	tmpl.Execute(os.Stdout, data)
}
""",
    "02_json_flattening_script/main.go": """package main

import (
	"encoding/json"
	"fmt"
)

func flatten(prefix string, nested map[string]interface{}, flat map[string]interface{}) {
	for k, v := range nested {
		newKey := k
		if prefix != "" {
			newKey = prefix + "_" + k
		}
		
		switch child := v.(type) {
		case map[string]interface{}:
			flatten(newKey, child, flat)
		default:
			flat[newKey] = v
		}
	}
}

func main() {
	raw := `{"user_id": 1, "profile": {"name": "Alice", "age": 30}}`
	var nested map[string]interface{}
	json.Unmarshal([]byte(raw), &nested)

	flat := make(map[string]interface{})
	flatten("", nested, flat)

	fmt.Println("Flattened Map:")
	for k, v := range flat {
		fmt.Printf("%s: %v\n", k, v)
	}
}
""",
    "03_data_type_caster/main.go": """package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

func main() {
	dateStr := "2023-01-01T12:00:00Z"
	priceStr := "$1,200.50"

	// Parse date
	cleanDate, _ := time.Parse(time.RFC3339, dateStr)

	// Clean and parse price
	cleanPriceStr := strings.ReplaceAll(priceStr, "$", "")
	cleanPriceStr = strings.ReplaceAll(cleanPriceStr, ",", "")
	cleanPrice, _ := strconv.ParseFloat(cleanPriceStr, 64)

	fmt.Printf("Parsed Date: %v (Type: %T)\n", cleanDate, cleanDate)
	fmt.Printf("Parsed Price: %f (Type: %T)\n", cleanPrice, cleanPrice)
}
""",
    "04_currency_converter_pipeline/main.go": """package main

import "fmt"

type Transaction struct {
	ID       int
	Amount   float64
	Currency string
}

func main() {
	txs := []Transaction{
		{1, 100.0, "EUR"},
		{2, 50.0, "GBP"},
	}

	rates := map[string]float64{"EUR": 1.1, "GBP": 1.3}

	for _, tx := range txs {
		usd := tx.Amount * rates[tx.Currency]
		fmt.Printf("TX %d: %.2f %s = $%.2f USD\n", tx.ID, tx.Amount, tx.Currency, usd)
	}
}
""",
    "05_pii_masking_transformer/main.go": """package main

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
"""
}

for filepath, content in py_files.items():
    with open(os.path.join(base_py, filepath), "w") as f:
        f.write(content)

for filepath, content in go_files.items():
    with open(os.path.join(base_go, filepath), "w") as f:
        f.write(content)

print("Generated Topic 07 code!")
