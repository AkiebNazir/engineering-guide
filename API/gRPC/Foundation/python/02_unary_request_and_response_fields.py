"""
FOUNDATION LEVEL 02 - Real fields in, real fields out
=========================================================
REST's level 02 was "JSON in and out". This is the same lesson, and the point is
how little there is to do: the generated `CreateOrderRequest` and
`CreateOrderResponse` types ARE the JSON-in / JSON-out step. There is no
`json.loads`, no `json.dumps`, no "did they spell it gift_wrap or giftWrap",
no schema validation code to write for the SHAPE of the data.

WHAT REPLACED WHAT
  REST                                  gRPC
  ----------------------------------    -------------------------------------
  json.loads(body) -> dict              request is already a typed object
  body.get("quantity") may be None      request.quantity is always an int
  KeyError / TypeError at runtime       wrong field name = AttributeError here
  json.dumps(response_dict)             return a typed response message

You will learn
  * how .proto types map to Python: string->str, int32/int64->int, double->float,
    bool->bool, repeated->a list-like sequence
  * naming: `gift_wrap` in the .proto stays `gift_wrap` in Python but becomes
    `GiftWrap` in Go - the generator applies each language's convention for you
  * every field has a zero value and is never missing: unset string is "", unset
    int is 0, unset bool is False, unset repeated is []
  * SHAPE validation is free, but BUSINESS validation is still yours: protobuf
    guarantees quantity is an integer, never that it is positive (level 06)
  * messages are mutable objects, and `repeated` fields are appended to /
    extended, never assigned with `=`

Run it   python 02_unary_request_and_response_fields.py
"""
from concurrent import futures

import grpc

import orders_pb2 as pb
import orders_pb2_grpc as rpc

PRICES_CENTS = {"KEYB-01": 4999, "MOUSE-02": 1999}
GIFT_WRAP_CENTS = 350


class OrderServiceServicer(rpc.OrderServiceServicer):
    def CreateOrder(self, request: pb.CreateOrderRequest, context: grpc.ServicerContext) -> pb.CreateOrderResponse:
        # Every field is guaranteed to EXIST and to have the declared type. So
        # this handler never checks "is quantity present" or "is it a number" -
        # only whether the value makes business sense, which protobuf cannot know.
        print(f"  [server] sku={request.sku!r} quantity={request.quantity} "
              f"currency={request.currency!r} gift_wrap={request.gift_wrap}")

        unit = PRICES_CENTS.get(request.sku, 0)
        total = unit * request.quantity

        response = pb.CreateOrderResponse(
            order_id=f"ord-{request.sku.lower()}",
            total_cents=total,
            currency=request.currency or "EUR",  # "" is the zero value, so `or` gives us a default
        )
        # A `repeated` field is a sequence you append/extend - you cannot assign
        # to it with `=`. This is the one protobuf-Python quirk worth memorising.
        response.notes.append(f"{request.quantity} x {request.sku} @ {unit}c")
        if request.gift_wrap:
            response.total_cents += GIFT_WRAP_CENTS
            response.notes.append(f"gift wrap +{GIFT_WRAP_CENTS}c")
        return response


def demo(port: int) -> None:
    with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = rpc.OrderServiceStub(channel)

        # --- all fields set explicitly ---
        res = stub.CreateOrder(pb.CreateOrderRequest(
            sku="KEYB-01", quantity=2, currency="USD", gift_wrap=True), timeout=2)
        print(f"order_id    : {res.order_id!r}")
        print(f"total_cents : {res.total_cents}   (2 x 4999 + 350 gift wrap)")
        print(f"currency    : {res.currency!r}")
        print(f"notes       : {list(res.notes)}")
        assert res.total_cents == 2 * 4999 + GIFT_WRAP_CENTS
        assert res.currency == "USD"
        assert len(res.notes) == 2

        # --- only some fields set: the rest are zero values, never missing ---
        res = stub.CreateOrder(pb.CreateOrderRequest(sku="MOUSE-02", quantity=1), timeout=2)
        print(f"\nwith currency and gift_wrap left unset:")
        print(f"  currency defaulted by the SERVER to {res.currency!r} (it received \"\")")
        print(f"  gift_wrap arrived as False, so notes has {len(res.notes)} entry")
        assert res.currency == "EUR" and len(res.notes) == 1

    # --- the zero-value rule, proved on a locally built message ---
    empty = pb.CreateOrderRequest()
    print(f"\nan entirely empty CreateOrderRequest reads as:")
    print(f"  sku={empty.sku!r} quantity={empty.quantity} currency={empty.currency!r} gift_wrap={empty.gift_wrap}")
    assert (empty.sku, empty.quantity, empty.currency, empty.gift_wrap) == ("", 0, "", False)
    assert list(pb.CreateOrderResponse().notes) == []

    # Asking for a field the contract does not have fails immediately and loudly,
    # in YOUR code - not silently as a None three layers downstream.
    try:
        _ = empty.giftWrap  # camelCase: correct in Go/JSON, wrong in Python
        raise AssertionError("expected an AttributeError for a non-existent field")
    except AttributeError:
        print("  reading a field that is not in the .proto -> AttributeError, right here")

    print("OK")


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    demo(port)
    server.stop(0).wait()
