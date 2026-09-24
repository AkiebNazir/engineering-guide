"""
FOUNDATION LEVEL 03 - Response structures: nesting, and the array that isn't
================================================================================
Levels 00-02 answered with one or two flat values. Real operations answer with
a STRUCTURE: an order with a customer inside it and a list of lines inside
that. XML expresses nesting by nesting elements, which is easy - but it has no
array type at all, which trips up everyone arriving from JSON.

JSON says `"items": [{...},{...}]`. XML says: repeat the element.

    <items>              <- a wrapper element, by convention
      <item>...</item>   <- the "array" is just <item> appearing twice
      <item>...</item>
    </items>

So "is this a list or a single value?" is not visible in the XML at all - it
lives in the contract (the WSDL's maxOccurs). A one-element list and a single
value look IDENTICAL on the wire. That is the single most common source of
"the client library gave me a dict instead of a list" bugs.

You will learn
  * building a nested response tree with ET.SubElement, parent by parent
  * that repetition IS the array: findall() vs find() on the client side
  * why a wrapper element (<items>) around repeated children is the convention
  * that a list of length one is indistinguishable from a scalar on the wire
  * reading a nested response back out without ever guessing at positions

Run it   python 03_response_structures.py
"""
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
TNS = "http://foundation.example.com/soap"
ET.register_namespace("soap", SOAP)
ET.register_namespace("t", TNS)
NS = {"soap": SOAP, "t": TNS}

ORDERS = {
    "ORD-1": {
        "customer": {"name": "Ada Lovelace", "country": "GB"},
        "items": [
            {"sku": "WIDGET-1", "qty": 2, "price": "9.99"},
            {"sku": "GIZMO-7", "qty": 1, "price": "24.50"},
        ],
    },
    "ORD-2": {
        "customer": {"name": "Alan Turing", "country": "GB"},
        # Deliberately ONE item: on the wire this looks exactly like a single
        # value, which is why clients need the contract to know it is a list.
        "items": [{"sku": "WIDGET-1", "qty": 1, "price": "9.99"}],
    },
}


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def tag(name: str) -> str:
    return f"{{{TNS}}}{name}"


def build_order_response(order_id: str, order: dict) -> ET.Element:
    """Build the nested tree top-down. Each SubElement call adds one level."""
    response = ET.Element(tag("GetOrderResponse"))
    order_el = ET.SubElement(response, tag("order"))

    # An ATTRIBUTE instead of a child element. Both are legal; the rule of
    # thumb is attributes for identity/metadata, elements for data.
    order_el.set("id", order_id)

    # ---- a nested single object ----
    customer_el = ET.SubElement(order_el, tag("customer"))
    ET.SubElement(customer_el, tag("name")).text = order["customer"]["name"]
    ET.SubElement(customer_el, tag("country")).text = order["customer"]["country"]

    # ---- the "array": a wrapper, then one child per element ----
    items_el = ET.SubElement(order_el, tag("items"))
    total = 0.0
    for item in order["items"]:
        item_el = ET.SubElement(items_el, tag("item"))
        ET.SubElement(item_el, tag("sku")).text = item["sku"]
        ET.SubElement(item_el, tag("qty")).text = str(item["qty"])
        ET.SubElement(item_el, tag("price")).text = item["price"]
        total += item["qty"] * float(item["price"])

    ET.SubElement(order_el, tag("total")).text = f"{total:.2f}"
    return response


def dispatch(raw: bytes) -> tuple[int, bytes]:
    operation = ET.fromstring(raw).find("soap:Body", NS)[0]
    if operation.tag != tag("GetOrder"):
        return 400, b"unknown operation"
    order_id = operation.findtext("t:orderId", default="", namespaces=NS)
    if order_id not in ORDERS:
        return 400, b"unknown order"
    return 200, build_envelope(build_order_response(order_id, ORDERS[order_id]))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        status, out = dispatch(self.rfile.read(length))
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


def get_order(url: str, order_id: str) -> tuple[int, bytes]:
    operation = ET.Element(tag("GetOrder"))
    ET.SubElement(operation, tag("orderId")).text = order_id
    request = urllib.request.Request(url, data=build_envelope(operation),
                                     headers={"Content-Type": "text/xml; charset=utf-8"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def parse_order(raw: bytes) -> dict:
    """The client's job: walk the tree, never guess at child positions."""
    order = ET.fromstring(raw).find("soap:Body/t:GetOrderResponse/t:order", NS)
    return {
        "id": order.get("id"),  # .get() reads an ATTRIBUTE, .find() a child element
        "customer": {
            "name": order.findtext("t:customer/t:name", namespaces=NS),
            "country": order.findtext("t:customer/t:country", namespaces=NS),
        },
        # findall() is the "give me the array" call. find() would silently give
        # you only the FIRST item - the classic quiet data-loss bug here.
        "items": [
            {
                "sku": item.findtext("t:sku", namespaces=NS),
                "qty": int(item.findtext("t:qty", namespaces=NS)),
            }
            for item in order.findall("t:items/t:item", NS)
        ],
        "total": order.findtext("t:total", namespaces=NS),
    }


def demo(url: str) -> None:
    print("== 1. a nested response, as raw XML ==")
    status, raw = get_order(url, "ORD-1")
    print(raw.decode().replace("><", ">\n<"))
    assert status == 200

    print("\n== 2. the same response, parsed into Python ==")
    order = parse_order(raw)
    print(f"  {order}")
    assert order["id"] == "ORD-1"
    assert order["customer"]["name"] == "Ada Lovelace"
    assert len(order["items"]) == 2
    assert order["total"] == "44.48"

    print("\n== 3. a ONE-item list looks exactly like a scalar on the wire ==")
    status, raw = get_order(url, "ORD-2")
    one = parse_order(raw)
    print(f"  items: {one['items']}   (findall gave a list of 1; find would have hidden that)")
    assert len(one["items"]) == 1
    # Proof of the trap: the naive "just take the child" reading of an array.
    naive = ET.fromstring(raw).find("soap:Body/t:GetOrderResponse/t:order/t:items/t:item", NS)
    print(f"  naive find() -> a single <item> element ({naive.findtext('t:sku', namespaces=NS)}), "
          "which is why you need the contract to know it is a list")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
