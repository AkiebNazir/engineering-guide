package main

import (
	"context"
	"log"
	"net"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Mock PB types to make file compilable conceptually
type AuthRequest struct { Token string }
type AuthResponse struct { IsValid bool; UserId string }
type UnimplementedMicroserviceSystemServer struct{}
func (UnimplementedMicroserviceSystemServer) ValidateToken(context.Context, *AuthRequest) (*AuthResponse, error) { return nil, nil }

type server struct {
	UnimplementedMicroserviceSystemServer
}

func (s *server) ValidateToken(ctx context.Context, req *AuthRequest) (*AuthResponse, error) {
	if req.Token == "" {
		return nil, status.Error(codes.InvalidArgument, "Token missing")
	}
	isValid := req.Token == "secret-jwt"
	return &AuthResponse{IsValid: isValid, UserId: "usr_123"}, nil
}

func main() {
	lis, _ := net.Listen("tcp", ":50051")
	s := grpc.NewServer()
	// pb.RegisterMicroserviceSystemServer(s, &server{})
	log.Printf("Auth server listening at %v", lis.Addr())
	s.Serve(lis)
}
