/*
FOUNDATION LEVEL 06 - Status codes: gRPC's deliberate error vocabulary
==========================================================================
Every gRPC call ends with a status code, exactly the way every HTTP response
ends with a status code. `OK` (0) means it worked; anything else means it did
not, and the code says WHY in a way the caller can branch on without reading
English error text.

THE MAPPING AGAINST REST (the point of this level)

	REST                     gRPC                  meaning
	----------------------   -------------------   -----------------------------
	200 OK                   OK                    it worked
	400 Bad Request          INVALID_ARGUMENT      your request is nonsense
	401 Unauthorized         UNAUTHENTICATED       we do not know who you are
	403 Forbidden            PERMISSION_DENIED     we know you; the answer is no
	404 Not Found            NOT_FOUND             no such resource
	404 Not Found (no route) UNIMPLEMENTED         no such METHOD (see level 00)
	409 Conflict             ALREADY_EXISTS        creating something that exists
	429 Too Many Requests    RESOURCE_EXHAUSTED    rate limited / over quota
	500 Internal Error       INTERNAL              a bug on our side
	503 Unavailable          UNAVAILABLE           transient; retry with backoff
	504 Gateway Timeout      DEADLINE_EXCEEDED     took longer than you allowed

	Note the ONE place gRPC is sharper than HTTP: REST collapses "no such URL"
	and "no such record" into a single 404. gRPC splits them into UNIMPLEMENTED
	(the method does not exist) and NOT_FOUND (the method exists, the data does
	not) - a distinction that matters enormously when you are debugging.

You will learn
  - `status.Error(codes.X, "message")` is how a handler returns a chosen status;
    the returned error IS the status
  - NEVER return a plain `errors.New` or `fmt.Errorf` from a handler - it becomes
    codes.Unknown, which tells the caller nothing
  - the client reads `status.Code(err)`, which returns codes.OK for a nil error,
    so it is always safe to call
  - UNAUTHENTICATED vs PERMISSION_DENIED is the 401-vs-403 distinction, and
    confusing them is the single most common gRPC API design mistake
  - which codes are safe to retry (UNAVAILABLE, RESOURCE_EXHAUSTED) and which
    never are (INVALID_ARGUMENT, NOT_FOUND, PERMISSION_DENIED) - see level 12

Run it   go run ./gRPC/Foundation/golang/06_status_codes
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"dsapractice/api/gRPC/Foundation/golang/pb/statusespb"
)

var secrets = map[string]string{"launch-codes": "0000", "wifi": "hunter2"}

const validToken = "s3cret-token"

// The token and role travel in REQUEST FIELDS here on purpose. Real services put
// credentials in metadata and check them in an interceptor - that is levels
// 07/09/10. This level is ONLY about choosing the right status code.

type vaultServer struct {
	statusespb.UnimplementedVaultServer
}

func (s *vaultServer) GetSecret(ctx context.Context, req *statusespb.GetSecretRequest) (*statusespb.Secret, error) {
	// Order matters, and it is always this order. Each check answers a different
	// question, and a later check would leak information if it ran before an
	// earlier one (telling an anonymous caller that a secret exists is a leak).

	// 1. Is the request even well-formed? -> INVALID_ARGUMENT (REST 400)
	if req.GetId() == "" {
		return nil, status.Error(codes.InvalidArgument, "id must not be empty")
	}

	// 2. Do we know who this is at all? -> UNAUTHENTICATED (REST 401)
	if req.GetToken() != validToken {
		return nil, status.Error(codes.Unauthenticated, "missing or invalid token")
	}

	// 3. We know who they are - are they allowed? -> PERMISSION_DENIED (403)
	if req.GetId() == "launch-codes" && req.GetRole() != "admin" {
		return nil, status.Errorf(codes.PermissionDenied,
			"role %q may not read the launch codes", req.GetRole())
	}

	// 4. Allowed, but does the thing exist? -> NOT_FOUND (REST 404)
	value, ok := secrets[req.GetId()]
	if !ok {
		return nil, status.Errorf(codes.NotFound, "no secret named %q", req.GetId())
	}

	// 5. Everything checked out. A nil error means status OK.
	return &statusespb.Secret{Id: req.GetId(), Value: value}, nil
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	statusespb.RegisterVaultServer(srv, &vaultServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := statusespb.NewVaultClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	cases := []struct {
		label string
		req   *statusespb.GetSecretRequest
		want  codes.Code
	}{
		{"well-formed, authorised, exists",
			&statusespb.GetSecretRequest{Id: "wifi", Token: validToken, Role: "viewer"}, codes.OK},
		{"empty id",
			&statusespb.GetSecretRequest{Id: "", Token: validToken, Role: "viewer"}, codes.InvalidArgument},
		{"no token at all",
			&statusespb.GetSecretRequest{Id: "wifi"}, codes.Unauthenticated},
		{"known caller, wrong role",
			&statusespb.GetSecretRequest{Id: "launch-codes", Token: validToken, Role: "viewer"}, codes.PermissionDenied},
		{"authorised, no such secret",
			&statusespb.GetSecretRequest{Id: "nope", Token: validToken, Role: "admin"}, codes.NotFound},
	}

	for _, c := range cases {
		res, err := client.GetSecret(ctx, c.req)
		// status.Code(err) is the machine-readable part you branch on.
		// status.Convert(err).Message() is for humans and logs only.
		code := status.Code(err)
		detail := ""
		if err != nil {
			detail = status.Convert(err).Message()
		} else {
			detail = res.GetValue()
		}
		fmt.Printf("%-32s -> %-18s %q\n", c.label, code, detail)
		if code != c.want {
			panic("FAILED: " + c.label)
		}
	}

	// UNIMPLEMENTED is the distinction REST cannot make: the method itself does
	// not exist, as opposed to the data not existing (NOT_FOUND above).
	err = conn.Invoke(ctx, "/foundation.statuses.v1.Vault/DeleteSecret",
		&statusespb.GetSecretRequest{Id: "wifi"}, &statusespb.Secret{})
	fmt.Printf("%-32s -> %-18s (REST would also say 404 here)\n", "no such method", status.Code(err))
	if status.Code(err) != codes.Unimplemented {
		panic("FAILED")
	}

	// A plain Go error from a handler would land here as codes.Unknown. Proving
	// it needs a deliberately misbehaving handler, so instead just name it: the
	// rule is to ALWAYS wrap with status.Error, never return a bare error.
	fmt.Printf("\n%-32s -> %-18s (this is why you never return a bare error)\n",
		"a handler returning errors.New", codes.Unknown)

	fmt.Println("\nretry policy is a PROPERTY of the status code (see level 12):")
	for _, row := range [][2]string{
		{"OK", "-"},
		{"INVALID_ARGUMENT", "never - the request itself is wrong"},
		{"UNAUTHENTICATED", "never - fix the credential first"},
		{"PERMISSION_DENIED", "never - the answer will not change"},
		{"NOT_FOUND", "never - it still will not exist"},
		{"RESOURCE_EXHAUSTED", "yes, with backoff"},
		{"UNAVAILABLE", "yes, with backoff"},
		{"DEADLINE_EXCEEDED", "only if the call is idempotent"},
		{"INTERNAL", "no - it is a bug, retrying hides it"},
	} {
		fmt.Printf("  %-20s %s\n", row[0], row[1])
	}

	fmt.Println("\nOK")
}
