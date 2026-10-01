/*
LAB 03 (advanced) - JSON <-> Protobuf, Any, and FieldMask partial updates
=========================================================================
You will learn
  - protojson: the CANONICAL JSON mapping. Do NOT use encoding/json on generated messages -
    it ignores oneofs, well-known types and int64 rules.
    int64            -> JSON string  ("150")       JavaScript numbers lose precision above 2^53
    bytes            -> base64
    enum             -> its NAME
    Timestamp        -> RFC 3339 string            Duration -> "300.250s"
    field names      -> lowerCamelCase (or UseProtoNames for snake_case)
  - marshal options: EmitUnpopulated (show zero values), UseProtoNames, Multiline
  - unmarshal options: DiscardUnknown - accept JSON with extra fields (forward compatibility)
  - Any: a self-describing envelope {type_url, bytes}; unpack with a type check
  - FieldMask: the clean way to do PATCH-style updates ("touch ONLY these paths")
    implemented here with protoreflect - the same mechanism gRPC gateways and Google APIs use

Run it   go run ./Protobuf/labs/golang/03_protojson_any_fieldmask
*/
package main

import (
	"fmt"
	"strings"
	"time"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/types/known/anypb"
	"google.golang.org/protobuf/types/known/durationpb"
	"google.golang.org/protobuf/types/known/fieldmaskpb"
	"google.golang.org/protobuf/types/known/timestamppb"

	"dsapractice/api/Protobuf/labs/golang/pb"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

// applyMask copies ONLY the masked top-level fields from src into dst.
func applyMask(dst, src proto.Message, mask *fieldmaskpb.FieldMask) error {
	d, s := dst.ProtoReflect(), src.ProtoReflect()
	for _, path := range mask.GetPaths() {
		fd := d.Descriptor().Fields().ByName(protoreflect.Name(path))
		if fd == nil {
			return fmt.Errorf("unknown field %q in update_mask", path)
		}
		if s.Has(fd) {
			d.Set(fd, s.Get(fd))
		} else {
			d.Clear(fd) // masked but empty in src => the client wants it CLEARED
		}
	}
	return nil
}

func main() {
	u := &pb.User{
		Id:   9007199254740993, // 2^53 + 1: cannot be represented exactly as a JSON number in JavaScript
		Name: "Ana", Role: pb.Role_ROLE_ADMIN, Avatar: []byte("hi"),
		CreatedAt: timestamppb.New(time.Date(2026, 9, 21, 10, 30, 0, 0, time.UTC)),
		Contact:   &pb.User_Slack{Slack: "@ana"},
	}

	fmt.Println("== 1. canonical JSON ==")
	js, _ := protojson.MarshalOptions{}.Marshal(u)
	fmt.Println(" ", string(js))
	for _, want := range []string{`"9007199254740993"`, `"ROLE_ADMIN"`, `"aGk="`, `"2026-09-21T10:30:00Z"`, `"createdAt"`, `"slack":"@ana"`} {
		must(strings.Contains(strings.ReplaceAll(string(js), " ", ""), want), "expected "+want)
	}
	fmt.Println("  note: id is a string, avatar is base64, role is a name, createdAt is lowerCamelCase RFC 3339")

	fmt.Println("\n== 2. options ==")
	snake, _ := protojson.MarshalOptions{UseProtoNames: true, EmitUnpopulated: false}.Marshal(&pb.User{Name: "Ana", CreatedAt: u.CreatedAt})
	fmt.Println("  UseProtoNames  :", string(snake))
	full, _ := protojson.MarshalOptions{EmitUnpopulated: true}.Marshal(&pb.User{Name: "Ana"})
	fmt.Println("  EmitUnpopulated:", string(full)[:90], "...")
	fmt.Println("  (by default zero values are OMITTED - clients must not assume every key is present)")

	fmt.Println("\n== 3. parsing JSON: strict vs forward-compatible ==")
	incoming := `{"name":"Zed","role":"ROLE_USER","shinyNewField":true}`
	var strict pb.User
	err := protojson.Unmarshal([]byte(incoming), &strict)
	fmt.Println("  default (strict)  ->", strings.SplitN(fmt.Sprint(err), "\n", 2)[0])
	must(err != nil, "unknown JSON field rejected by default")
	var lenient pb.User
	must(protojson.UnmarshalOptions{DiscardUnknown: true}.Unmarshal([]byte(incoming), &lenient) == nil, "lenient")
	fmt.Println("  DiscardUnknown    ->", lenient.GetName(), lenient.GetRole())
	var numeric pb.User
	must(protojson.Unmarshal([]byte(`{"id": 150, "role": 2}`), &numeric) == nil, "numbers accepted for int64 and enums")
	fmt.Println("  parsers are liberal: id as number and role as number are accepted ->", numeric.GetId(), numeric.GetRole())

	fmt.Println("\n== 4. Any: type-checked unpacking ==")
	payload, _ := anypb.New(&pb.User{Id: 42, Name: "Zed"})
	ev := &pb.Event{Id: "evt-1", Payload: payload, Ttl: durationpb.New(5*time.Minute + 250*time.Millisecond)}
	wire, _ := proto.Marshal(ev)
	fmt.Println("  type_url:", ev.Payload.TypeUrl)
	var got pb.Event
	must(proto.Unmarshal(wire, &got) == nil, "unmarshal event")
	if inner, err := got.Payload.UnmarshalNew(); err == nil { // looks the type up in the global registry
		fmt.Printf("  UnmarshalNew -> %T %v\n", inner, inner.(*pb.User).GetName())
	}
	var wrong pb.Address
	err = got.Payload.UnmarshalTo(&wrong)
	fmt.Println("  UnmarshalTo(wrong type) ->", err)
	must(err != nil, "type mismatch detected")
	evJSON, _ := protojson.Marshal(ev)
	fmt.Println("  Event as JSON:", string(evJSON))
	must(strings.Contains(string(evJSON), `"@type":"type.googleapis.com/demo.v1.User"`) && strings.Contains(string(evJSON), `"300.250s"`), "Any and Duration JSON")

	fmt.Println("\n== 5. FieldMask: PATCH without ambiguity ==")
	stored := &pb.User{Id: 1, Name: "Ana", Email: "ana@old.io", Role: pb.Role_ROLE_USER}
	patch := &pb.UserPatch{
		User:       &pb.User{Name: "Ana Maria", Email: "" /* clear it! */, Role: pb.Role_ROLE_ADMIN},
		UpdateMask: &fieldmaskpb.FieldMask{Paths: []string{"name", "email"}}, // role is NOT in the mask
	}
	must(applyMask(stored, patch.User, patch.UpdateMask) == nil, "apply")
	fmt.Printf("  after patch: name=%q email=%q role=%v (role untouched: it was not in the mask)\n",
		stored.Name, stored.Email, stored.Role)
	must(stored.Name == "Ana Maria" && stored.Email == "" && stored.Role == pb.Role_ROLE_USER, "mask semantics")

	err = applyMask(stored, patch.User, &fieldmaskpb.FieldMask{Paths: []string{"passwrod"}})
	fmt.Println("  typo in mask ->", err)
	must(err != nil, "unknown path")

	_, err = fieldmaskpb.New(&pb.User{}, "name", "address.city")
	fmt.Println("  fieldmaskpb.New validates paths against the schema (nested ok):", err == nil)
	_, err = fieldmaskpb.New(&pb.User{}, "address.nope")
	must(err != nil, "invalid nested path rejected")
	fmt.Println("  invalid nested path ->", err)
	fmt.Println("\nOK")
}
