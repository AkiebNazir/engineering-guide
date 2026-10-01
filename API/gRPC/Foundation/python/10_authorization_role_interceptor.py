"""
FOUNDATION LEVEL 10 - Authorization: what you are allowed to do
====================================================================
Authentication (level 09) established WHO is calling. Authorization is a
SEPARATE question: is THIS identified caller allowed to invoke THIS specific
RPC? Two callers can both pass authentication and still get different answers
here. This level adds a SECOND interceptor, layered on top of level 09's, and
the layering is the lesson.

    interceptors=[AuthenticationInterceptor(), AuthorizationInterceptor()]
                   ^ runs first: sets identity      ^ runs second: reads identity

  Order is not a style choice. Authorization CANNOT run first - it has nothing
  to decide with until authentication has produced an identity.

WHICH RPC NEEDS WHICH ROLE
  ListReports    any authenticated caller
  DeleteReport   the "admin" role only

  The authorization interceptor learns which RPC it is wrapping from
  `handler_call_details.method`, so one interceptor protects the whole service
  with a table - rather than an `if role != "admin"` scattered in every handler.

You will learn
  * PERMISSION_DENIED means "we know exactly who you are, and the answer is
    still no" - REST's 403. Do not confuse it with UNAUTHENTICATED (401), which
    means "who even ARE you"
  * role-based access control (RBAC) in its simplest honest form: a table from
    method path to required role
  * the SAME RPC behaves differently per caller, and that decision lives in one
    interceptor, not smeared across handlers
  * a policy table has to be default-DENY-friendly: an RPC nobody remembered to
    list should fail closed in a real system, and this file shows where that
    decision goes
  * authentication and authorization compose: level 11 uses exactly these two
    interceptors, unchanged in shape

Run it   python 10_authorization_role_interceptor.py
"""
from concurrent import futures

import grpc

import authz_pb2 as pb
import authz_pb2_grpc as rpc

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}
REPORTS = {1: "Q1 report", 2: "Q2 report"}

# THE POLICY, in one readable place. Keys are the full method paths gRPC uses on
# the wire; the value is the role required to call them. An RPC absent from this
# table needs authentication but no particular role.
REQUIRED_ROLE = {
    "/foundation.authz.v1.Reports/DeleteReport": "admin",
}


# ---- level 09's interceptor, unchanged in shape ----
class AuthenticationInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def authenticated(request, context):
            md = dict(context.invocation_metadata())
            token = md.get("authorization", "").removeprefix("Bearer ")
            identity = TOKENS.get(token)
            if identity is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "missing or invalid token")
            context.identity = identity
            return handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            authenticated,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


# ---- the NEW interceptor: it runs INSIDE authentication, so identity exists ----
class AuthorizationInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method
        needed = REQUIRED_ROLE.get(method)  # None = no special role required
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def authorized(request, context):
            # This attribute exists ONLY because AuthenticationInterceptor ran
            # first. If the list order were reversed this would be an
            # AttributeError - which is the whole reason order matters.
            identity = getattr(context, "identity", None)
            if identity is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "not authenticated")

            if needed is not None and identity["role"] != needed:
                print(f"  [authz] {identity['user']!r} has role {identity['role']!r}, "
                      f"{method} requires {needed!r} -> denied")
                context.abort(grpc.StatusCode.PERMISSION_DENIED,
                              f"this method requires the {needed!r} role")

            print(f"  [authz] {identity['user']!r} allowed to call {method}")
            return handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            authorized,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


class ReportsServicer(rpc.ReportsServicer):
    # Neither handler contains a single line about tokens or roles. That is the
    # point: the policy is enforced above them, uniformly, and cannot be
    # forgotten when someone adds the next RPC.
    def ListReports(self, request, context) -> pb.ListReportsResponse:
        return pb.ListReportsResponse(titles=list(REPORTS.values()))

    def DeleteReport(self, request: pb.DeleteReportRequest, context) -> pb.DeleteReportResponse:
        REPORTS.pop(request.id, None)  # idempotent: deleting a gone report is fine
        return pb.DeleteReportResponse(remaining=len(REPORTS))


def call(fn, token: str | None, *args):
    metadata = (("authorization", f"Bearer {token}"),) if token is not None else ()
    try:
        return grpc.StatusCode.OK, fn(*args, timeout=2, metadata=metadata)
    except grpc.RpcError as e:
        return e.code(), e.details()


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.ReportsStub(channel)

        # --- no credential: authentication rejects it before authorization runs ---
        code, detail = call(stub.ListReports, None, pb.ListReportsRequest())
        print(f"ListReports   (anonymous)  -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.UNAUTHENTICATED

        # --- a viewer MAY list ---
        code, res = call(stub.ListReports, "bob-token", pb.ListReportsRequest())
        print(f"ListReports   (bob/viewer) -> {code.name:<18} {list(res.titles)}")
        assert code == grpc.StatusCode.OK and len(res.titles) == 2

        # --- but a viewer may NOT delete: 403, not 401. Bob is known. ---
        code, detail = call(stub.DeleteReport, "bob-token", pb.DeleteReportRequest(id=1))
        print(f"DeleteReport  (bob/viewer) -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.PERMISSION_DENIED
        assert len(REPORTS) == 2, "the denied call must not have changed any state"

        # --- an admin may delete ---
        code, res = call(stub.DeleteReport, "alice-token", pb.DeleteReportRequest(id=1))
        print(f"DeleteReport  (alice/admin)-> {code.name:<18} remaining={res.remaining}")
        assert code == grpc.StatusCode.OK and res.remaining == 1

        print("\nthe two statuses answer two different questions:")
        print("  UNAUTHENTICATED   = we do not know who you are   (REST 401)")
        print("  PERMISSION_DENIED = we know you; the answer is no (REST 403)")

    print("OK")


if __name__ == "__main__":
    # Outside-in. Authentication MUST come first: authorization reads what it sets.
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[AuthenticationInterceptor(), AuthorizationInterceptor()],
    )
    rpc.add_ReportsServicer_to_server(ReportsServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
