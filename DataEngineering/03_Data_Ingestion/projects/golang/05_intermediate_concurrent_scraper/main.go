package main

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

	titleRegex := regexp.MustCompile(`<title>(.*?)</title>`)

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
