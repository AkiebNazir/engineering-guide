"""
FOUNDATION LEVEL 11 - CAPSTONE: one complete, secured SOAP service
======================================================================
Nothing new here. Every idea from levels 00-10 - the envelope, headers, typed
parameters, nested responses, namespaces, Faults with detail, the HTTP status
convention, middleware, authentication and authorization - combined into one
small service with three operations and one deliberate access policy:

    GetStatus     public          anyone, no credentials at all
    CreateOrder   authenticated   any recognized caller (level 09)
    CancelOrder   admin only      role check on top (level 10)

This is deliberately the same shape as ../../labs/python/02_soap_server_and_wsdl.py:
once this feels easy, the labs (a real generated WSDL, real WS-Security
digests, SOAP 1.2, mustUnderstand, a JSON gateway over a legacy service) are
the very next step, not a jump.

You will learn
  * how ten small lessons compose into one real-looking, real-secured service
  * the deliberate order of a SOAP request's life: parse -> read headers ->
    authenticate -> authorize -> validate -> act -> build response
  * that a per-operation policy table beats an `if` inside every operation
  * that every error path in a SOAP service ends in exactly one place: a Fault

Run it        python 11_complete_soap_service.py
Keep serving  python 11_complete_soap_service.py --serve   (curl hint is printed on start)
"""
import sys
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
TNS = "http://foundation.example.com/orders"
ET.register_namespace("soap", SOAP)
ET.register_namespace("wsse", WSSE)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "wsse": WSSE, "t": TNS}

TOKENS = {
    "alice-token": {"user": "alice", "role": "admin"},
    "bob-token": {"user": "bob", "role": "viewer"},
}

# None = public. Otherwise: the roles allowed to call the operation.
POLICY: dict[str, set[str] | None] = {
    "GetStatus": None,
    "CreateOrder": {"viewer", "admin"},
    "CancelOrder": {"admin"},
}

ORDERS: dict[str, dict] = {}
STARTED_AT = time.time()


class Fault(Exception):
    """Every error path in the service ends here, and nowhere else."""

    def __init__(self, code: str, message: str, detail_name: str | None = None, **detail: str):
        super().__init__(message)
        self.code, self.message, self.detail_name, self.detail = code, message, detail_name, detail


@dataclass
class Request:
    envelope: ET.Element
    operation: str
    body: ET.Element
    caller: dict | None = None
    header: dict = field(default_factory=dict)


Dispatcher = Callable[[Request], tuple[int, bytes]]


# ------------------------------------------------------------ XML plumbing ----
def tag(name: str) -> str:
    return f"{{{TNS}}}{name}"


def build_envelope(body_child: ET.Element, header_children: list[ET.Element] | None = None) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    header = ET.SubElement(envelope, f"{{{SOAP}}}Header")
    for child in header_children or []:
        header.append(child)
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def build_fault(fault: Fault) -> ET.Element:
    element = ET.Element(f"{{{SOAP}}}Fault")
    ET.SubElement(element, "faultcode").text = fault.code
    ET.SubElement(element, "faultstring").text = fault.message
    if fault.detail_name:
        named = ET.SubElement(ET.SubElement(element, "detail"), tag(fault.detail_name))
        for key, value in fault.detail.items():
            ET.SubElement(named, tag(key)).text = str(value)
    return element


def required(element: ET.Element, name: str) -> str:
    value = element.findtext(f"t:{name}", default=None, namespaces=NS)
    if value is None or not value.strip():
        raise Fault("soap:Client", f"<{name}> is required", "MissingElement", element=name)
    return value.strip()


# --------------------------------------------------------------- operations ----
def get_status(request: Request) -> ET.Element:
    """Public: a health probe. No credential, so no caller to report."""
    response = ET.Element(tag("GetStatusResponse"))
    ET.SubElement(response, tag("status")).text = "UP"
    ET.SubElement(response, tag("orderCount")).text = str(len(ORDERS))
    ET.SubElement(response, tag("uptimeSeconds")).text = f"{time.time() - STARTED_AT:.0f}"
    return response


def create_order(request: Request) -> ET.Element:
    """Authenticated: validate (level 05), then answer with a nested structure
    (level 03) that records WHO placed the order (level 09)."""
    sku = required(request.body, "sku")
    quantity_text = required(request.body, "quantity")
    try:
        quantity = int(quantity_text)
    except ValueError:
        raise Fault("soap:Client", "quantity must be an integer",
                    "InvalidValue", element="quantity", got=quantity_text)
    if quantity < 1:
        raise Fault("soap:Client", "quantity must be at least 1",
                    "InvalidValue", element="quantity", got=quantity_text)
    try:
        unit_price = Decimal(request.body.findtext("t:unitPrice", default="10.00", namespaces=NS))
    except InvalidOperation:
        raise Fault("soap:Client", "unitPrice must be a decimal", "InvalidValue", element="unitPrice")

    order_id = f"ORD-{len(ORDERS) + 1:04d}"
    ORDERS[order_id] = {
        "sku": sku,
        "quantity": quantity,
        "total": unit_price * quantity,
        "state": "OPEN",
        "owner": request.caller["user"],
    }

    response = ET.Element(tag("CreateOrderResponse"))
    order = ET.SubElement(response, tag("order"))
    order.set("id", order_id)
    ET.SubElement(order, tag("state")).text = "OPEN"
    ET.SubElement(order, tag("owner")).text = request.caller["user"]
    ET.SubElement(order, tag("total")).text = f"{ORDERS[order_id]['total']:.2f}"
    return response


