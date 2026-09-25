package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"reflect"
	
	"dsapractice/api/Protobuf/Foundation/golang/pb/l12"
	"google.golang.org/protobuf/proto"
)

func main() {
	fmt.Println("== 1. the request and response are ordinary messages ==")
	request := &l12.EchoRequest{Text: "hello, gRPC"}
	response := &l12.EchoResponse{Text: request.Text, Length: int32(len(request.Text))}
	
	reqBytes, _ := proto.Marshal(request)
	fmt.Printf("  EchoRequest  -> %x\n", reqBytes)
	
	fmt.Println("\n== 2. the generated message code knows nothing about networking ==")
	t := reflect.TypeOf(request)
	fmt.Printf("  l12.EchoRequest is just a struct: %v\n", t.Elem().Name())

	fmt.Println("\n== 3. the one wire detail gRPC adds ==")
	var frame bytes.Buffer
	frame.WriteByte(0)
	binary.Write(&frame, binary.BigEndian, uint32(len(reqBytes)))
	frame.Write(reqBytes)
	
	fmt.Printf("  protobuf message : %d bytes  %x\n", len(reqBytes), reqBytes)
	fmt.Printf("  gRPC frame       : %d bytes  %x\n", frame.Len(), frame.Bytes())
	
	fmt.Println("\nOK")
}
