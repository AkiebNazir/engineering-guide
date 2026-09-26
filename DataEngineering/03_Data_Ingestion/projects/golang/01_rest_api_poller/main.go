package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/lib/pq"
)

type Post struct {
	ID     int    `json:"id"`
	UserID int    `json:"userId"`
	Title  string `json:"title"`
	Body   string `json:"body"`
}

func initDB(dbURL string) *sql.DB {
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("Failed to open db connection: %v", err)
	}

	createTableQuery := `
	CREATE TABLE IF NOT EXISTS posts (
		id INT PRIMARY KEY,
		user_id INT,
		title TEXT,
		body TEXT
	);
	`
	if _, err := db.Exec(createTableQuery); err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}

	return db
}

func fetchAndSave(ctx context.Context, client *http.Client, apiURL string, db *sql.DB) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, apiURL, nil)
	if err != nil {
		return err
	}

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	var posts []Post
	if err := json.NewDecoder(resp.Body).Decode(&posts); err != nil {
		return err
	}

	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO posts (id, user_id, title, body) 
		VALUES ($1, $2, $3, $4) 
		ON CONFLICT (id) DO UPDATE SET 
			user_id = EXCLUDED.user_id,
			title = EXCLUDED.title,
			body = EXCLUDED.body
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for _, p := range posts {
		if _, err := stmt.ExecContext(ctx, p.ID, p.UserID, p.Title, p.Body); err != nil {
			return err
		}
	}

	return tx.Commit()
}

func main() {
	log.Println("Starting Data Engineering Project: 01_rest_api_poller")

	apiURL := os.Getenv("API_URL")
	if apiURL == "" {
		apiURL = "https://jsonplaceholder.typicode.com/posts"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:password@localhost:5432/poller_db?sslmode=disable"
	}

	pollInterval := 60 * time.Second

	db := initDB(dbURL)
	defer db.Close()

	client := &http.Client{Timeout: 10 * time.Second}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	// Initial run
	log.Println("Fetching initial data...")
	if err := fetchAndSave(ctx, client, apiURL, db); err != nil {
		log.Printf("Initial fetch failed: %v", err)
	} else {
		log.Println("Initial fetch successful.")
	}

	for {
		select {
		case <-ticker.C:
			log.Println("Polling data...")
			if err := fetchAndSave(ctx, client, apiURL, db); err != nil {
				log.Printf("Poll failed: %v", err)
			} else {
				log.Println("Poll successful, data saved.")
			}
		case <-sigs:
			log.Println("Shutting down...")
			return
		}
	}
}
