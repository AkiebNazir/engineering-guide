package main

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
	"time"
)

const logFile = "cdc_mock.log"

func createMockLog() {
	if _, err := os.Stat(logFile); os.IsNotExist(err) {
		err := os.WriteFile(logFile, []byte("INIT: server started\n"), 0644)
		if err != nil {
			log.Fatal(err)
		}
	}
}

func main() {
	fmt.Println("Starting Data Engineering Project: 03_cdc_log_tailer")
	createMockLog()

	file, err := os.Open(logFile)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	file.Seek(0, io.SeekEnd)
	reader := bufio.NewReader(file)

	fmt.Printf("Tailing %s for INSERT/UPDATE events (Ctrl+C to stop)...\n", logFile)

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				time.Sleep(500 * time.Millisecond)
				continue
			}
			log.Fatal(err)
		}

		if strings.Contains(line, "INSERT") || strings.Contains(line, "UPDATE") {
			fmt.Printf("Event detected: %s", line)
		}
	}
}
