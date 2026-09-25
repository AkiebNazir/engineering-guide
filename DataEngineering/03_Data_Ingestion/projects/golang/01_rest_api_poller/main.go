package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

type Post struct {
	ID     int    `json:"id"`
	UserID int    `json:"userId"`
	Title  string `json:"title"`
	Body   string `json:"body"`
}

func initDB() *sql.DB {
	db, err := sql.Open("sqlite3", "./data.db")
	if err != nil {
		log.Fatal(err)
	}

	sqlStmt := `
	CREATE TABLE IF NOT EXISTS posts (
		id INTEGER PRIMARY KEY,
		user_id INTEGER,
		title TEXT,
		body TEXT
	);
	`
	_, err = db.Exec(sqlStmt)
	if err != nil {
		log.Printf("%q: %s\n", err, sqlStmt)
	}
	return db
}

func main() {
	fmt.Println("Starting Data Engineering Project: 01_rest_api_poller")

	db := initDB()
	defer db.Close()

	url := "https://jsonplaceholder.typicode.com/posts"
	fmt.Printf("Fetching data from %s...\n", url)

	resp, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	var posts []Post
	if err := json.Unmarshal(body, &posts); err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Fetched %d items. Saving to SQLite...\n", len(posts))

	stmt, err := db.Prepare("INSERT OR REPLACE INTO posts(id, user_id, title, body) values(?,?,?,?)")
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	for _, post := range posts {
		_, err = stmt.Exec(post.ID, post.UserID, post.Title, post.Body)
		if err != nil {
			log.Fatal(err)
		}
	}

	fmt.Println("Data saved successfully.")
}
