package main

import (
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/fsnotify/fsnotify"
)

func waitForFile(watchDir, targetFilename string, timeout time.Duration) bool {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatalf("Failed to create watcher: %v", err)
	}
	defer watcher.Close()

	// Watch the specified directory
	err = watcher.Add(watchDir)
	if err != nil {
		log.Fatalf("Failed to add watch directory: %v", err)
	}

	log.Printf("Starting sensor on directory '%s' for file '%s'", watchDir, targetFilename)

	timeoutChan := time.After(timeout)

	for {
		select {
		case event, ok := <-watcher.Events:
			if !ok {
				return false
			}
			// Check if the event is a creation or write and matches our target file
			if event.Op&fsnotify.Create == fsnotify.Create || event.Op&fsnotify.Write == fsnotify.Write {
				if filepath.Base(event.Name) == targetFilename {
					log.Printf("Detected trigger file: %s", event.Name)
					return true
				}
			}
		case err, ok := <-watcher.Errors:
			if !ok {
				return false
			}
			log.Printf("Watcher error: %v", err)
		case <-timeoutChan:
			log.Println("Sensor timed out waiting for the file.")
			return false
		}
	}
}

func simulateUpstreamSystem(dir, filename string, delay time.Duration) {
	time.Sleep(delay)
	filePath := filepath.Join(dir, filename)
	log.Printf("Upstream system creating file: %s", filePath)
	file, err := os.Create(filePath)
	if err != nil {
		log.Printf("Failed to create simulated file: %v", err)
		return
	}
	file.WriteString("ready")
	file.Close()
}

func main() {
	watchDir := "."
	triggerFile := "data_ready.trigger"

	// Ensure a clean state for the demo
	os.Remove(triggerFile)

	// Simulate an external system dropping a file after some delay
	go simulateUpstreamSystem(watchDir, triggerFile, 5*time.Second)

	// Run the sensor using fsnotify instead of busy polling
	if waitForFile(watchDir, triggerFile, 15*time.Second) {
		log.Println("Sensor condition met! Triggering downstream pipeline...")
		// Clean up afterwards
		os.Remove(triggerFile)
	} else {
		log.Println("Pipeline aborted due to missing file.")
	}
}
