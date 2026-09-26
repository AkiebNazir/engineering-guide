package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"time"

	_ "github.com/lib/pq"
)

type Post struct {
	ID     int    `json:"id"`
	UserID int    `json:"userId"`
	Title  string `json:"title"`
	Body   string `json:"body"`
}

func main() {
	log.Println("Starting Data Engineering Project: 02_beginner_http_api_client")

	apiURL := os.Getenv("API_URL")
	if apiURL == "" {
		apiURL = "https://jsonplaceholder.typicode.com/posts"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:password@localhost:5432/client_db?sslmode=disable"
	}

	// 1. Setup robust HTTP Client
	client := &http.Client{
		Timeout: 15 * time.Second,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, apiURL, nil)
	if err != nil {
		log.Fatalf("Failed to create request: %v", err)
	}

	log.Printf("Fetching data from %s...", apiURL)
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalf("HTTP request failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Fatalf("Unexpected status code: %d", resp.StatusCode)
	}

	var posts []Post
	if err := json.NewDecoder(resp.Body).Decode(&posts); err != nil {
		log.Fatalf("Failed to decode JSON: %v", err)
	}
	log.Printf("Fetched %d posts successfully.", len(posts))

	// 2. Setup PostgreSQL connection with pooling
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(25)
	db.SetConnMaxLifetime(5 * time.Minute)

	createTableSQL := `
	CREATE TABLE IF NOT EXISTS posts (
		id INT PRIMARY KEY,
		user_id INT,
		title TEXT,
		body TEXT
	);`
	if _, err := db.ExecContext(ctx, createTableSQL); err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}

	// 3. Batch insert using transaction
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		log.Fatalf("Failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	insertSQL := `
	INSERT INTO posts (id, user_id, title, body) VALUES ($1, $2, $3, $4)
	ON CONFLICT (id) DO NOTHING`
	stmt, err := tx.PrepareContext(ctx, insertSQL)
	if err != nil {
		log.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, post := range posts {
		if _, err := stmt.ExecContext(ctx, post.ID, post.UserID, post.Title, post.Body); err != nil {
			log.Fatalf("Failed to insert post %d: %v", post.ID, err)
		}
	}

	if err := tx.Commit(); err != nil {
		log.Fatalf("Failed to commit transaction: %v", err)
	}

	log.Println("Data pipeline executed successfully.")
}
