package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"sort"
	"time"
)

type Event struct {
	UserID    string
	Timestamp time.Time
	Page      string
}

type SessionEvent struct {
	Event
	SessionID int
}

func main() {
	inPath := flag.String("in", "events.csv", "Input events CSV file")
	outPath := flag.String("out", "sessions.csv", "Output sessionized CSV file")
	timeoutMins := flag.Int("timeout", 30, "Session timeout in minutes")
	flag.Parse()

	file, err := os.Open(*inPath)
	if err != nil {
		log.Printf("Failed to open %s: %v. Please provide a valid input.", *inPath, err)
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)
	if _, err := reader.Read(); err != nil {
		log.Fatalf("failed to read header: %v", err)
	}

	// Group events by user
	userEvents := make(map[string][]Event)
	log.Println("Reading events into memory...")
	
	for {
		rec, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("error reading record: %v", err)
			continue
		}

		userID := rec[0]
		ts, err := time.Parse("2006-01-02 15:04:05", rec[1])
		if err != nil {
			log.Printf("invalid timestamp %s: %v", rec[1], err)
			continue
		}
		page := rec[2]

		userEvents[userID] = append(userEvents[userID], Event{
			UserID:    userID,
			Timestamp: ts,
			Page:      page,
		})
	}

	log.Println("Sessionizing events...")
	timeout := time.Duration(*timeoutMins) * time.Minute

	outFile, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("failed to create output file: %v", err)
	}
	defer outFile.Close()

	writer := csv.NewWriter(outFile)
	defer writer.Flush()
	writer.Write([]string{"user_id", "timestamp", "page", "session_id"})

	totalEvents := 0
	for _, events := range userEvents {
		// Sort events by timestamp
		sort.Slice(events, func(i, j int) bool {
			return events[i].Timestamp.Before(events[j].Timestamp)
		})

		sessionID := 1
		for i := 0; i < len(events); i++ {
			if i > 0 {
				diff := events[i].Timestamp.Sub(events[i-1].Timestamp)
				if diff > timeout {
					sessionID++
				}
			}

			writer.Write([]string{
				events[i].UserID,
				events[i].Timestamp.Format("2006-01-02 15:04:05"),
				events[i].Page,
				fmt.Sprintf("%d", sessionID),
			})
			totalEvents++
		}
	}

	log.Printf("Sessionization complete. Wrote %d events.", totalEvents)
}
