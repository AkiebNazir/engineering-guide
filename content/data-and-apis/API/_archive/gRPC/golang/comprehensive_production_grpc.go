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
)

// Conceptually assuming we have a generated PB package
// type ServerInterface interface { Unary(ctx), Stream(stream) }

type server struct{}

// 1. Unary RPC (Standard Request/Response with Deadlines & Validation)
func (s *server) ProcessData(ctx context.Context, req interface{}) (interface{}, error) {
	// Validate Data
	// if req.Field == "" { return nil, status.Error(codes.InvalidArgument, "field required") }
	
	// Simulate work respecting context deadline
	select {
	case <-time.After(2 * time.Second):
		return nil, nil // Return response
	case <-ctx.Done():
		log.Println("Context cancelled by client")
		return nil, status.Error(codes.DeadlineExceeded, "deadline exceeded")
	}
}

// 2. Bidirectional Streaming RPC
func (s *server) RealtimeChat(stream interface{}) error { // Concept interface
	// for {
	// 	req, err := stream.Recv()
	// 	if err == io.EOF { return nil }
	// 	if err != nil { return err }
	// 	stream.Send(response)
	// }
	return nil
}

// --- Middleware (Unary Interceptor) ---
func AuthInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok || len(md["authorization"]) == 0 {
		return nil, status.Error(codes.Unauthenticated, "missing token")
	}

	token := md["authorization"][0]
	if token != "Bearer secret-jwt" {
		return nil, status.Error(codes.Unauthenticated, "invalid token")
	}

	// Token is valid, proceed to the actual RPC handler
	return handler(ctx, req)
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// Register Middleware during server startup
	opts := []grpc.ServerOption{
		grpc.UnaryInterceptor(AuthInterceptor),
	}
	
	grpcServer := grpc.NewServer(opts...)
	
	// pb.RegisterMyServiceServer(grpcServer, &server{})
	log.Println("gRPC Production Server started on :50051")
	grpcServer.Serve(lis)
}
