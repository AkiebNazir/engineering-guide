package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"sync"
)

func main() {
	file, err := os.Create("server.log")
	if err != nil {
		panic(err)
	}
	for i := 0; i < 100; i++ {
		file.WriteString("192.168.1.1 - - [10/Oct/2023:13:55:36 -0700] \"GET /index.html HTTP/1.1\" 200 2326\n")
		file.WriteString("10.0.0.5 - - [10/Oct/2023:13:55:37 -0700] \"GET /missing.html HTTP/1.1\" 404 232\n")
	}
	file.Close()

	f, err := os.Open("server.log")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	lines := make(chan string, 100)
	var wg sync.WaitGroup

	errorCounts := make(map[string]int)
	var mu sync.Mutex

	// Worker pool
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			pattern := regexp.MustCompile(`(\d+\.\d+\.\d+\.\d+).*" \w+ .* HTTP/1.\d" (\d{3})`)
			for line := range lines {
				match := pattern.FindStringSubmatch(line)
				if len(match) == 3 && match[2] == "404" {
					mu.Lock()
					errorCounts[match[1]]++
					mu.Unlock()
				}
			}
		}()
	}

	for scanner.Scan() {
		lines <- scanner.Text()
	}
	close(lines)
	wg.Wait()

	fmt.Println("Anomalous IPs (high 404 rate):")
	for ip, count := range errorCounts {
		if count > 10 {
			fmt.Printf("%s: %d errors\n", ip, count)
		}
	}
}
