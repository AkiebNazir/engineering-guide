package main

import (
	"database/sql"
	"fmt"
	"log"
	"regexp"

	_ "github.com/mattn/go-sqlite3"
)

var mockHTML = `
<html>
    <head><title>Mock Webpage</title></head>
    <body>
        <h1>Breaking News</h1>
        <div class="article"><h2>Go 1.22 Released!</h2></div>
        <div class="article"><h2>Data Engineering in Go</h2></div>
        <div class="article"><h2>Concurrency is not Parallelism</h2></div>
    </body>
</html>
`

func initDB() *sql.DB {
	db, err := sql.Open("sqlite3", "./scraper.db")
	if err != nil {
		log.Fatal(err)
	}

	sqlStmt := `
	CREATE TABLE IF NOT EXISTS titles (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		title TEXT
	);
	`
	_, err = db.Exec(sqlStmt)
	if err != nil {
		log.Printf("%q: %s\n", err, sqlStmt)
	}
	return db
}

func main() {
	fmt.Println("Starting Data Engineering Project: 02_web_scraper_to_db")
	db := initDB()
	defer db.Close()

	fmt.Println("Extracting titles from mock HTML...")
	re := regexp.MustCompile(`<h2>(.*?)</h2>`)
	matches := re.FindAllStringSubmatch(mockHTML, -1)

	fmt.Printf("Extracted %d titles. Saving to database...\n", len(matches))
	stmt, err := db.Prepare("INSERT INTO titles(title) values(?)")
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	for _, match := range matches {
		if len(match) > 1 {
			_, err = stmt.Exec(match[1])
			if err != nil {
				log.Fatal(err)
			}
		}
	}
	fmt.Println("Titles saved successfully.")
}
