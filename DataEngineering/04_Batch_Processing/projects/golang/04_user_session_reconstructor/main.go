package main

import (
	"fmt"
	"sort"
	"time"
)

type Event struct {
	UserID    int
	Timestamp time.Time
	Page      string
}

func main() {
	layout := "2006-01-02 15:04:05"
	parseTime := func(s string) time.Time {
		t, _ := time.Parse(layout, s)
		return t
	}

	events := []Event{
		{1, parseTime("2023-10-01 10:00:00"), "/home"},
		{1, parseTime("2023-10-01 10:15:00"), "/about"},
		{1, parseTime("2023-10-01 11:00:00"), "/contact"},
		{2, parseTime("2023-10-01 10:00:00"), "/home"},
		{2, parseTime("2023-10-01 10:05:00"), "/products"},
	}

	// Sort events by user, then timestamp
	sort.Slice(events, func(i, j int) bool {
		if events[i].UserID == events[j].UserID {
			return events[i].Timestamp.Before(events[j].Timestamp)
		}
		return events[i].UserID < events[j].UserID
	})

	fmt.Println("Reconstructed Sessions:")
	sessionID := 0
	var lastTime time.Time
	var lastUser int

	for i, ev := range events {
		if i == 0 || ev.UserID != lastUser || ev.Timestamp.Sub(lastTime).Minutes() > 30 {
			sessionID++
		}
		fmt.Printf("UserID: %d, Time: %s, Page: %s, Session: %d\n", ev.UserID, ev.Timestamp.Format(layout), ev.Page, sessionID)
		lastTime = ev.Timestamp
		lastUser = ev.UserID
	}
}
