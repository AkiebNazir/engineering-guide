// REAL-WORLD EXAMPLE: google.golang.org/grpc (External 1)
// Demonstrates: Unary Interceptors (Middleware), Context metadata extraction, Error Codes
package main

import (
	"context"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	// pb "path/to/userpb"
)

// --- MOCK PROTOBUF TYPES ---
type GetUserRequest struct{ Id string }
type User struct{ Name string }
type GetUserResponse struct{ User *User }
// ---------------------------

type server struct {
	// pb.UnimplementedUserServiceServer
}

func (s *server) GetUser(ctx context.Context, req *GetUserRequest) (*GetUserResponse, error) {
	// Extract metadata (like headers)
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok || len(md["authorization"]) == 0 {
		return nil, status.Errorf(codes.Unauthenticated, "missing token")
	}

	if req.Id == "1" {
		return &GetUserResponse{User: &User{Name: "Alice"}}, nil
	}
	return nil, status.Errorf(codes.NotFound, "User not found")
}

// 1. Unary Interceptor (Middleware for logging and panic recovery)
func LoggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	start := time.Now()
	// Call the actual handler
	res, err := handler(ctx, req)
	log.Printf("Method: %s, Duration: %s, Error: %v", info.FullMethod, time.Since(start), err)
	return res, err
}

func main() {
	lis, _ := net.Listen("tcp", ":50051")
	
	// 2. Initialize Server with Interceptors
	s := grpc.NewServer(
		grpc.UnaryInterceptor(LoggingInterceptor),
	)
	
	// pb.RegisterUserServiceServer(s, &server{})
	log.Println("gRPC Server running on :50051")
	s.Serve(lis)
}
