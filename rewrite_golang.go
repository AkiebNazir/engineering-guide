package main

import (
	"io/ioutil"
	"log"
)

var files = map[string]string{
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/01_rest_api_poller/main.go": `package main

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
	ID     int    ` + "`json:\"id\"`" + `
	UserID int    ` + "`json:\"userId\"`" + `
	Title  string ` + "`json:\"title\"`" + `
	Body   string ` + "`json:\"body\"`" + `
}

func initDB(dbURL string) *sql.DB {
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("Failed to open db connection: %v", err)
	}

	createTableQuery := ` + "`" + `
	CREATE TABLE IF NOT EXISTS posts (
		id INT PRIMARY KEY,
		user_id INT,
		title TEXT,
		body TEXT
	);
	` + "`" + `
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

	stmt, err := tx.PrepareContext(ctx, ` + "`" + `
		INSERT INTO posts (id, user_id, title, body) 
		VALUES ($1, $2, $3, $4) 
		ON CONFLICT (id) DO UPDATE SET 
			user_id = EXCLUDED.user_id,
			title = EXCLUDED.title,
			body = EXCLUDED.body
	` + "`" + `)
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
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/02_beginner_http_api_client/main.go": `package main

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
	ID     int    ` + "`json:\"id\"`" + `
	UserID int    ` + "`json:\"userId\"`" + `
	Title  string ` + "`json:\"title\"`" + `
	Body   string ` + "`json:\"body\"`" + `
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

	createTableSQL := ` + "`" + `
	CREATE TABLE IF NOT EXISTS posts (
		id INT PRIMARY KEY,
		user_id INT,
		title TEXT,
		body TEXT
	);` + "`" + `
	if _, err := db.ExecContext(ctx, createTableSQL); err != nil {
		log.Fatalf("Failed to create table: %v", err)
	}

	// 3. Batch insert using transaction
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		log.Fatalf("Failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	insertSQL := ` + "`" + `
	INSERT INTO posts (id, user_id, title, body) VALUES ($1, $2, $3, $4)
	ON CONFLICT (id) DO NOTHING` + "`" + `
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
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/02_web_scraper_to_db/main.go": `package main

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

	sqlStmt := ` + "`" + `
	CREATE TABLE IF NOT EXISTS article_titles (
		id SERIAL PRIMARY KEY,
		title TEXT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	` + "`" + `
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
	re := regexp.MustCompile(` + "`" + `class="titleline"><a href=".*?">(.*?)</a>` + "`" + `)
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
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/03_cdc_log_tailer/main.go": `package main

import (
	"context"
	"fmt"
	"log"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
)

func main() {
	log.Println("Starting Data Engineering Project: 03_cdc_log_tailer (Kafka Consumer)")

	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}

	topic := os.Getenv("KAFKA_CDC_TOPIC")
	if topic == "" {
		topic = "dbserver1.inventory.customers"
	}

	groupID := os.Getenv("KAFKA_GROUP_ID")
	if groupID == "" {
		groupID = "cdc-tailer-group"
	}

	// Setup Kafka Reader
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        []string{brokers},
		GroupID:        groupID,
		Topic:          topic,
		MinBytes:       10e3, // 10KB
		MaxBytes:       10e6, // 10MB
		CommitInterval: time.Second,
		StartOffset:    kafka.FirstOffset,
	})
	defer reader.Close()

	log.Printf("Subscribed to topic %s. Waiting for events...", topic)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigs
		log.Println("Shutting down consumer...")
		cancel()
	}()

	for {
		m, err := reader.FetchMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break // Shutdown gracefully
			}
			log.Printf("Failed to fetch message: %v", err)
			time.Sleep(1 * time.Second)
			continue
		}

		fmt.Printf("CDC Event Detected at offset %d: key=%s value=%s\n", m.Offset, string(m.Key), string(m.Value))

		if err := reader.CommitMessages(ctx, m); err != nil {
			log.Printf("Failed to commit message: %v", err)
		}
	}
	log.Println("Consumer stopped cleanly.")
}
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/04_webhook_listener/main.go": `package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
)

type WebhookHandler struct {
	S3Client *s3.Client
	Bucket   string
}

