"""
FOUNDATION LEVEL 11 (capstone) - One complete, PROTECTED gRPC service
=========================================================================
Nothing new here. Every idea from levels 00-10 - the .proto contract, typed
request/response fields, status codes, metadata, interceptors, authentication
and authorization - combined into one small service, end to end.

    GetNote      public         no credential needed at all
    CreateNote   authenticated  any valid token
    DeleteNote   admin only     a valid token AND the "admin" role

The interesting new wrinkle is PER-METHOD policy: a single interceptor chain
protects the whole service, but one RPC is deliberately public. That is done
with a table of method paths, not with an `if` inside each handler - so adding
the next RPC means adding a table row, and forgetting to do so fails CLOSED.

This is deliberately the same shape as ../../labs/python/03_interceptors_auth_logging_ratelimit.py
and ../../labs/golang/03_interceptor_chain. Once this feels easy, ../../labs/
(rich error details, mTLS identity, flow control, health checking, reflection)
is the very next step, not a jump.

You will learn
  * how the previous eleven small lessons compose into one real-looking,
    real-SECURED service
  * the deliberate order of operations per call: log -> recover -> authenticate
    -> authorize -> validate -> act
  * public-by-exception: the chain runs on every RPC, and the policy table is
    what makes one of them anonymous-friendly
  * that "a gRPC API" is not one big new idea - it is these small ideas layered
    in a fixed order

Run it        python 11_complete_protected_service.py
Keep serving  python 11_complete_protected_service.py --serve   (listens on 127.0.0.1:50051)
"""
import sys
import time
from concurrent import futures

import grpc

import notes_pb2 as pb
import notes_pb2_grpc as rpc

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

NOTES: dict[int, pb.Note] = {1: pb.Note(id=1, title="read the .proto first", author="alice")}
NEXT_ID = 2

# --- THE POLICY, in one place (level 10's idea, now with a public exception) ---
PUBLIC = {"/foundation.notes.v1.Notes/GetNote"}
REQUIRED_ROLE = {"/foundation.notes.v1.Notes/DeleteNote": "admin"}


def _rewrap(handler, fn):
    return grpc.unary_unary_rpc_method_handler(
        fn,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )


# ---- level 08: logging (outermost, so it sees every outcome) ----
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method.rsplit("/", 1)[-1]
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def logged(request, context):
            start = time.perf_counter()
            code = "OK"
            try:
                return handler.unary_unary(request, context)
            except Exception:
                code = "FAILED"
                raise
            finally:
                print(f"  [log] {method:<11} {code:<7} {(time.perf_counter() - start) * 1000:.2f}ms")

        return _rewrap(handler, logged)


# ---- level 08: panic recovery ----
class RecoveryInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def recovered(request, context):
            try:
                return handler.unary_unary(request, context)
            except Exception as exc:
                # grpcio implements context.abort() by raising a BARE Exception
                # after recording the status on the call. So "type is exactly
                # Exception" means "a handler deliberately chose a status" and
                # must pass straight through; anything else (RuntimeError,
                # KeyError, ...) is a genuine bug worth converting to INTERNAL.
                if type(exc) is Exception:
                    raise
                print(f"  [recovery] {exc!r} -> INTERNAL, server stays up")
                context.abort(grpc.StatusCode.INTERNAL, "internal error")

        return _rewrap(handler, recovered)


# ---- level 09: authentication ----
class AuthenticationInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        is_public = handler_call_details.method in PUBLIC
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def authenticated(request, context):
            token = dict(context.invocation_metadata()).get("authorization", "").removeprefix("Bearer ")
            identity = TOKENS.get(token)

            if identity is None and not is_public:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "missing or invalid token")

            # A public RPC still gets an identity if one was offered - "public"
            # means "a credential is not REQUIRED", not "ignore credentials".
            context.identity = identity
            return handler.unary_unary(request, context)

        return _rewrap(handler, authenticated)


# ---- level 10: authorization ----
class AuthorizationInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        needed = REQUIRED_ROLE.get(handler_call_details.method)
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        def authorized(request, context):
            if needed is not None:
                identity = getattr(context, "identity", None)
                if identity is None:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "not authenticated")
                if identity["role"] != needed:
                    context.abort(grpc.StatusCode.PERMISSION_DENIED,
                                  f"this method requires the {needed!r} role")
            return handler.unary_unary(request, context)

        return _rewrap(handler, authorized)


