package main

import (
	"crypto/tls"
	"crypto/x509"
	"io/ioutil"
	"log"
	"net"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

func main() {
	// 1. Load the Certificates
	cert, err := tls.LoadX509KeyPair("../mtls/server-cert.pem", "../mtls/server-key.pem")
	if err != nil {
		log.Fatalf("Failed to load server certs: %v", err)
	}

	// 2. Load the CA certificate to verify clients
	caCert, err := ioutil.ReadFile("../mtls/ca-cert.pem")
	if err != nil {
		log.Fatalf("Failed to read CA cert: %v", err)
	}
	certPool := x509.NewCertPool()
	if !certPool.AppendCertsFromPEM(caCert) {
		log.Fatal("Failed to append CA cert")
	}

	// 3. Configure TLS to REQUIRE mutual authentication (mTLS)
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		ClientAuth:   tls.RequireAndVerifyClientCert,
		ClientCAs:    certPool,
	}

	// 4. Create the gRPC server with the TLS credentials
	creds := credentials.NewTLS(tlsConfig)
	server := grpc.NewServer(grpc.Creds(creds))

	// Register your handlers here...
	// pb.RegisterMyServiceServer(server, &myServer{})

	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	
	log.Println("gRPC mTLS Server running on :50051...")
	server.Serve(lis)
}
