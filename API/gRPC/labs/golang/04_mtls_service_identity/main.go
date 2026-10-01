/*
LAB 04 (advanced) - Mutual TLS: service identity between microservices, built from scratch
==========================================================================================
You will learn

  - TLS proves the SERVER is who it claims.  mTLS also proves the CLIENT is who it claims:

    client                                        server
    |--- ClientHello ------------------------->|
    |<-- server certificate (signed by CA) ----|   client checks: chain + hostname
    |<-- CertificateRequest -------------------|
    |--- client certificate (signed by CA) --->|   server checks: chain + not expired
    |======= encrypted gRPC traffic ===========|

  - the identity of the caller is then INSIDE the connection: read it from the certificate
    (peer.FromContext), no passwords or tokens to steal

  - authorization on top of authentication: allow-list by certificate Common Name

  - creating a tiny private CA with crypto/x509 (ECDSA P-256) - nothing is written to disk

  - the four ways a connection is refused, each demonstrated:
    1. no client certificate          2. certificate from an UNKNOWN CA
    3. EXPIRED certificate            4. server name does not match the certificate
    plus: a plaintext client cannot talk to a TLS server at all

  - production notes: short-lived certs (hours/days), automatic rotation (SPIFFE/SPIRE, cert-manager,
    service mesh), keep the CA key offline

Run it   go run ./gRPC/labs/golang/04_mtls_service_identity
*/
package main

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"fmt"
	"math/big"
	"net"
	"slices"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/peer"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/labs/golang/shoppb"
)

// ------------------------------------------------------- a tiny private CA --
type authority struct {
	cert *x509.Certificate
	key  *ecdsa.PrivateKey
	pool *x509.CertPool
}

func newCA(name string) *authority {
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: name},
		NotBefore: time.Now().Add(-time.Minute), NotAfter: time.Now().Add(24 * time.Hour),
		IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign,
	}
	der, _ := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	cert, _ := x509.ParseCertificate(der)
	pool := x509.NewCertPool()
	pool.AddCert(cert)
	return &authority{cert, key, pool}
}

// issue signs a leaf certificate. `server` picks the ExtKeyUsage; `validFor` may be negative (expired).
func (ca *authority) issue(cn string, server bool, dnsNames []string, validFor time.Duration) tls.Certificate {
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	serial, _ := rand.Int(rand.Reader, big.NewInt(1<<62))
	usage := x509.ExtKeyUsageClientAuth
	if server {
		usage = x509.ExtKeyUsageServerAuth
	}
	notBefore, notAfter := time.Now().Add(-time.Hour), time.Now().Add(validFor)
	if validFor < 0 { // an already-expired certificate
		notBefore, notAfter = time.Now().Add(-2*time.Hour), time.Now().Add(validFor)
	}
	tmpl := &x509.Certificate{
		SerialNumber: serial, Subject: pkix.Name{CommonName: cn},
		DNSNames: dnsNames, IPAddresses: []net.IP{net.ParseIP("127.0.0.1")},
		NotBefore: notBefore, NotAfter: notAfter,
		KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{usage},
	}
	der, _ := x509.CreateCertificate(rand.Reader, tmpl, ca.cert, &key.PublicKey, ca.key)
	return tls.Certificate{Certificate: [][]byte{der}, PrivateKey: key}
}

// ------------------------------------------------------------ the service ---
var allowedCallers = []string{"billing-service", "orders-service"} // authorization by identity

type server struct {
	shoppb.UnimplementedCatalogServer
}

func callerIdentity(ctx context.Context) (string, error) {
	p, ok := peer.FromContext(ctx)
	if !ok {
		return "", status.Error(codes.Unauthenticated, "no peer info")
	}
	tlsInfo, ok := p.AuthInfo.(credentials.TLSInfo)
	if !ok || len(tlsInfo.State.PeerCertificates) == 0 {
		return "", status.Error(codes.Unauthenticated, "no client certificate")
	}
	return tlsInfo.State.PeerCertificates[0].Subject.CommonName, nil
}

