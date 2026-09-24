package main

import (
	"fmt"
	// "google.golang.org/protobuf/proto"
)

type User struct { Id int32; Name string; Email string }
func (u *User) ProtoReflect() {} // conceptual

func cloneUser(original *User) *User {
	// clone := proto.Clone(original).(*pb.User)
	clone := &User{Id: original.Id, Name: original.Name, Email: original.Email}
	return clone
}

func main() {
	user := &User{Id: 1, Name: "Alice"}
	cloned := cloneUser(user)
	fmt.Printf("Original: %p, Cloned: %p\n", user, cloned)
}
