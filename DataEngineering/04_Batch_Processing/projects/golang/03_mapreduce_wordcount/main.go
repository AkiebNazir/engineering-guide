package main

import (
	"fmt"
	"regexp"
	"strings"
	"sync"
)

func mapper(text string, out chan<- map[string]int) {
	counts := make(map[string]int)
	pattern := regexp.MustCompile(`\b\w+\b`)
	words := pattern.FindAllString(strings.ToLower(text), -1)
	for _, word := range words {
		counts[word]++
	}
	out <- counts
}

func reducer(in <-chan map[string]int, out chan<- map[string]int) {
	total := make(map[string]int)
	for counts := range in {
		for word, count := range counts {
			total[word] += count
		}
	}
	out <- total
}

func main() {
	text := strings.Repeat("Hello world! This is a test. Hello again. World of MapReduce. ", 1000)
	chunkSize := len(text) / 4

	mapOut := make(chan map[string]int, 4)
	var wg sync.WaitGroup

	for i := 0; i < 4; i++ {
		wg.Add(1)
		start := i * chunkSize
		end := start + chunkSize
		if i == 3 {
			end = len(text)
		}
		go func(chunk string) {
			defer wg.Done()
			mapper(chunk, mapOut)
		}(text[start:end])
	}

	go func() {
		wg.Wait()
		close(mapOut)
	}()

	reduceOut := make(chan map[string]int)
	go reducer(mapOut, reduceOut)

	result := <-reduceOut
	fmt.Println("Word counts (sample):")
	fmt.Printf("hello: %d\n", result["hello"])
	fmt.Printf("world: %d\n", result["world"])
}
