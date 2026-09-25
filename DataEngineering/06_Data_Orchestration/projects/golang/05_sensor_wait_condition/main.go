package main

import (
	"fmt"
	"os"
	"time"
)

func simulateFileCreation(filePath string, delay time.Duration) {
	fmt.Printf("Simulation: File will be created in %v...\n", delay)
	time.Sleep(delay)
	
	file, err := os.Create(filePath)
	if err == nil {
		file.WriteString("data")
		file.Close()
		fmt.Printf("Simulation: File '%s' created.\n", filePath)
	}
}

func fileSensor(filePath string, checkInterval time.Duration, timeout time.Duration) bool {
	fmt.Printf("Sensor: Waiting for file '%s' to appear...\n", filePath)
	start := time.Now()
	
	for {
		if _, err := os.Stat(filePath); err == nil {
			fmt.Printf("Sensor: File '%s' detected!\n", filePath)
			return true
		}
		
		if time.Since(start) > timeout {
			fmt.Printf("Sensor: Timeout reached. File '%s' not found.\n", filePath)
			return false
		}
		
		time.Sleep(checkInterval)
	}
}

func main() {
	targetFile := "trigger.txt"
	
	// Clean up if it exists
	os.Remove(targetFile)
	
	// Start file creation simulation
	go simulateFileCreation(targetFile, 4*time.Second)
	
	// Run the sensor
	if fileSensor(targetFile, 1*time.Second, 10*time.Second) {
		fmt.Println("Executing next task: Processing data...")
	} else {
		fmt.Println("Pipeline aborted due to missing file.")
	}
	
	// Clean up afterwards
	os.Remove(targetFile)
}
