package main

import (
	"log"
	"net"
	// "google.golang.org/protobuf/proto"
)

type User struct { Id int32; Name string; Email string }

func sendUDP(user *User) {
	conn, err := net.Dial("udp", "127.0.0.1:8080")
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	
	// data, _ := proto.Marshal(user)
	data := []byte("mock binary payload")
	
	conn.Write(data)
	log.Println("Sent protobuf over UDP datagram")
}

func main() {}