def cancel_order(request: Request) -> ET.Element:
    """Admin only: the role check already happened in the middleware, so this
    function only worries about business rules."""
    order_id = required(request.body, "orderId")
    order = ORDERS.get(order_id)
    if order is None:
        raise Fault("soap:Client", f"no such order: {order_id}", "OrderNotFound", orderId=order_id)
    if order["state"] == "CANCELLED":
        raise Fault("soap:Client", f"order {order_id} is already cancelled",
                    "IllegalState", orderId=order_id, state=order["state"])

    order["state"] = "CANCELLED"
    response = ET.Element(tag("CancelOrderResponse"))
    ET.SubElement(response, tag("orderId")).text = order_id
    ET.SubElement(response, tag("state")).text = "CANCELLED"
    ET.SubElement(response, tag("cancelledBy")).text = request.caller["user"]
    return response


OPERATIONS: dict[str, Callable[[Request], ET.Element]] = {
    "GetStatus": get_status,
    "CreateOrder": create_order,
    "CancelOrder": cancel_order,
}


# --------------------------------------------------------------- middleware ----
def with_logging(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        started = time.perf_counter()
        status, out = next_dispatch(request)
        code = ET.fromstring(out).findtext("soap:Body/soap:Fault/faultcode", namespaces=NS)
        print(f"  [log] {request.operation:<12} caller={request.header.get('caller', '-'):<10} "
              f"-> HTTP {status}{' ' + code if code else ''} ({(time.perf_counter() - started) * 1000:.2f}ms)")
        return status, out
    return wrapped


def with_recovery(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        try:
            return next_dispatch(request)
        except Fault as fault:
            # An EXPECTED failure: the operations raise these on purpose.
            return 500, build_envelope(build_fault(fault))
        except Exception as exc:
            # An UNEXPECTED one: a bug. Same clean XML out, nothing leaked.
            print(f"  [recovery] bug in {request.operation}: {exc!r}")
            return 500, build_envelope(build_fault(Fault("soap:Server", "internal error")))
    return wrapped


def with_authentication(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        if POLICY.get(request.operation) is None and request.operation in OPERATIONS:
            return next_dispatch(request)          # a public operation, no credential needed

        token = request.envelope.findtext(
            "soap:Header/wsse:Security/wsse:UsernameToken/wsse:Password", namespaces=NS)
        caller = TOKENS.get(token) if token else None
        if caller is None:
            raise Fault("soap:Client", "missing or invalid credentials", "Unauthenticated")

        request.caller = caller
        request.header["caller"] = caller["user"]
        return next_dispatch(request)
    return wrapped


def with_authorization(next_dispatch: Dispatcher) -> Dispatcher:
    def wrapped(request: Request) -> tuple[int, bytes]:
        allowed = POLICY.get(request.operation)
        if allowed is not None and request.caller["role"] not in allowed:
            raise Fault("soap:Client",
                        f"role '{request.caller['role']}' may not call {request.operation}",
                        "Forbidden", requiredRole=",".join(sorted(allowed)))
        return next_dispatch(request)
    return wrapped


def dispatch(request: Request) -> tuple[int, bytes]:
    operation = OPERATIONS.get(request.operation)
    if operation is None:
        raise Fault("soap:Client", f"unknown operation {request.operation}",
                    "UnknownOperation", operation=request.operation)
    return 200, build_envelope(operation(request))


# Outside in, and the order IS the design:
#   log everything -> convert any failure to a Fault -> identify -> permit -> act
pipeline: Dispatcher = with_logging(with_recovery(with_authentication(with_authorization(dispatch))))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/orders":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            envelope = ET.fromstring(raw)
            body = envelope.find("soap:Body", NS)
            if body is None or len(body) != 1:
                raise ValueError("expected exactly one element in soap:Body")
            operation_element = body[0]
            request = Request(envelope=envelope,
                              operation=operation_element.tag.split("}")[-1],
                              body=operation_element)
        except Exception:
            status = 500
            out = build_envelope(build_fault(Fault("soap:Client", "malformed SOAP request")))
        else:
            status, out = pipeline(request)

        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


# --------------------------------------------------------------------- demo ----
def call(url: str, operation: str, token: str | None = None, **params: str) -> tuple[int, ET.Element]:
    element = ET.Element(tag(operation))
    for name, value in params.items():
        ET.SubElement(element, tag(name)).text = str(value)

    headers = []
    if token:
        security = ET.Element(f"{{{WSSE}}}Security")
        username_token = ET.SubElement(security, f"{{{WSSE}}}UsernameToken")
        ET.SubElement(username_token, f"{{{WSSE}}}Password").text = token
        headers.append(security)

    request = urllib.request.Request(url, data=build_envelope(element, headers),
                                     headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, ET.fromstring(response.read())
    except urllib.error.HTTPError as e:
        return e.code, ET.fromstring(e.read())


def detail_of(envelope: ET.Element) -> str | None:
    detail = envelope.find("soap:Body/soap:Fault/detail", NS)
    return detail[0].tag.split("}")[-1] if detail is not None and len(detail) else None


def demo(url: str) -> None:
    print("== 1. GetStatus is public ==")
    status, envelope = call(url, "GetStatus")
    print(f"  -> {status} status={envelope.findtext('soap:Body/t:GetStatusResponse/t:status', namespaces=NS)}")
    assert status == 200

    print("\n== 2. CreateOrder needs a credential ==")
    status, envelope = call(url, "CreateOrder", sku="WIDGET-1", quantity="3")
    print(f"  anonymous        -> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "Unauthenticated"

    status, envelope = call(url, "CreateOrder", token="bob-token", sku="WIDGET-1", quantity="3", unitPrice="9.99")
    order = envelope.find("soap:Body/t:CreateOrderResponse/t:order", NS)
    print(f"  bob (viewer)     -> {status} id={order.get('id')} "
          f"owner={order.findtext('t:owner', namespaces=NS)} total={order.findtext('t:total', namespaces=NS)}")
    assert status == 200 and order.findtext("t:total", namespaces=NS) == "29.97"
    order_id = order.get("id")

    print("\n== 3. validation still applies to an authenticated caller ==")
    for label, params, expected in [
        ("missing sku", dict(quantity="1"), "MissingElement"),
        ("quantity='many'", dict(sku="X", quantity="many"), "InvalidValue"),
        ("quantity=0", dict(sku="X", quantity="0"), "InvalidValue"),
    ]:
        status, envelope = call(url, "CreateOrder", token="bob-token", **params)
        print(f"  {label:<16} -> {status} <{detail_of(envelope)}> "
              f"{envelope.findtext('soap:Body/soap:Fault/faultstring', namespaces=NS)!r}")
        assert detail_of(envelope) == expected

    print("\n== 4. CancelOrder is admin only ==")
    status, envelope = call(url, "CancelOrder", token="bob-token", orderId=order_id)
    print(f"  bob (viewer)     -> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "Forbidden"
    assert ORDERS[order_id]["state"] == "OPEN", "a refused call must change nothing"

    status, envelope = call(url, "CancelOrder", token="alice-token", orderId=order_id)
    print(f"  alice (admin)    -> {status} "
          f"state={envelope.findtext('soap:Body/t:CancelOrderResponse/t:state', namespaces=NS)} "
          f"by={envelope.findtext('soap:Body/t:CancelOrderResponse/t:cancelledBy', namespaces=NS)}")
    assert status == 200 and ORDERS[order_id]["state"] == "CANCELLED"

    print("\n== 5. business rules, unknown ids, unknown operations ==")
    status, envelope = call(url, "CancelOrder", token="alice-token", orderId=order_id)
    print(f"  cancel twice     -> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "IllegalState"

    status, envelope = call(url, "CancelOrder", token="alice-token", orderId="ORD-9999")
    print(f"  unknown order    -> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "OrderNotFound"

    status, envelope = call(url, "DropDatabase", token="alice-token")
    print(f"  unknown operation-> {status} <{detail_of(envelope)}>")
    assert detail_of(envelope) == "UnknownOperation"

    print("\n== 6. and the public operation still works, after all that ==")
    status, envelope = call(url, "GetStatus")
    count = envelope.findtext("soap:Body/t:GetStatusResponse/t:orderCount", namespaces=NS)
    print(f"  -> {status} orderCount={count}")
    assert status == 200 and count == "1"

    print("\nOK")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        print("listening on http://localhost:8080/orders - try:\n")
        print("  curl -s -X POST localhost:8080/orders -H 'Content-Type: text/xml' -d \\\n"
              f"    '<soap:Envelope xmlns:soap=\"{SOAP}\"><soap:Body>"
              f"<GetStatus xmlns=\"{TNS}\"/></soap:Body></soap:Envelope>'\n")
        print("  (CreateOrder/CancelOrder additionally need a wsse:Security header - see call() above)\n")
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/orders")
    server.shutdown()
