package main

import (
	"fmt"
	"math/rand"
	"time"
)

type TaskStatus struct {
	TaskName string
	Status   string
	Duration time.Duration
	ErrorMsg string
}

func runTask(name string, statusChan chan<- TaskStatus) {
	start := time.Now()
	
	// Simulate work
	sleepTime := time.Duration(500+rand.Intn(1000)) * time.Millisecond
	time.Sleep(sleepTime)
	
	duration := time.Since(start)
	
	if name == "Transform" && rand.Float64() < 0.5 {
		statusChan <- TaskStatus{name, "FAILED", duration, "Data validation error during transformation"}
		return
	}
	
	statusChan <- TaskStatus{name, "SUCCESS", duration, ""}
}

func main() {
	rand.Seed(time.Now().UnixNano())
	
	tasks := []string{"Extract", "Transform", "Load"}
	statusChan := make(chan TaskStatus)
	
	var logs []TaskStatus
	
	fmt.Println("Starting pipeline execution...")
	
	for _, task := range tasks {
		go runTask(task, statusChan)
		
		status := <-statusChan
		logs = append(logs, status)
		
		timestamp := time.Now().Format(time.RFC3339)
		fmt.Printf("[%s] Task '%s': %s (%.2fs)\n", timestamp, status.TaskName, status.Status, status.Duration.Seconds())
		
		if status.Status == "FAILED" {
			fmt.Printf("\n[ALERT] Pipeline failed at task '%s'\n", status.TaskName)
			fmt.Printf("Reason: %s\n", status.ErrorMsg)
			fmt.Println("Summary of execution:")
			for _, log := range logs {
				fmt.Printf("  - %s: %s (%.2fs)\n", log.TaskName, log.Status, log.Duration.Seconds())
			}
			return
		}
	}
	
	fmt.Println("\nPipeline completed successfully!")
}
