// BASIC EXAMPLE: Go Inbuilt net/rpc
// Demonstrates the native binary RPC standard library in Go (the precursor to gRPC).
package main

import (
	"log"
	"net"
	"net/rpc"
)

type UserService struct{}
type GetUserArgs struct{ ID string }
type User struct{ Name string }

// Method must have this exact signature to be exported via RPC
func (s *UserService) GetUser(args *GetUserArgs, reply *User) error {
	reply.Name = "Alice"
	return nil
}

func main() {
	rpc.Register(new(UserService))
	listener, err := net.Listen("tcp", ":1234")
	if err != nil {
		log.Fatal("Listen error:", err)
	}
	
	log.Println("Go Standard RPC Server running on :1234")
	rpc.Accept(listener)
}
