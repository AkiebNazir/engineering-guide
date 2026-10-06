/*
FOUNDATION LEVEL 11 (capstone) - One complete, PROTECTED gRPC service
=========================================================================
Nothing new here. Every idea from levels 00-10 - the .proto contract, typed
request/response fields, status codes, metadata, interceptors, authentication
and authorization - combined into one small service, end to end.

	GetNote      public         no credential needed at all
	CreateNote   authenticated  any valid token
	DeleteNote   admin only     a valid token AND the "admin" role

The interesting new wrinkle is PER-METHOD policy: a single interceptor chain
protects the whole service, but one RPC is deliberately public. That is done
with a table of method paths, not with an `if` inside each handler - so adding
the next RPC means adding a table row, and forgetting to do so fails CLOSED.

This is deliberately the same shape as ../../../labs/golang/03_interceptor_chain.
Once this feels easy, ../../../labs/ (rich error details, mTLS identity, flow
control, health checking, reflection) is the very next step, not a jump.

You will learn
  - how the previous eleven small lessons compose into one real-looking,
    real-SECURED service
  - the deliberate order of operations per call: log -> recover -> authenticate
    -> authorize -> validate -> act
  - public-by-exception: the chain runs on every RPC, and the policy table is
    what makes one of them anonymous-friendly
  - a mutex, because a gRPC server handles calls CONCURRENTLY on many goroutines -
    the one production concern the earlier levels could ignore
  - that "a gRPC API" is not one big new idea - it is these small ideas layered
    in a fixed order

Run it        go run ./gRPC/Foundation/golang/11_complete_protected_service
Keep serving  go run ./gRPC/Foundation/golang/11_complete_protected_service --serve   (127.0.0.1:50051)
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/notespb"
)

type identity struct {
	user string
	role string
}

type identityKey struct{}

var tokens = map[string]identity{
	"alice-token": {user: "alice", role: "admin"},
	"bob-token":   {user: "bob", role: "viewer"},
}

// --- THE POLICY, in one place (level 10's idea, now with a public exception) ---
var publicMethods = map[string]bool{
	"/foundation.notes.v1.Notes/GetNote": true,
}

var requiredRole = map[string]string{
	"/foundation.notes.v1.Notes/DeleteNote": "admin",
}

// ---- level 08: logging (outermost, so it sees every outcome) ----
func loggingInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	start := time.Now()
	res, err := next(ctx, req)
	short := info.FullMethod[strings.LastIndex(info.FullMethod, "/")+1:]
	fmt.Printf("  [log] %-11s %-17s %.2fms\n", short, status.Code(err).String(),
		float64(time.Since(start).Microseconds())/1000)
	return res, err
}

// ---- level 08: panic recovery ----
func recoveryInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (res any, err error) {

	defer func() {
		if p := recover(); p != nil {
			fmt.Printf("  [recovery] %v -> INTERNAL, server stays up\n", p)
			res, err = nil, status.Error(codes.Internal, "internal error")
		}
	}()
	return next(ctx, req)
}

// ---- level 09: authentication ----
func authenticationInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	md, _ := metadata.FromIncomingContext(ctx)
	var id identity
	var known bool
	if values := md.Get("authorization"); len(values) > 0 {
		id, known = tokens[strings.TrimPrefix(values[0], "Bearer ")]
	}

	if !known && !publicMethods[info.FullMethod] {
		return nil, status.Error(codes.Unauthenticated, "missing or invalid token")
	}

	// A public RPC still gets an identity if one was offered - "public" means "a
	// credential is not REQUIRED", not "ignore credentials".
	if known {
		ctx = context.WithValue(ctx, identityKey{}, id)
	}
	return next(ctx, req)
}

// ---- level 10: authorization ----
func authorizationInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	needed, restricted := requiredRole[info.FullMethod]
	if restricted {
		id, ok := ctx.Value(identityKey{}).(identity)
		if !ok {
			return nil, status.Error(codes.Unauthenticated, "not authenticated")
		}
		if id.role != needed {
			return nil, status.Errorf(codes.PermissionDenied, "this method requires the %q role", needed)
		}
	}
	return next(ctx, req)
}

// notesServer holds the state. A gRPC server serves calls CONCURRENTLY on many
// goroutines, so every access to these fields takes the mutex - the one
// production concern levels 00-10 could safely ignore.
type notesServer struct {
	notespb.UnimplementedNotesServer

	mu     sync.Mutex
	notes  map[int32]*notespb.Note
	nextID int32
}

// Not one line about tokens, roles, logging or panics below. Only notes.

func (s *notesServer) GetNote(ctx context.Context, req *notespb.GetNoteRequest) (*notespb.Note, error) {
	if req.GetId() <= 0 { // level 06: validation is still the handler's job
		return nil, status.Error(codes.InvalidArgument, "id must be positive")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	note, ok := s.notes[req.GetId()]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "no note %d", req.GetId())
	}
	return note, nil
}

func (s *notesServer) CreateNote(ctx context.Context, req *notespb.CreateNoteRequest) (*notespb.Note, error) {
	if strings.TrimSpace(req.GetTitle()) == "" {
		return nil, status.Error(codes.InvalidArgument, "title must not be empty")
	}
	// The identity is guaranteed present: this RPC is not in publicMethods.
	id, ok := ctx.Value(identityKey{}).(identity)
	if !ok {
		return nil, status.Error(codes.Internal, "interceptor did not set an identity")
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	note := &notespb.Note{Id: s.nextID, Title: req.GetTitle(), Author: id.user}
	s.notes[s.nextID] = note
	s.nextID++
	return note, nil
}

func (s *notesServer) DeleteNote(ctx context.Context, req *notespb.DeleteNoteRequest) (*notespb.DeleteNoteResponse, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.notes, req.GetId()) // idempotent: deleting a gone note is not an error
	return &notespb.DeleteNoteResponse{Remaining: int32(len(s.notes))}, nil
}

func (s *notesServer) count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.notes)
}

func (s *notesServer) has(id int32) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, ok := s.notes[id]
	return ok
}

func startServer(addr string) (*grpc.Server, net.Listener, *notesServer) {
	// THE ORDER. Outside-in: log everything, recover from panics, then identify
	// the caller, then decide what they may do, then run the handler.
	srv := grpc.NewServer(grpc.ChainUnaryInterceptor(
		loggingInterceptor,
		recoveryInterceptor,
		authenticationInterceptor,
		authorizationInterceptor,
	))
	svc := &notesServer{
		notes:  map[int32]*notespb.Note{1: {Id: 1, Title: "read the .proto first", Author: "alice"}},
		nextID: 2,
	}
	notespb.RegisterNotesServer(srv, svc)

	ln, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatal(err)
	}
	go srv.Serve(ln)
	return srv, ln, svc
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--serve" {
		srv, ln, _ := startServer("127.0.0.1:50051")
		fmt.Printf("listening on %s  (try grpcurl, or point level 12's client at it)\n", ln.Addr())
		defer srv.Stop()
		select {}
	}

	srv, ln, svc := startServer("127.0.0.1:0")
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := notespb.NewNotesClient(conn)

	callCtx := func(token string) (context.Context, func()) {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		if token != "" {
			ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs("authorization", "Bearer "+token))
		}
		return ctx, cancel
	}

	fmt.Println("== GetNote is PUBLIC ==")
	ctx, cancel := callCtx("")
	note, err := client.GetNote(ctx, &notespb.GetNoteRequest{Id: 1})
	cancel()
	fmt.Printf("GetNote(1)    anonymous   -> %-18s title=%q\n", status.Code(err), note.GetTitle())
	if err != nil || note.GetAuthor() != "alice" {
		panic("FAILED")
	}

	ctx, cancel = callCtx("")
	_, err = client.GetNote(ctx, &notespb.GetNoteRequest{Id: 99})
	cancel()
	fmt.Printf("GetNote(99)   anonymous   -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.NotFound {
		panic("FAILED")
	}

	ctx, cancel = callCtx("")
	_, err = client.GetNote(ctx, &notespb.GetNoteRequest{Id: 0})
	cancel()
	fmt.Printf("GetNote(0)    anonymous   -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.InvalidArgument {
		panic("FAILED")
	}

	fmt.Println("\n== CreateNote needs ANY valid token ==")
	ctx, cancel = callCtx("")
	_, err = client.CreateNote(ctx, &notespb.CreateNoteRequest{Title: "sneaky"})
	cancel()
	fmt.Printf("CreateNote    anonymous   -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.Unauthenticated {
		panic("FAILED")
	}

	ctx, cancel = callCtx("bob-token")
	created, err := client.CreateNote(ctx, &notespb.CreateNoteRequest{Title: "bob's note"})
	cancel()
	fmt.Printf("CreateNote    bob/viewer  -> %-18s id=%d author=%q\n",
		status.Code(err), created.GetId(), created.GetAuthor())
	if err != nil || created.GetAuthor() != "bob" {
		panic("FAILED")
	}
	createdID := created.GetId()

	ctx, cancel = callCtx("bob-token")
	_, err = client.CreateNote(ctx, &notespb.CreateNoteRequest{Title: "   "})
	cancel()
	fmt.Printf("CreateNote(\"\")bob/viewer  -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.InvalidArgument {
		panic("FAILED")
	}

	fmt.Println("\n== DeleteNote needs the admin role specifically ==")
	ctx, cancel = callCtx("bob-token")
	_, err = client.DeleteNote(ctx, &notespb.DeleteNoteRequest{Id: createdID})
	cancel()
	fmt.Printf("DeleteNote    bob/viewer  -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.PermissionDenied {
		panic("FAILED")
	}
	if !svc.has(createdID) {
		panic("FAILED: a denied call must not change state")
	}

	ctx, cancel = callCtx("alice-token")
	delRes, err := client.DeleteNote(ctx, &notespb.DeleteNoteRequest{Id: createdID})
	cancel()
	fmt.Printf("DeleteNote    alice/admin -> %-18s remaining=%d\n", status.Code(err), delRes.GetRemaining())
	if err != nil || svc.has(createdID) {
		panic("FAILED")
	}

	// Idempotent: deleting it again is still OK, with the same end state.
	ctx, cancel = callCtx("alice-token")
	delRes, err = client.DeleteNote(ctx, &notespb.DeleteNoteRequest{Id: createdID})
	cancel()
	fmt.Printf("DeleteNote    again       -> %-18s remaining=%d  (idempotent)\n",
		status.Code(err), delRes.GetRemaining())
	if err != nil || delRes.GetRemaining() != 1 || svc.count() != 1 {
		panic("FAILED")
	}

	fmt.Println("\nper call, in order: log -> recover -> authenticate -> authorize -> validate -> act")
	fmt.Println("OK")
}
