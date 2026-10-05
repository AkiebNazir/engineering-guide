/*
LAB 04 (advanced) - Reflection and dynamic messages: working with schemas you did not compile in
=================================================================================================
You will learn
  - every generated message can describe itself:  msg.ProtoReflect().Descriptor()
  - walking any message generically with Range() - the basis of loggers, redactors, diff tools,
    validators, and gRPC gateways that never import your generated code
  - the registry: look a message type up BY NAME at runtime (protoregistry.GlobalFiles)
  - dynamicpb: parse and print bytes using ONLY a descriptor, no generated struct
  - building a schema in code (descriptorpb -> protodesc) - what `grpcurl` and gRPC server
    reflection do when they learn a service's types from a running server
  - a real use: a generic PII redactor that blanks every field named in a list, for ANY message

Run it   go run ./Protobuf/labs/golang/04_reflection_and_dynamic_messages
*/
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"sort"
	"strings"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"

	"dsapractice/api/Protobuf/labs/golang/pb"
)

// protojson output has deliberately unstable whitespace; compact it for stable printing.
func compact(b []byte) string {
	var out bytes.Buffer
	json.Compact(&out, b)
	return out.String()
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// walk prints every POPULATED field of any message, recursing into nested messages.
func walk(m protoreflect.Message, indent string) {
	m.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		kind := fd.Kind().String()
		switch {
		case fd.IsMap():
			fmt.Printf("%s#%d %s (map, %d entries)\n", indent, fd.Number(), fd.Name(), v.Map().Len())
		case fd.IsList():
			fmt.Printf("%s#%d %s (repeated %s, %d items)\n", indent, fd.Number(), fd.Name(), kind, v.List().Len())
		case fd.Kind() == protoreflect.MessageKind:
			fmt.Printf("%s#%d %s (message %s)\n", indent, fd.Number(), fd.Name(), fd.Message().FullName())
			walk(v.Message(), indent+"    ")
		default:
			fmt.Printf("%s#%d %s (%s) = %v\n", indent, fd.Number(), fd.Name(), kind, v)
		}
		return true
	})
}

// redact blanks every string field whose NAME is in `names`, in ANY message, at any depth.
func redact(m protoreflect.Message, names map[string]bool) {
	m.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		switch {
		case fd.Kind() == protoreflect.StringKind && !fd.IsList() && !fd.IsMap() && names[string(fd.Name())]:
			m.Set(fd, protoreflect.ValueOfString("[REDACTED]"))
		case fd.Kind() == protoreflect.MessageKind && !fd.IsList() && !fd.IsMap():
			redact(v.Message(), names)
		}
		return true
	})
}

