package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

type Post struct {
	UserID int    `json:"userId"`
	ID     int    `json:"id"`
	Title  string `json:"title"`
	Body   string `json:"body"`
}

func main() {
	// Fetch data from REST API
	resp, err := http.Get("https://jsonplaceholder.typicode.com/posts")
	if err != nil {
		log.Fatalf("Failed to fetch data: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Failed to read response body: %v", err)
	}

	// Unmarshal JSON
	var posts []Post
	if err := json.Unmarshal(body, &posts); err != nil {
		log.Fatalf("Failed to unmarshal JSON: %v", err)
	}

	// Setup SQLite database
	db, err := sql.Open("sqlite3", "./posts.db")
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()

	// Create table
	createTableSQL := `CREATE TABLE IF NOT EXISTS posts (
		"id" INTEGER PRIMARY KEY,
		"userId" INTEGER,
		"title" TEXT,
		"body" TEXT
	);`
	_, err = db.Exec(createTableSQL)
	if err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}

	// Insert data
	insertSQL := `INSERT INTO posts (id, userId, title, body) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING`
	stmt, err := db.Prepare(insertSQL)
	if err != nil {
		log.Fatalf("Failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, post := range posts {
		_, err = stmt.Exec(post.ID, post.UserID, post.Title, post.Body)
		if err != nil {
			log.Printf("Failed to insert post %d: %v", post.ID, err)
		}
	}

	fmt.Printf("Successfully fetched and inserted %d posts into SQLite database.\n", len(posts))
}