func (h *WebhookHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	if len(body) == 0 {
		http.Error(w, "Empty payload", http.StatusBadRequest)
		return
	}

	key := fmt.Sprintf("webhooks/%s_%s.json", time.Now().Format("20060102150405"), uuid.New().String())

	_, err = h.S3Client.PutObject(r.Context(), &s3.PutObjectInput{
		Bucket:      aws.String(h.Bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(body),
		ContentType: aws.String("application/json"),
	})

	if err != nil {
		log.Printf("Failed to upload to S3: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	log.Printf("Received webhook, saved to s3://%s/%s", h.Bucket, key)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(` + "`" + `{"status": "success"}` + "`" + `))
}

func main() {
	log.Println("Starting Data Engineering Project: 04_webhook_listener (AWS S3 Backend)")

	bucket := os.Getenv("S3_BUCKET")
	if bucket == "" {
		bucket = "my-webhook-payloads"
	}

	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("unable to load SDK config, %v", err)
	}

	s3Client := s3.NewFromConfig(cfg)

	handler := &WebhookHandler{
		S3Client: s3Client,
		Bucket:   bucket,
	}

	http.Handle("/webhook", handler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Listening for webhooks on port %s...", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/05_ftp_file_downloader/main.go": `package main

import (
	"io"
	"log"

	"github.com/pkg/sftp"
	"golang.org/x/crypto/ssh"
)

func downloadSFTP(host, user, pkeyPath, remotePath, localPath string) error {
	log.Printf("Connecting to SFTP server %s as %s...", host, user)

	key, err := os.ReadFile(pkeyPath)
	if err != nil {
		return err
	}

	signer, err := ssh.ParsePrivateKey(key)
	if err != nil {
		return err
	}

	config := &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			ssh.PublicKeys(signer),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(), // In prod, use a proper host key callback
	}

	client, err := ssh.Dial("tcp", host, config)
	if err != nil {
		return err
	}
	defer client.Close()

	sftpClient, err := sftp.NewClient(client)
	if err != nil {
		return err
	}
	defer sftpClient.Close()

	log.Printf("Downloading %s to %s...", remotePath, localPath)

	remoteFile, err := sftpClient.Open(remotePath)
	if err != nil {
		return err
	}
	defer remoteFile.Close()

	localFile, err := os.Create(localPath)
	if err != nil {
		return err
	}
	defer localFile.Close()

	bytesCopied, err := io.Copy(localFile, remoteFile)
	if err != nil {
		return err
	}

	log.Printf("Successfully downloaded %d bytes to %s", bytesCopied, localPath)
	return nil
}

func main() {
	log.Println("Starting Data Engineering Project: 05_ftp_file_downloader (SFTP Client)")

	host := os.Getenv("SFTP_HOST")
	if host == "" {
		host = "sftp.example.com:22"
	}
	user := os.Getenv("SFTP_USER")
	if user == "" {
		user = "demo"
	}
	pkeyPath := os.Getenv("SFTP_PKEY_PATH")
	if pkeyPath == "" {
		pkeyPath = "./id_rsa"
	}
	remotePath := os.Getenv("SFTP_REMOTE_PATH")
	if remotePath == "" {
		remotePath = "/incoming/data.csv"
	}
	localPath := os.Getenv("LOCAL_DOWNLOAD_PATH")
	if localPath == "" {
		localPath = "./data.csv"
	}

	if _, err := os.Stat(pkeyPath); os.IsNotExist(err) {
		log.Printf("WARNING: Private key not found at %s. Ensure it exists for successful connection.", pkeyPath)
	}

	if err := downloadSFTP(host, user, pkeyPath, remotePath, localPath); err != nil {
		log.Printf("SFTP Download failed: %v", err)
	}
}
`,
	"/Users/njasm/Njasm/AI/engineering-guide/DataEngineering/03_Data_Ingestion/projects/golang/05_intermediate_concurrent_scraper/main.go": `package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"regexp"
	"sync"
	"time"
)

// In a real application, you might save these to a database instead of just printing
type ScrapeResult struct {
	URL   string
	Title string
	Error error
}

func main() {
	log.Println("Starting Data Engineering Project: 05_intermediate_concurrent_scraper")

	urls := []string{
		"https://example.com",
		"https://golang.org",
		"https://pkg.go.dev",
		"https://github.com",
		"https://news.ycombinator.com",
	}

	// 1 req/second rate limiting
	rateLimiter := time.NewTicker(1 * time.Second)
	defer rateLimiter.Stop()

	titleRegex := regexp.MustCompile(` + "`" + `<title>(.*?)</title>` + "`" + `)

	var wg sync.WaitGroup
	results := make(chan ScrapeResult, len(urls))

	// Pre-configure HTTP Client
	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	for _, url := range urls {
		wg.Add(1)
		<-rateLimiter.C // Enforce rate limit

		go func(u string) {
			defer wg.Done()
			
			// Use context for each request
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()

			req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
			if err != nil {
				results <- ScrapeResult{URL: u, Error: err}
				return
			}

			resp, err := client.Do(req)
			if err != nil {
				results <- ScrapeResult{URL: u, Error: err}
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode >= 400 {
				results <- ScrapeResult{URL: u, Error: fmt.Errorf("bad status code: %d", resp.StatusCode)}
				return
			}

			body, err := io.ReadAll(resp.Body)
			if err != nil {
				results <- ScrapeResult{URL: u, Error: err}
				return
			}

			matches := titleRegex.FindSubmatch(body)
			if len(matches) > 1 {
				results <- ScrapeResult{URL: u, Title: string(matches[1])}
			} else {
				results <- ScrapeResult{URL: u, Title: "No title found"}
			}
		}(url)
	}

	// Wait for all to complete in a separate goroutine to close the channel
	go func() {
		wg.Wait()
		close(results)
	}()

	// Consume results
	log.Println("Scraping completed. Results:")
	for res := range results {
		if res.Error != nil {
			log.Printf("ERROR  %s -> %v", res.URL, res.Error)
		} else {
			log.Printf("SUCCESS %s -> %s", res.URL, res.Title)
		}
	}
}
`,
}

func main() {
	for path, content := range files {
		err := ioutil.WriteFile(path, []byte(content), 0644)
		if err != nil {
			log.Fatalf("Failed to write %s: %v", path, err)
		}
		log.Printf("Successfully wrote %s", path)
	}
}
