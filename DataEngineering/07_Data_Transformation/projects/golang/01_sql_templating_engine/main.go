package main

import (
	"bytes"
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"strings"
	"text/template"
	"time"

	_ "github.com/lib/pq"
)

type QueryContext struct {
	Columns    []string
	Table      string
	Conditions []string
}

// GenerateSQL parses the template and data to produce a SQL string.
func GenerateSQL(tmplStr string, data QueryContext) (string, error) {
	tmpl, err := template.New("sql").Funcs(template.FuncMap{
		"join": strings.Join,
	}).Parse(tmplStr)
	if err != nil {
		return "", fmt.Errorf("failed to parse template: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		return "", fmt.Errorf("failed to execute template: %w", err)
	}
	return buf.String(), nil
}

// ExecuteQuery runs the query on the provided DB connection.
func ExecuteQuery(ctx context.Context, db *sql.DB, query string) error {
	log.Printf("Executing query: \n%s", strings.TrimSpace(query))
	
	rows, err := db.QueryContext(ctx, query)
	if err != nil {
		return fmt.Errorf("query execution failed: %w", err)
	}
	defer rows.Close()

	var count int
	for rows.Next() {
		count++
	}

	if err := rows.Err(); err != nil {
		return fmt.Errorf("row iteration error: %w", err)
	}

	log.Printf("Query returned %d rows", count)
	return nil
}

func main() {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://user:password@localhost:5432/analytics_db?sslmode=disable"
	}

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		log.Fatalf("Failed to open DB connection: %v", err)
	}
	defer db.Close()

	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Minute * 5)

	sqlTmpl := `SELECT
{{join .Columns ", "}}
FROM {{.Table}}
WHERE {{range $i, $cond := .Conditions}}{{if $i}} AND {{end}}{{$cond}}{{end}};`

	data := QueryContext{
		Columns:    []string{"id", "name", "amount", "transaction_date"},
		Table:      "raw_transactions",
		Conditions: []string{"amount > 100", "status = 'completed'"},
	}

	query, err := GenerateSQL(sqlTmpl, data)
	if err != nil {
		log.Fatalf("Template generation error: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := ExecuteQuery(ctx, db, query); err != nil {
		log.Printf("Note: Database not reachable, skipping execution. Query was: \n%s", query)
	}
}
