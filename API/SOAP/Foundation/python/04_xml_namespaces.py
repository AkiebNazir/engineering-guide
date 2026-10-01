"""
FOUNDATION LEVEL 04 - XML namespaces: why every tag has two halves
======================================================================
Every level so far wrote tags like `{http://foundation.example.com/soap}symbol`
and you took it on faith. Here is the why: an XML document can mix vocabularies
from different authors, and two authors will absolutely both use the tag
`<Amount>`. A NAMESPACE is a globally unique string (usually a URL that nobody
ever fetches) that says which vocabulary a tag belongs to.

    <t:Amount xmlns:t="http://orders.example.com">   "Amount, the orders one"
    <s:Amount xmlns:s="http://shipping.example.com"> "Amount, the shipping one"

The PREFIX (`t:`, `s:`) is throwaway shorthand chosen per document; the
namespace URI it maps to is the real identity. Two documents using different
prefixes for the same URI are the SAME document as far as any parser cares.

THE CLASSIC BUG, demonstrated below: matching a tag by its local name only
("does it end in Amount?") happily matches the wrong vocabulary's element. It
works perfectly on your test message and corrupts data in production the day
someone adds a second namespace.

You will learn
  * what a namespace is, and that the prefix is NOT part of the identity
  * how ElementTree spells a qualified name: "{namespace}localname"
  * matching by qualified name (correct) vs by local name (the classic bug)
  * that re-prefixing a document changes nothing about its meaning
  * the default namespace (xmlns="...") and why it makes prefix-matching worse

Run it   python 04_xml_namespaces.py
"""
import threading
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
ORDERS = "http://orders.example.com"       # our own operation vocabulary
SHIPPING = "http://shipping.example.com"   # a DIFFERENT team's vocabulary
ET.register_namespace("soap", SOAP)
ET.register_namespace("o", ORDERS)
ET.register_namespace("s", SHIPPING)
NS = {"soap": SOAP, "o": ORDERS, "s": SHIPPING}


def build_envelope(body_child: ET.Element) -> bytes:
    envelope = ET.Element(f"{{{SOAP}}}Envelope")
    ET.SubElement(envelope, f"{{{SOAP}}}Header")
    ET.SubElement(envelope, f"{{{SOAP}}}Body").append(body_child)
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


# The request we will send carries TWO elements whose local name is "Amount":
# the goods total (ours) and the shipping surcharge (the shipping team's).
# Only the namespace tells them apart.
REQUEST_BODY = (
    f'<o:PriceOrder xmlns:o="{ORDERS}" xmlns:s="{SHIPPING}">'
    "<o:Amount>100.00</o:Amount>"
    "<s:Amount>7.50</s:Amount>"
    "</o:PriceOrder>"
)


def dispatch(raw: bytes) -> tuple[int, bytes]:
    operation = ET.fromstring(raw).find("soap:Body", NS)[0]
    if operation.tag != f"{{{ORDERS}}}PriceOrder":
        return 400, b"unknown operation"

    # ---- THE CORRECT WAY: match the qualified name ----
    goods = float(operation.findtext("o:Amount", namespaces=NS))
    shipping = float(operation.findtext("s:Amount", namespaces=NS))

    # ---- THE BUG, for comparison: "any child whose name ends in Amount" ----
    # This is what you write when you strip namespaces to "keep things simple".
    # It finds two elements it believes are the same thing and takes the first.
    naive = [el for el in operation if el.tag.split("}")[-1] == "Amount"]
    print(f"  [server] correct match : goods={goods} shipping={shipping}")
    print(f"  [server] naive  match  : {len(naive)} element(s) called 'Amount', "
          f"first = {naive[0].text} - the bug silently takes the goods amount as the total")

    response = ET.Element(f"{{{ORDERS}}}PriceOrderResponse")
    ET.SubElement(response, f"{{{ORDERS}}}Total").text = f"{goods + shipping:.2f}"
    return 200, build_envelope(response)


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


def post(url: str, raw: bytes) -> bytes:
    request = urllib.request.Request(url, data=raw, headers={"Content-Type": "text/xml; charset=utf-8"})
    with urllib.request.urlopen(request) as response:
        return response.read()


def demo(url: str) -> None:
    print("== 1. two elements, same local name, different namespaces ==")
    print(f"  {REQUEST_BODY}")
    raw = post(url, build_envelope(ET.fromstring(REQUEST_BODY)))
    total = ET.fromstring(raw).findtext("soap:Body/o:PriceOrderResponse/o:Total", namespaces=NS)
    print(f"  total -> {total}   (100.00 goods + 7.50 shipping)")
    assert total == "107.50"

    print("\n== 2. the prefix is throwaway: DIFFERENT prefixes, identical meaning ==")
    # Same namespaces, renamed prefixes, and the goods amount uses the DEFAULT
    # namespace (no prefix at all). A parser sees the exact same document.
    reprefixed = (
        f'<PriceOrder xmlns="{ORDERS}" xmlns:ship="{SHIPPING}">'
        "<Amount>100.00</Amount>"
        "<ship:Amount>7.50</ship:Amount>"
        "</PriceOrder>"
    )
    print(f"  {reprefixed}")
    raw = post(url, build_envelope(ET.fromstring(reprefixed)))
    total_again = ET.fromstring(raw).findtext("soap:Body/o:PriceOrderResponse/o:Total", namespaces=NS)
    print(f"  total -> {total_again}   (same answer: prefixes carry no meaning)")
    assert total_again == total

    print("\n== 3. proof that matching on the prefix or local name is not enough ==")
    parsed = ET.fromstring(reprefixed)
    tags = [el.tag for el in parsed]
    print(f"  qualified tags as the parser sees them:\n    {tags[0]}\n    {tags[1]}")
    # Both children are literally called "Amount"; only the {namespace} differs.
    assert tags[0].split("}")[-1] == tags[1].split("}")[-1] == "Amount"
    assert tags[0] != tags[1]
    assert parsed.find("o:Amount", NS).text == "100.00"
    assert parsed.find("s:Amount", NS).text == "7.50"
    print("  -> ALWAYS match {namespace}localname. Never strip namespaces 'for simplicity'.")

    print("\nOK")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    demo(f"http://127.0.0.1:{server.server_port}/soap")
    server.shutdown()
