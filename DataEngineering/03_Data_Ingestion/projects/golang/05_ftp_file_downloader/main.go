package main

import (
	"io"
	"log"

	"github.com/pkg/sftp"
	"golang.org/x/crypto/ssh"
)

func downloadSFTP(host, user, pkeyPath, remotePath, localPath string) error {
	log.Printf("Connecting to SFTP server %s as %s...", host, user)

	key, err := os.ReadFile(pkeyPath)
	if err != nil {
		return err
	}

	signer, err := ssh.ParsePrivateKey(key)
	if err != nil {
		return err
	}

	config := &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			ssh.PublicKeys(signer),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(), // In prod, use a proper host key callback
	}

	client, err := ssh.Dial("tcp", host, config)
	if err != nil {
		return err
	}
	defer client.Close()

	sftpClient, err := sftp.NewClient(client)
	if err != nil {
		return err
	}
	defer sftpClient.Close()

	log.Printf("Downloading %s to %s...", remotePath, localPath)

	remoteFile, err := sftpClient.Open(remotePath)
	if err != nil {
		return err
	}
	defer remoteFile.Close()

	localFile, err := os.Create(localPath)
	if err != nil {
		return err
	}
	defer localFile.Close()

	bytesCopied, err := io.Copy(localFile, remoteFile)
	if err != nil {
		return err
	}

	log.Printf("Successfully downloaded %d bytes to %s", bytesCopied, localPath)
	return nil
}

func main() {
	log.Println("Starting Data Engineering Project: 05_ftp_file_downloader (SFTP Client)")

	host := os.Getenv("SFTP_HOST")
	if host == "" {
		host = "sftp.example.com:22"
	}
	user := os.Getenv("SFTP_USER")
	if user == "" {
		user = "demo"
	}
	pkeyPath := os.Getenv("SFTP_PKEY_PATH")
	if pkeyPath == "" {
		pkeyPath = "./id_rsa"
	}
	remotePath := os.Getenv("SFTP_REMOTE_PATH")
	if remotePath == "" {
		remotePath = "/incoming/data.csv"
	}
	localPath := os.Getenv("LOCAL_DOWNLOAD_PATH")
	if localPath == "" {
		localPath = "./data.csv"
	}

	if _, err := os.Stat(pkeyPath); os.IsNotExist(err) {
		log.Printf("WARNING: Private key not found at %s. Ensure it exists for successful connection.", pkeyPath)
	}

	if err := downloadSFTP(host, user, pkeyPath, remotePath, localPath); err != nil {
		log.Printf("SFTP Download failed: %v", err)
	}
}
