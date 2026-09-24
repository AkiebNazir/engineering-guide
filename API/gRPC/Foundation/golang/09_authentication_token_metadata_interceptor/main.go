/*
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Interceptors (level 08) are the mechanism; authentication is the first serious
thing people put in one. Authentication answers exactly ONE question: "do we
recognize this caller at all?" It says NOTHING about what they are allowed to
do - that is level 10, authorization, and it is a deliberately separate concept.

The credential arrives in METADATA (level 07), not in a request field - exactly
like REST's `Authorization: Bearer <token>` header, because it IS that header.
Notice that ../../proto/authn.proto has no token field anywhere: the contract
describes the DATA, and a credential is not data.

	client: metadata.Pairs("authorization", "Bearer alice-token")
	server: an interceptor reads it and rejects BEFORE the handler runs

This checks a token against a hardcoded lookup table. Real systems verify a
signed JWT or an mTLS peer certificate (see
../../../labs/golang/04_mtls_service_identity) - the SHAPE of the check is
identical: reject before the real handler ever runs if the token is missing or
unknown.

You will learn
  - "authorization" is the conventional metadata key, lower-cased like all of them
  - an authentication interceptor SHORT-CIRCUITS the chain by returning an error
    instead of calling `next` - the real handler never runs at all
  - UNAUTHENTICATED is the status for "we do not know who you are" - the direct
    analogue of REST's 401, and never to be confused with PERMISSION_DENIED
  - context.WithValue is how Go passes the identified caller down to the handler,
    keyed by an unexported type so no other package can collide with it
  - a plaintext channel means the token is readable on the wire; this is exactly
    why you use TLS credentials in production, not `insecure.NewCredentials()`

Run it   go run ./gRPC/Foundation/golang/09_authentication_token_metadata_interceptor
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/authnpb"
)

type identity struct {
	user string
	role string
}

// A stand-in for "who is allowed in", the way a real system would verify a
// signed token or consult a database instead of this map.
var tokens = map[string]identity{
	"alice-token": {user: "alice", role: "admin"},
	"bob-token":   {user: "bob", role: "viewer"},
}

// An UNEXPORTED key type. This is the standard Go idiom: no other package can
// construct this type, so nothing can accidentally overwrite our context value.
type identityKey struct{}

// authenticationInterceptor runs before EVERY handler on this server. Its only
// job is to turn a credential into an identity, or to reject the call.
func authenticationInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Error(codes.Unauthenticated, "missing bearer token")
	}

	values := md.Get("authorization")
	if len(values) == 0 {
		// Returning here WITHOUT calling next() is the short circuit: the real
		// handler never runs.
		return nil, status.Error(codes.Unauthenticated, "missing bearer token")
	}

	token, hasPrefix := strings.CutPrefix(values[0], "Bearer ")
	if !hasPrefix {
		return nil, status.Error(codes.Unauthenticated, "missing bearer token")
	}

	id, known := tokens[token]
	if !known {
		// Keep the message vague on purpose - do not help a caller guess which
		// tokens exist.
		return nil, status.Error(codes.Unauthenticated, "invalid token")
	}

	fmt.Printf("  [authn] %s authenticated as %q (role %q)\n", info.FullMethod, id.user, id.role)

	// Hand the identity down to the handler on a NEW context. Contexts are
	// immutable, so WithValue returns a copy - you must pass the copy to next().
	return next(context.WithValue(ctx, identityKey{}, id), req)
}

type identityServer struct {
	authnpb.UnimplementedIdentityServer
}

func (s *identityServer) WhoAmI(ctx context.Context, req *authnpb.WhoAmIRequest) (*authnpb.WhoAmIResponse, error) {
	// No token handling here at all. By the time this runs, the interceptor has
	// already guaranteed the context carries an identity - that guarantee is the
	// entire value of doing it in an interceptor instead of in every handler.
	id, ok := ctx.Value(identityKey{}).(identity)
	if !ok {
		return nil, status.Error(codes.Internal, "interceptor did not set an identity")
	}
	return &authnpb.WhoAmIResponse{User: id.user, Role: id.role}, nil
}

func main() {
	srv := grpc.NewServer(grpc.ChainUnaryInterceptor(authenticationInterceptor))
	authnpb.RegisterIdentityServer(srv, &identityServer{})

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := authnpb.NewIdentityClient(conn)

	// whoami calls WhoAmI with the given token, or with no metadata at all when
	// token is empty, and reports what came back.
	whoami := func(token string) (codes.Code, string) {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		if token != "" {
			ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs("authorization", "Bearer "+token))
		}
		res, err := client.WhoAmI(ctx, &authnpb.WhoAmIRequest{})
		if err != nil {
			return status.Code(err), status.Convert(err).Message()
		}
		return codes.OK, res.GetUser() + "/" + res.GetRole()
	}

	code, detail := whoami("")
	fmt.Printf("WhoAmI  (no metadata)              -> %-16s %q\n", code, detail)
	if code != codes.Unauthenticated {
		panic("FAILED")
	}

	code, detail = whoami("not-a-real-token")
	fmt.Printf("WhoAmI  Bearer not-a-real-token    -> %-16s %q\n", code, detail)
	if code != codes.Unauthenticated {
		panic("FAILED")
	}

	code, detail = whoami("alice-token")
	fmt.Printf("WhoAmI  Bearer alice-token         -> %-16s %q\n", code, detail)
	if code != codes.OK || detail != "alice/admin" {
		panic("FAILED")
	}

	code, detail = whoami("bob-token")
	fmt.Printf("WhoAmI  Bearer bob-token           -> %-16s %q\n", code, detail)
	if code != codes.OK || detail != "bob/viewer" {
		panic("FAILED")
	}

	// BOTH callers above were authenticated successfully, and they have
	// different roles. Nothing here cares about that yet - deciding what each one
	// may DO is a separate question, answered in level 10.
	fmt.Println("\nalice and bob both passed authentication despite different roles:")
	fmt.Println("  'who are you' is answered; 'what may you do' is level 10")

	fmt.Println("OK")
}
