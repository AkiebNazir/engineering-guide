package main

import (
	"context"
	"database/sql"
	"io"
	"log"
	"net/http"
	"regexp"
	"time"

	_ "github.com/lib/pq"
)

func fetchHTML(ctx context.Context, url string) (string, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return "", err
	}

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}

func initDB(dbURL string) *sql.DB {
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("Failed to open DB: %v", err)
	}

	sqlStmt := `
	CREATE TABLE IF NOT EXISTS article_titles (
		id SERIAL PRIMARY KEY,
		title TEXT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`
	if _, err := db.Exec(sqlStmt); err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}
	return db
}

func main() {
	log.Println("Starting Data Engineering Project: 02_web_scraper_to_db (Real Target & Postgres)")

	targetURL := os.Getenv("TARGET_URL")
	if targetURL == "" {
		targetURL = "https://news.ycombinator.com/"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:password@localhost:5432/scraper_db?sslmode=disable"
	}

	db := initDB(dbURL)
	defer db.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	log.Printf("Fetching HTML from %s...", targetURL)
	htmlContent, err := fetchHTML(ctx, targetURL)
	if err != nil {
		log.Fatalf("Failed to fetch HTML: %v", err)
	}

	// Simple regex for extracting titles (using title tags or similar, depending on the site)
	// This is a naive regex for demonstration on real sites
	re := regexp.MustCompile(`class="titleline"><a href=".*?">(.*?)</a>`)
	matches := re.FindAllStringSubmatch(htmlContent, -1)

	if len(matches) == 0 {
		log.Println("No titles found. Adjust regex for the target site.")
		return
	}

	log.Printf("Extracted %d titles. Saving to database...\n", len(matches))
	stmt, err := db.PrepareContext(ctx, "INSERT INTO article_titles(title) VALUES($1)")
	if err != nil {
		log.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, match := range matches {
		if len(match) > 1 {
			if _, err := stmt.ExecContext(ctx, match[1]); err != nil {
				log.Printf("Failed to insert title '%s': %v", match[1], err)
			}
		}
	}
	log.Println("Titles saved successfully.")
}
