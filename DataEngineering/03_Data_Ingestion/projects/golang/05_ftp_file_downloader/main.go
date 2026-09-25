package main

import (
	"fmt"
	"os"
)

func mockDownloadFTP(host, user, pass, filename, localPath string) error {
	fmt.Printf("Connecting to FTP server %s...\n", host)
	fmt.Println("Connected.")
	fmt.Printf("Mocking download of %s...\n", filename)
	
	data := "mock downloaded data from ftp server"
	err := os.WriteFile(localPath, []byte(data), 0644)
	if err != nil {
		return err
	}
	
	fmt.Printf("File downloaded to %s\n", localPath)
	return nil
}

func main() {
	fmt.Println("Starting Data Engineering Project: 05_ftp_file_downloader")
	
	host := "test.rebex.net"
	user := "demo"
	password := "password"
	filename := "readme.txt"
	localPath := "downloaded_readme.txt"
	
	err := mockDownloadFTP(host, user, password, filename, localPath)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}
