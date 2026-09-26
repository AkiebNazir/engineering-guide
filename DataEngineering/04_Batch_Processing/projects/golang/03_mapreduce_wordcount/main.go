package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"regexp"
	"sort"
	"strings"
	"sync"
)

type WordCount map[string]int

func mapper(lines <-chan string, out chan<- WordCount, wg *sync.WaitGroup) {
	defer wg.Done()
	counts := make(WordCount)
	pattern := regexp.MustCompile(`\b\w+\b`)
	
	for line := range lines {
		words := pattern.FindAllString(strings.ToLower(line), -1)
		for _, word := range words {
			counts[word]++
		}
	}
	out <- counts
}

func reducer(in <-chan WordCount, out chan<- WordCount) {
	total := make(WordCount)
	for counts := range in {
		for word, count := range counts {
			total[word] += count
		}
	}
	out <- total
}

func main() {
	inPath := flag.String("in", "corpus.txt", "Input text file for word count")
	outPath := flag.String("out", "word_counts.csv", "Output CSV for word counts")
	workers := flag.Int("workers", 4, "Number of mapper workers")
	flag.Parse()

	file, err := os.Open(*inPath)
	if err != nil {
		log.Printf("Failed to open %s: %v. Please provide a valid input.", *inPath, err)
		return
	}
	defer file.Close()

	linesChan := make(chan string, 1000)
	mapOut := make(chan WordCount, *workers)
	
	var mapWg sync.WaitGroup

	// Start mappers
	for i := 0; i < *workers; i++ {
		mapWg.Add(1)
		go mapper(linesChan, mapOut, &mapWg)
	}

	// Read file and distribute to mappers
	go func() {
		scanner := bufio.NewScanner(file)
		// increase max token size if needed, but default is usually fine for text lines
		for scanner.Scan() {
			linesChan <- scanner.Text()
		}
		if err := scanner.Err(); err != nil {
			log.Printf("Error scanning file: %v", err)
		}
		close(linesChan)
	}()

	// Wait for mappers and close mapOut
	go func() {
		mapWg.Wait()
		close(mapOut)
	}()

	reduceOut := make(chan WordCount)
	// Start reducer
	go reducer(mapOut, reduceOut)

	// Wait for final result
	finalCounts := <-reduceOut
	
	// Sort by count descending
	type kv struct {
		Key   string
		Value int
	}
	var sortedCounts []kv
	for k, v := range finalCounts {
		sortedCounts = append(sortedCounts, kv{k, v})
	}
	
	sort.Slice(sortedCounts, func(i, j int) bool {
		return sortedCounts[i].Value > sortedCounts[j].Value
	})

	// Write output
	outFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("Failed to create output file: %v", err)
	}
	defer outFile.Close()

	outFile.WriteString("word,count\n")
	for _, kv := range sortedCounts {
		outFile.WriteString(fmt.Sprintf("%s,%d\n", kv.Key, kv.Value))
	}

	fmt.Printf("MapReduce word count completed. Saved %d unique words to %s\n", len(sortedCounts), *outPath)
}