func (server) GetProduct(ctx context.Context, r *shoppb.GetProductRequest) (*shoppb.Product, error) {
	who, err := callerIdentity(ctx)
	if err != nil {
		return nil, err
	}
	if !slices.Contains(allowedCallers, who) {
		return nil, status.Errorf(codes.PermissionDenied, "service %q may not call the catalog", who)
	}
	return &shoppb.Product{Id: r.Id, Name: "Keyboard (requested by " + who + ")"}, nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	ca := newCA("Acme Internal CA")
	otherCA := newCA("Evil CA")
	serverCert := ca.issue("catalog.internal", true, []string{"catalog.internal", "localhost"}, time.Hour)

	lis, _ := net.Listen("tcp", "127.0.0.1:0")
	s := grpc.NewServer(grpc.Creds(credentials.NewTLS(&tls.Config{
		Certificates: []tls.Certificate{serverCert},
		ClientAuth:   tls.RequireAndVerifyClientCert, // <- this line makes it MUTUAL
		ClientCAs:    ca.pool,
		MinVersion:   tls.VersionTLS13,
	})))
	shoppb.RegisterCatalogServer(s, server{})
	go s.Serve(lis)
	defer s.Stop()

	try := func(label string, creds credentials.TransportCredentials) error {
		conn, _ := grpc.NewClient(lis.Addr().String(), grpc.WithTransportCredentials(creds))
		defer conn.Close()
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		p, err := shoppb.NewCatalogClient(conn).GetProduct(ctx, &shoppb.GetProductRequest{Id: 1})
		if err != nil {
			fmt.Printf("  %-34s REFUSED  %s\n", label, status.Code(err))
		} else {
			fmt.Printf("  %-34s ok       %s\n", label, p.Name)
		}
		return err
	}
	clientTLS := func(cert *tls.Certificate, roots *x509.CertPool, serverName string) credentials.TransportCredentials {
		cfg := &tls.Config{RootCAs: roots, ServerName: serverName, MinVersion: tls.VersionTLS13}
		if cert != nil {
			cfg.Certificates = []tls.Certificate{*cert}
		}
		return credentials.NewTLS(cfg)
	}

	fmt.Println("== the happy path ==")
	billing := ca.issue("billing-service", false, nil, time.Hour)
	must(try("billing-service (valid cert)", clientTLS(&billing, ca.pool, "catalog.internal")) == nil, "valid client")

	fmt.Println("\n== authenticated but not authorized (identity is known, policy says no) ==")
	marketing := ca.issue("marketing-service", false, nil, time.Hour)
	err := try("marketing-service (valid, not listed)", clientTLS(&marketing, ca.pool, "catalog.internal"))
	must(status.Code(err) == codes.PermissionDenied, "authz")

	fmt.Println("\n== the four ways a handshake is refused ==")
	must(try("1. no client certificate", clientTLS(nil, ca.pool, "catalog.internal")) != nil, "no cert")
	evil := otherCA.issue("billing-service", false, nil, time.Hour) // right NAME, wrong signer
	must(try("2. cert signed by an unknown CA", clientTLS(&evil, ca.pool, "catalog.internal")) != nil, "unknown CA")
	expired := ca.issue("billing-service", false, nil, -time.Minute)
	must(try("3. expired certificate", clientTLS(&expired, ca.pool, "catalog.internal")) != nil, "expired")
	must(try("4. server name mismatch", clientTLS(&billing, ca.pool, "payments.internal")) != nil, "hostname check")

	fmt.Println("\n== and a client that does not speak TLS at all ==")
	must(try("plaintext client", insecure.NewCredentials()) != nil, "plaintext refused")

	fmt.Println("\n  Note: every refusal surfaces on the client as Unavailable. In failures 1-3 the SERVER rejected the")
	fmt.Println("  client (TLS 1.3 reports that after the client thinks it is connected); in 4 the CLIENT rejected the")
	fmt.Println("  server. Look at the server-side TLS logs to see the real reason.")
	fmt.Println("\nOK")
}
