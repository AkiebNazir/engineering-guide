"""
FOUNDATION LEVEL 09 - Authentication: proving who you are
=============================================================
Interceptors (level 08) are the mechanism; authentication is the first serious
thing people put in one. Authentication answers exactly ONE question: "do we
recognize this caller at all?" It says NOTHING about what they are allowed to
do - that is level 10, authorization, and it is a deliberately separate concept.

The credential arrives in METADATA (level 07), not in a request field - exactly
like REST's `Authorization: Bearer <token>` header, because it IS that header.
Notice that ../proto/authn.proto has no token field anywhere: the contract
describes the DATA, and a credential is not data.

    client: metadata=(("authorization", "Bearer alice-token"),)
    server: an interceptor reads it and rejects BEFORE the handler runs

This checks a token against a hardcoded lookup table. Real systems verify a
signed JWT or an mTLS peer certificate (see
../../labs/python/03_interceptors_auth_logging_ratelimit.py and
../../labs/golang/04_mtls_service_identity) - the SHAPE of the check is
identical: reject before the real handler ever runs if the token is missing or
unknown.

You will learn
  * "authorization" is the conventional metadata key, lower-cased like all of them
  * an authentication interceptor SHORT-CIRCUITS the chain: on failure it never
    calls the real handler at all
  * UNAUTHENTICATED is the status for "we do not know who you are" - the direct
    analogue of REST's 401, and never to be confused with PERMISSION_DENIED
  * how the identified caller reaches the handler: Python has no request-scoped
    context value, so this stashes the identity on the ServicerContext object
    itself (Go uses context.WithValue - see main.go)
  * a plaintext channel means the token is readable on the wire; this is exactly
    why you use TLS credentials in production, not `insecure_channel`

Run it   python 09_authentication_token_metadata_interceptor.py
"""
from concurrent import futures

import grpc

import authn_pb2 as pb
import authn_pb2_grpc as rpc

# A stand-in for "who is allowed in", the way a real system would verify a
# signed token or consult a database instead of this dict.
TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}


class AuthenticationInterceptor(grpc.ServerInterceptor):
    """Runs before EVERY handler on this server. Its only job is to turn a
    credential into an identity, or to reject the call."""

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def authenticated(request, context):
            md = dict(context.invocation_metadata())
            header = md.get("authorization", "")

            if not header.startswith("Bearer "):
                # abort() raises, so the real handler is NEVER called.
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "missing bearer token")

            token = header.removeprefix("Bearer ")
            identity = TOKENS.get(token)
            if identity is None:
                # Keep the message vague on purpose - do not help a caller guess
                # which tokens exist.
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid token")

            # Hand the identity down to the handler. Python's ServicerContext is
            # a per-call object, so attaching an attribute to it is the idiomatic
            # trick (Go puts it in the context.Context instead).
            context.identity = identity
            print(f"  [authn] {handler_call_details.method} authenticated as "
                  f"{identity['user']!r} (role {identity['role']!r})")
            return handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            authenticated,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


class IdentityServicer(rpc.IdentityServicer):
    def WhoAmI(self, request: pb.WhoAmIRequest, context: grpc.ServicerContext) -> pb.WhoAmIResponse:
        # No token handling here at all. By the time this runs, the interceptor
        # has already guaranteed context.identity exists - that guarantee is the
        # entire value of doing it in an interceptor instead of in every handler.
        identity = context.identity
        return pb.WhoAmIResponse(user=identity["user"], role=identity["role"])


def whoami(stub, token: str | None):
    metadata = (("authorization", f"Bearer {token}"),) if token is not None else ()
    try:
        res = stub.WhoAmI(pb.WhoAmIRequest(), timeout=2, metadata=metadata)
        return grpc.StatusCode.OK, f"{res.user}/{res.role}"
    except grpc.RpcError as e:
        return e.code(), e.details()


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.IdentityStub(channel)

        code, detail = whoami(stub, None)
        print(f"WhoAmI  (no metadata)              -> {code.name:<16} {detail!r}")
        assert code == grpc.StatusCode.UNAUTHENTICATED

        code, detail = whoami(stub, "not-a-real-token")
        print(f"WhoAmI  Bearer not-a-real-token    -> {code.name:<16} {detail!r}")
        assert code == grpc.StatusCode.UNAUTHENTICATED

        code, detail = whoami(stub, "alice-token")
        print(f"WhoAmI  Bearer alice-token         -> {code.name:<16} {detail!r}")
        assert code == grpc.StatusCode.OK and detail == "alice/admin"

        code, detail = whoami(stub, "bob-token")
        print(f"WhoAmI  Bearer bob-token           -> {code.name:<16} {detail!r}")
        assert code == grpc.StatusCode.OK and detail == "bob/viewer"

        # BOTH callers above were authenticated successfully, and they have
        # different roles. Nothing here cares about that yet - deciding what each
        # one may DO is a separate question, answered in level 10.
        print("\nalice and bob both passed authentication despite different roles:")
        print("  'who are you' is answered; 'what may you do' is level 10")

    print("OK")


if __name__ == "__main__":
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[AuthenticationInterceptor()],
    )
    rpc.add_IdentityServicer_to_server(IdentityServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
