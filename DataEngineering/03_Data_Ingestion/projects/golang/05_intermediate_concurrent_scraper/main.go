package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"regexp"
	"sync"
	"time"
)

func main() {
	urls := []string{
		"https://example.com",
		"https://golang.org",
		"https://pkg.go.dev",
		"https://github.com",
		"https://news.ycombinator.com",
	}

	// Rate limiter: 1 request per second
	rateLimiter := time.NewTicker(1 * time.Second)
	defer rateLimiter.Stop()

	titleRegex := regexp.MustCompile(`<title>(.*?)</title>`)

	var wg sync.WaitGroup
	titles := make(chan string, len(urls))

	for _, url := range urls {
		wg.Add(1)
		
		// Wait for tick before executing goroutine to enforce rate limits
		<-rateLimiter.C

		go func(u string) {
			defer wg.Done()
			
			resp, err := http.Get(u)
			if err != nil {
				log.Printf("Failed to fetch %s: %v", u, err)
				return
			}
			defer resp.Body.Close()

			body, err := io.ReadAll(resp.Body)
			if err != nil {
				log.Printf("Failed to read body from %s: %v", u, err)
				return
			}

			matches := titleRegex.FindSubmatch(body)
			if len(matches) > 1 {
				titles <- fmt.Sprintf("%s -> %s", u, string(matches[1]))
			} else {
				titles <- fmt.Sprintf("%s -> No title found", u)
			}
		}(url)
	}

	// Wait for all fetches to complete
	go func() {
		wg.Wait()
		close(titles)
	}()

	// Output collected titles
	fmt.Println("Scraped Titles:")
	for t := range titles {
		fmt.Println(t)
	}
}