class NotesServicer(rpc.NotesServicer):
    """Not one line about tokens, roles, logging or crashes. Only notes."""

    def GetNote(self, request: pb.GetNoteRequest, context) -> pb.Note:
        if request.id <= 0:  # level 06: validation is still the handler's job
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id must be positive")
        note = NOTES.get(request.id)
        if note is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"no note {request.id}")
        return note

    def CreateNote(self, request: pb.CreateNoteRequest, context) -> pb.Note:
        global NEXT_ID
        if not request.title.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "title must not be empty")
        # context.identity is guaranteed non-None: this RPC is not in PUBLIC.
        note = pb.Note(id=NEXT_ID, title=request.title, author=context.identity["user"])
        NOTES[NEXT_ID] = note
        NEXT_ID += 1
        return note

    def DeleteNote(self, request: pb.DeleteNoteRequest, context) -> pb.DeleteNoteResponse:
        NOTES.pop(request.id, None)  # idempotent: deleting a gone note is not an error
        return pb.DeleteNoteResponse(remaining=len(NOTES))


def start_server(port: int = 0) -> tuple[grpc.Server, int]:
    # THE ORDER. Outside-in: log everything, recover from crashes, then identify
    # the caller, then decide what they may do, then run the handler.
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[
            LoggingInterceptor(),
            RecoveryInterceptor(),
            AuthenticationInterceptor(),
            AuthorizationInterceptor(),
        ],
    )
    rpc.add_NotesServicer_to_server(NotesServicer(), server)
    bound = server.add_insecure_port(f"127.0.0.1:{port}")
    server.start()
    return server, bound


def call(fn, token, request):
    metadata = (("authorization", f"Bearer {token}"),) if token else ()
    try:
        return grpc.StatusCode.OK, fn(request, timeout=2, metadata=metadata)
    except grpc.RpcError as e:
        return e.code(), e.details()


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.NotesStub(channel)

        print("== GetNote is PUBLIC ==")
        code, note = call(stub.GetNote, None, pb.GetNoteRequest(id=1))
        print(f"GetNote(1)    anonymous   -> {code.name:<18} title={note.title!r}")
        assert code == grpc.StatusCode.OK and note.author == "alice"

        code, detail = call(stub.GetNote, None, pb.GetNoteRequest(id=99))
        print(f"GetNote(99)   anonymous   -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.NOT_FOUND

        code, detail = call(stub.GetNote, None, pb.GetNoteRequest(id=0))
        print(f"GetNote(0)    anonymous   -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.INVALID_ARGUMENT

        print("\n== CreateNote needs ANY valid token ==")
        code, detail = call(stub.CreateNote, None, pb.CreateNoteRequest(title="sneaky"))
        print(f"CreateNote    anonymous   -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.UNAUTHENTICATED

        code, note = call(stub.CreateNote, "bob-token", pb.CreateNoteRequest(title="bob's note"))
        print(f"CreateNote    bob/viewer  -> {code.name:<18} id={note.id} author={note.author!r}")
        assert code == grpc.StatusCode.OK and note.author == "bob"
        created_id = note.id

        code, detail = call(stub.CreateNote, "bob-token", pb.CreateNoteRequest(title="   "))
        print(f"CreateNote('')bob/viewer  -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.INVALID_ARGUMENT

        print("\n== DeleteNote needs the admin role specifically ==")
        code, detail = call(stub.DeleteNote, "bob-token", pb.DeleteNoteRequest(id=created_id))
        print(f"DeleteNote    bob/viewer  -> {code.name:<18} {detail!r}")
        assert code == grpc.StatusCode.PERMISSION_DENIED
        assert created_id in NOTES, "a denied call must not change state"

        code, res = call(stub.DeleteNote, "alice-token", pb.DeleteNoteRequest(id=created_id))
        print(f"DeleteNote    alice/admin -> {code.name:<18} remaining={res.remaining}")
        assert code == grpc.StatusCode.OK and created_id not in NOTES

        # Idempotent: deleting it again is still OK, with the same end state.
        code, res = call(stub.DeleteNote, "alice-token", pb.DeleteNoteRequest(id=created_id))
        print(f"DeleteNote    again       -> {code.name:<18} remaining={res.remaining}  (idempotent)")
        assert code == grpc.StatusCode.OK and res.remaining == 1

    print("\nper call, in order: log -> recover -> authenticate -> authorize -> validate -> act")
    print("OK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        server, port = start_server(50051)
        print(f"listening on 127.0.0.1:{port}  (try grpcurl, or point level 12's client at it)")
        server.wait_for_termination()

    server, port = start_server()
    demo(port)
    server.stop(0).wait()
