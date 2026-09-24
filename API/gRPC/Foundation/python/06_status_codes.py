"""
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
  * `context.abort(code, message)` RAISES - nothing after it in the handler runs
  * the client always catches `grpc.RpcError` and branches on `.code()`, which is
    a `grpc.StatusCode` enum, never a string or an integer you hardcode
  * UNAUTHENTICATED vs PERMISSION_DENIED is the 401-vs-403 distinction, and
    confusing them is the single most common gRPC API design mistake
  * returning a plain Python exception from a handler becomes UNKNOWN, which
    tells the caller nothing - always abort with a real code instead
  * which codes are safe to retry (UNAVAILABLE, RESOURCE_EXHAUSTED) and which
    never are (INVALID_ARGUMENT, NOT_FOUND, PERMISSION_DENIED) - see level 12

Run it   python 06_status_codes.py
"""
from concurrent import futures

import grpc

import statuses_pb2 as pb
import statuses_pb2_grpc as rpc

SECRETS = {"launch-codes": "0000", "wifi": "hunter2"}
VALID_TOKEN = "s3cret-token"

# The token and role travel in REQUEST FIELDS here on purpose. Real services put
# credentials in metadata and check them in an interceptor - that is levels
# 07/09/10. This level is ONLY about choosing the right status code.


class VaultServicer(rpc.VaultServicer):
    def GetSecret(self, request: pb.GetSecretRequest, context: grpc.ServicerContext) -> pb.Secret:
        # Order matters, and it is always this order. Each check answers a
        # different question, and a later check would leak information if it ran
        # before an earlier one (telling an anonymous caller that a secret
        # exists is itself a leak).

        # 1. Is the request even well-formed? -> INVALID_ARGUMENT (REST 400)
        if not request.id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id must not be empty")

        # 2. Do we know who this is at all? -> UNAUTHENTICATED (REST 401)
        if request.token != VALID_TOKEN:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "missing or invalid token")

        # 3. We know who they are - are they allowed? -> PERMISSION_DENIED (403)
        if request.id == "launch-codes" and request.role != "admin":
            context.abort(grpc.StatusCode.PERMISSION_DENIED,
                          f"role {request.role!r} may not read the launch codes")

        # 4. Allowed, but does the thing exist? -> NOT_FOUND (REST 404)
        value = SECRETS.get(request.id)
        if value is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"no secret named {request.id!r}")

        # 5. Everything checked out. Returning normally means status OK.
        return pb.Secret(id=request.id, value=value)


def call(stub, **kwargs) -> tuple[grpc.StatusCode, str]:
    """Returns (code, message) for any outcome, success or failure, so the demo
    below can print them side by side."""
    try:
        res = stub.GetSecret(pb.GetSecretRequest(**kwargs), timeout=2)
        return grpc.StatusCode.OK, res.value
    except grpc.RpcError as e:
        # `.code()` is the machine-readable part you branch on.
        # `.details()` is the human-readable message, for logs and humans only.
        return e.code(), e.details()


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.VaultStub(channel)

        cases = [
            ("well-formed, authorised, exists", dict(id="wifi", token=VALID_TOKEN, role="viewer"),
             grpc.StatusCode.OK),
            ("empty id", dict(id="", token=VALID_TOKEN, role="viewer"),
             grpc.StatusCode.INVALID_ARGUMENT),
            ("no token at all", dict(id="wifi"),
             grpc.StatusCode.UNAUTHENTICATED),
            ("known caller, wrong role", dict(id="launch-codes", token=VALID_TOKEN, role="viewer"),
             grpc.StatusCode.PERMISSION_DENIED),
            ("authorised, no such secret", dict(id="nope", token=VALID_TOKEN, role="admin"),
             grpc.StatusCode.NOT_FOUND),
        ]
        for label, kwargs, expected in cases:
            code, detail = call(stub, **kwargs)
            print(f"{label:<32} -> {code.name:<18} {detail!r}")
            assert code == expected, f"{label}: expected {expected}, got {code}"

        # UNIMPLEMENTED is the distinction REST cannot make: the method itself
        # does not exist, as opposed to the data not existing (NOT_FOUND above).
        missing = channel.unary_unary(
            "/foundation.statuses.v1.Vault/DeleteSecret",
            request_serializer=pb.GetSecretRequest.SerializeToString,
            response_deserializer=pb.Secret.FromString,
        )
        try:
            missing(pb.GetSecretRequest(id="wifi"), timeout=2)
            raise AssertionError("expected UNIMPLEMENTED")
        except grpc.RpcError as e:
            print(f"{'no such method':<32} -> {e.code().name:<18} (REST would also say 404 here)")
            assert e.code() == grpc.StatusCode.UNIMPLEMENTED

    print("\nretry policy is a PROPERTY of the status code (see level 12):")
    for code, retryable in [("OK", "-"),
                            ("INVALID_ARGUMENT", "never - the request itself is wrong"),
                            ("UNAUTHENTICATED", "never - fix the credential first"),
                            ("PERMISSION_DENIED", "never - the answer will not change"),
                            ("NOT_FOUND", "never - it still will not exist"),
                            ("RESOURCE_EXHAUSTED", "yes, with backoff"),
                            ("UNAVAILABLE", "yes, with backoff"),
                            ("DEADLINE_EXCEEDED", "only if the call is idempotent"),
                            ("INTERNAL", "no - it is a bug, retrying hides it")]:
        print(f"  {code:<20} {retryable}")

    print("\nOK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_VaultServicer_to_server(VaultServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
