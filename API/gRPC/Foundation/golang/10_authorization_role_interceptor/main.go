/*
FOUNDATION LEVEL 10 - Authorization: what you are allowed to do
====================================================================
Authentication (level 09) established WHO is calling. Authorization is a
SEPARATE question: is THIS identified caller allowed to invoke THIS specific
RPC? Two callers can both pass authentication and still get different answers
here. This level adds a SECOND interceptor, layered on top of level 09's, and
the layering is the lesson.

	grpc.ChainUnaryInterceptor(authenticationInterceptor, authorizationInterceptor)
	                           ^ runs first: sets identity  ^ runs second: reads it

	Order is not a style choice. Authorization CANNOT run first - it has nothing
	to decide with until authentication has produced an identity.

WHICH RPC NEEDS WHICH ROLE

	ListReports    any authenticated caller
	DeleteReport   the "admin" role only

	The authorization interceptor learns which RPC it is wrapping from
	`info.FullMethod`, so one interceptor protects the whole service with a table -
	rather than an `if role != "admin"` scattered in every handler.

You will learn
  - PERMISSION_DENIED means "we know exactly who you are, and the answer is
    still no" - REST's 403. Do not confuse it with UNAUTHENTICATED (401), which
    means "who even ARE you"
  - role-based access control (RBAC) in its simplest honest form: a table from
    method path to required role
  - the SAME RPC behaves differently per caller, and that decision lives in one
    interceptor, not smeared across handlers
  - a denied call must change NO state - the interceptor returns before the
    handler runs, so this is structurally guaranteed rather than remembered
  - authentication and authorization compose: level 11 uses exactly these two
    interceptors, unchanged in shape

Run it   go run ./gRPC/Foundation/golang/10_authorization_role_interceptor
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

	"dsapractice/api/gRPC/Foundation/golang/pb/authzpb"
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

var reports = map[int32]string{1: "Q1 report", 2: "Q2 report"}

// THE POLICY, in one readable place. Keys are the full method paths gRPC uses on
// the wire; the value is the role required to call them. An RPC absent from this
// table needs authentication but no particular role.
var requiredRole = map[string]string{
	"/foundation.authz.v1.Reports/DeleteReport": "admin",
}

// ---- level 09's interceptor, unchanged in shape ----
func authenticationInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	md, _ := metadata.FromIncomingContext(ctx)
	values := md.Get("authorization")
	if len(values) == 0 {
		return nil, status.Error(codes.Unauthenticated, "missing or invalid token")
	}
	token := strings.TrimPrefix(values[0], "Bearer ")
	id, known := tokens[token]
	if !known {
		return nil, status.Error(codes.Unauthenticated, "missing or invalid token")
	}
	return next(context.WithValue(ctx, identityKey{}, id), req)
}

// ---- the NEW interceptor: it runs INSIDE authentication, so identity exists ----
func authorizationInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
	next grpc.UnaryHandler) (any, error) {

	// This value exists ONLY because authenticationInterceptor ran first. If the
	// chain order were reversed, this type assertion would fail - which is the
	// whole reason order matters.
	id, ok := ctx.Value(identityKey{}).(identity)
	if !ok {
		return nil, status.Error(codes.Unauthenticated, "not authenticated")
	}

	needed, restricted := requiredRole[info.FullMethod]
	if restricted && id.role != needed {
		fmt.Printf("  [authz] %q has role %q, %s requires %q -> denied\n",
			id.user, id.role, info.FullMethod, needed)
		// Returning here means the handler never runs, so no state can change.
		return nil, status.Errorf(codes.PermissionDenied, "this method requires the %q role", needed)
	}

	fmt.Printf("  [authz] %q allowed to call %s\n", id.user, info.FullMethod)
	return next(ctx, req)
}

// Neither handler contains a single line about tokens or roles. That is the
// point: the policy is enforced above them, uniformly, and cannot be forgotten
// when someone adds the next RPC.
type reportsServer struct {
	authzpb.UnimplementedReportsServer
}

func (s *reportsServer) ListReports(ctx context.Context, req *authzpb.ListReportsRequest) (*authzpb.ListReportsResponse, error) {
	titles := make([]string, 0, len(reports))
	for _, t := range reports {
		titles = append(titles, t)
	}
	return &authzpb.ListReportsResponse{Titles: titles}, nil
}

func (s *reportsServer) DeleteReport(ctx context.Context, req *authzpb.DeleteReportRequest) (*authzpb.DeleteReportResponse, error) {
	delete(reports, req.GetId()) // idempotent: deleting a gone report is fine
	return &authzpb.DeleteReportResponse{Remaining: int32(len(reports))}, nil
}

func main() {
	// Outside-in. Authentication MUST come first: authorization reads what it sets.
	srv := grpc.NewServer(grpc.ChainUnaryInterceptor(
		authenticationInterceptor,
		authorizationInterceptor,
	))
	authzpb.RegisterReportsServer(srv, &reportsServer{})

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
	client := authzpb.NewReportsClient(conn)

	callCtx := func(token string) (context.Context, func()) {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		if token != "" {
			ctx = metadata.NewOutgoingContext(ctx, metadata.Pairs("authorization", "Bearer "+token))
		}
		return ctx, cancel
	}

	// --- no credential: authentication rejects it before authorization runs ---
	ctx, cancel := callCtx("")
	_, err = client.ListReports(ctx, &authzpb.ListReportsRequest{})
	cancel()
	fmt.Printf("ListReports   (anonymous)  -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.Unauthenticated {
		panic("FAILED")
	}

	// --- a viewer MAY list ---
	ctx, cancel = callCtx("bob-token")
	listRes, err := client.ListReports(ctx, &authzpb.ListReportsRequest{})
	cancel()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("ListReports   (bob/viewer) -> %-18s %d titles\n", codes.OK, len(listRes.GetTitles()))
	if len(listRes.GetTitles()) != 2 {
		panic("FAILED")
	}

	// --- but a viewer may NOT delete: 403, not 401. Bob is known. ---
	ctx, cancel = callCtx("bob-token")
	_, err = client.DeleteReport(ctx, &authzpb.DeleteReportRequest{Id: 1})
	cancel()
	fmt.Printf("DeleteReport  (bob/viewer) -> %-18s %q\n", status.Code(err), status.Convert(err).Message())
	if status.Code(err) != codes.PermissionDenied {
		panic("FAILED")
	}
	if len(reports) != 2 {
		panic("FAILED: the denied call must not have changed any state")
	}

	// --- an admin may delete ---
	ctx, cancel = callCtx("alice-token")
	delRes, err := client.DeleteReport(ctx, &authzpb.DeleteReportRequest{Id: 1})
	cancel()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("DeleteReport  (alice/admin)-> %-18s remaining=%d\n", codes.OK, delRes.GetRemaining())
	if delRes.GetRemaining() != 1 {
		panic("FAILED")
	}

	fmt.Println("\nthe two statuses answer two different questions:")
	fmt.Println("  Unauthenticated  = we do not know who you are   (REST 401)")
	fmt.Println("  PermissionDenied = we know you; the answer is no (REST 403)")

	fmt.Println("OK")
}