func main() {
	u := &pb.User{Id: 7, Name: "Ana", Email: "ana@x.io", Tags: []string{"a", "b"}, Attrs: map[string]string{"k": "v"},
		Address: &pb.Address{Street: "Main St 1", City: "Oslo"}}

	fmt.Println("== 1. a message describes itself ==")
	md := u.ProtoReflect().Descriptor()
	fmt.Printf("  %s has %d fields; oneofs: %d; file: %s\n", md.FullName(), md.Fields().Len(), md.Oneofs().Len(), md.ParentFile().Path())
	var names []string
	for i := 0; i < md.Fields().Len(); i++ {
		f := md.Fields().Get(i)
		names = append(names, fmt.Sprintf("%d:%s", f.Number(), f.Name()))
	}
	fmt.Println("  ", strings.Join(names[:8], " "), "...")

	fmt.Println("\n== 2. generic walk (only populated fields) ==")
	walk(u.ProtoReflect(), "  ")

	fmt.Println("\n== 3. a schema-agnostic redactor ==")
	clone := proto.Clone(u).(*pb.User)
	redact(clone.ProtoReflect(), map[string]bool{"email": true, "street": true})
	fmt.Printf("  email=%q street=%q name=%q (untouched)\n", clone.Email, clone.Address.Street, clone.Name)
	must(clone.Email == "[REDACTED]" && clone.Address.Street == "[REDACTED]" && clone.Name == "Ana", "redaction")
	must(u.Email == "ana@x.io", "original untouched (we cloned)")

	fmt.Println("\n== 4. find a type by name and decode bytes with a DYNAMIC message ==")
	wire, _ := proto.Marshal(u)
	desc, err := protoregistry.GlobalFiles.FindDescriptorByName("demo.v1.User") // a string, not a Go type
	must(err == nil, "registry lookup")
	dyn := dynamicpb.NewMessage(desc.(protoreflect.MessageDescriptor))
	must(proto.Unmarshal(wire, dyn) == nil, "dynamic unmarshal")
	js, _ := protojson.Marshal(dyn)
	fmt.Println("  dynamic message as JSON:", compact(js))
	nameField := desc.(protoreflect.MessageDescriptor).Fields().ByName("name")
	fmt.Println("  read field by name     :", dyn.Get(nameField).String())
	must(dyn.Get(nameField).String() == "Ana", "dynamic field access")

	fmt.Println("\n== 5. build a brand-new schema at runtime - no .proto, no codegen ==")
	// The equivalent of:   message Point { int32 x = 1; int32 y = 2; string label = 3; }
	file, err := protodesc.NewFile(&descriptorpb.FileDescriptorProto{
		Name: proto.String("runtime.proto"), Package: proto.String("rt"), Syntax: proto.String("proto3"),
		MessageType: []*descriptorpb.DescriptorProto{{
			Name: proto.String("Point"),
			Field: []*descriptorpb.FieldDescriptorProto{
				{Name: proto.String("x"), Number: proto.Int32(1), Type: descriptorpb.FieldDescriptorProto_TYPE_INT32.Enum(), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum()},
				{Name: proto.String("y"), Number: proto.Int32(2), Type: descriptorpb.FieldDescriptorProto_TYPE_INT32.Enum(), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum()},
				{Name: proto.String("label"), Number: proto.Int32(3), Type: descriptorpb.FieldDescriptorProto_TYPE_STRING.Enum(), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum()},
			},
		}},
	}, nil)
	must(err == nil, fmt.Sprint(err))
	pointDesc := file.Messages().ByName("Point")
	pt := dynamicpb.NewMessage(pointDesc)
	pt.Set(pointDesc.Fields().ByName("x"), protoreflect.ValueOfInt32(3))
	pt.Set(pointDesc.Fields().ByName("y"), protoreflect.ValueOfInt32(-4))
	pt.Set(pointDesc.Fields().ByName("label"), protoreflect.ValueOfString("origin+"))
	ptBytes, _ := proto.Marshal(pt)
	fmt.Printf("  Point{3,-4,\"origin+\"} -> % x\n", ptBytes)
	ptJSON, _ := protojson.Marshal(pt)
	fmt.Println("  as JSON:", compact(ptJSON))

	back := dynamicpb.NewMessage(pointDesc)
	must(proto.Unmarshal(ptBytes, back) == nil && proto.Equal(pt, back), "dynamic round trip")

	fmt.Println("\n== 6. the descriptor decides what the bytes MEAN ==")
	// interpret the Point bytes as demo.v1.User: field 1 (int32 x=3) lines up with User.id (int64), etc.
	var asUser pb.User
	_ = proto.Unmarshal(ptBytes, &asUser)
	fmt.Printf("  Point bytes read as User: id=%d (x reused as id), email=%q (field 3, was 'label')\n", asUser.Id, asUser.Email)
	fmt.Println("  => the descriptor decides the meaning; the bytes carry only numbers. See lab 03 of the Python track.")

	all := []string{}
	protoregistry.GlobalFiles.RangeFilesByPackage("demo.v1", func(fd protoreflect.FileDescriptor) bool {
		for i := 0; i < fd.Messages().Len(); i++ {
			all = append(all, string(fd.Messages().Get(i).Name()))
		}
		return true
	})
	sort.Strings(all)
	fmt.Println("\n  messages registered in package demo.v1:", all)
	fmt.Println("\nOK")
}
