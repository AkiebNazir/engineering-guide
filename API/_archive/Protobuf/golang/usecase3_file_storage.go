package main

import (
	"log"
	"os"
	// "google.golang.org/protobuf/proto"
)

type User struct { Id int32; Name string; Email string }

func writeToFile(user *User) {
	// data, _ := proto.Marshal(user)
	data := []byte("mock binary payload")
	
	f, err := os.OpenFile("users.bin", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()
	
	f.Write(data)
	log.Println("Appended protobuf payload to disk")
}

func main() {}
