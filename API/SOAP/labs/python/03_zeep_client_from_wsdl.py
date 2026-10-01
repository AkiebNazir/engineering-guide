"""
LAB 03 (advanced) - A WSDL-driven client with zeep: generated types, validation, faults, timeouts
================================================================================================
Writing envelopes by hand (lab 01) does not scale to a WSDL with 200 operations. The industry answer:
point a library at the WSDL and call operations like Python methods. zeep is the maintained library.

You will learn
  * client = Client(wsdl_url); client.service.GetBalance(accountId="...")   - types come from the WSDL
  * decimals arrive as decimal.Decimal, and the STRUCTURE of your input is validated CLIENT-SIDE against
    the schema before anything is sent (missing required element, unknown argument). Scalar VALUES are
    only loosely checked, so the server must still validate (lab 02 does) - never rely on the client.
  * seeing the real XML: HistoryPlugin (what was sent/received) and client.create_message(...)
  * faults become exceptions: zeep.exceptions.Fault with .code, .message and a parsed .detail
    -> catch InsufficientFunds by name
  * timeouts: Transport(timeout=..., operation_timeout=...) - the default is NO timeout. Always set both.
  * the classic production fix: the WSDL advertises an internal hostname; override the endpoint
    with client.create_service(binding, address)
  * reading a WSDL: client.wsdl.dump()

This lab reuses the server from lab 02 (imported by file path).

Needs   pip install zeep
Run it  python 03_zeep_client_from_wsdl.py
"""
import importlib.util
import logging
import pathlib
import time
from decimal import Decimal
from unittest import mock

import zeep
import zeep.exceptions
from lxml import etree
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

logging.getLogger("zeep").setLevel(logging.ERROR)

# --- reuse lab 02's server ---------------------------------------------------------
spec = importlib.util.spec_from_file_location("lab02", pathlib.Path(__file__).with_name("02_soap_server_and_wsdl.py"))
lab02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab02)


def pretty(el) -> str:
    return etree.tostring(el, pretty_print=True).decode().rstrip()


if __name__ == "__main__":
    srv = lab02.start()
    base = f"http://127.0.0.1:{srv.server_port}/bank"
    history = HistoryPlugin()
    client = zeep.Client(base + "?wsdl", plugins=[history],
                         transport=Transport(timeout=5, operation_timeout=5))       # connect timeout + read timeout

    print("== 1. what zeep learned from the WSDL ==")
    ops = client.wsdl.services["BankService"].ports["BankPort"].binding._operations
    for name, op in ops.items():
        print(f"  {name}: input = {op.input.signature()}   output = {op.output.signature()}")

    print("\n== 2. calling operations like Python methods ==")
    result = client.service.GetBalance(accountId="ACC-1001")
    print("  GetBalance ->", result.balance, type(result.balance).__name__, result.currency)
    assert isinstance(result.balance, Decimal) and result.balance == Decimal("1042.50")

    print("\n== 3. the XML that actually went over the wire ==")
    print(pretty(history.last_sent["envelope"]))
    print(pretty(history.last_received["envelope"]))
    print("\n== 3b. build a message WITHOUT sending it (great for tests and debugging) ==")
    msg = client.create_message(client.service, "Transfer", fromAccount="ACC-1001", toAccount="ACC-2002", amount=Decimal("10.00"))
    print(pretty(msg))

    print("\n== 4. client-side validation of the message STRUCTURE ==")
    sent_before = len(history._buffer)
    for label, kwargs in [("missing element", dict(fromAccount="ACC-1001", toAccount="ACC-2002")),
                          ("unknown argument", dict(fromAccount="ACC-1001", toAccount="ACC-2002", amount=Decimal(1), bogus=1))]:
        try:
            client.service.Transfer(**kwargs)
            raise AssertionError(label)
        except (zeep.exceptions.ValidationError, TypeError) as e:
            print(f"  {label:<17} -> {type(e).__name__}: {str(e)[:66]}")
    assert len(history._buffer) == sent_before, "nothing should have been sent"
    print("  (0 requests were sent for these two calls)")
    try:
        client.service.Transfer(fromAccount="ACC-1001", toAccount="ACC-2002", amount="abc")
    except zeep.exceptions.Fault as e:
        print(f"  but amount='abc' is only checked loosely by the client -> the SERVER rejected it: {e.message!r}")
    print("  => validate on the server, always; client-side checks are a convenience.")
    print("\n== 5. faults are exceptions with parsed details ==")
    try:
        client.service.Transfer(fromAccount="ACC-2002", toAccount="ACC-1001", amount=Decimal("99999"))
    except zeep.exceptions.Fault as fault:
        detail = fault.detail[0]                                        # <InsufficientFunds> element
        name = etree.QName(detail).localname
        fields = {etree.QName(c).localname: c.text for c in detail}
        print(f"  Fault code={fault.code!r} message={fault.message!r}")
        print(f"  detail element <{name}> {fields}")
        assert name == "InsufficientFunds" and Decimal(fields["requested"]) == Decimal("99999")
        print(f"  -> the app can say: 'You have {fields['available']}, you asked for {fields['requested']}'")

    print("\n== 6. timeouts: the DEFAULT is to wait forever ==")
    slow_client = zeep.Client(base + "?wsdl", transport=Transport(timeout=5, operation_timeout=0.3))
    with mock.patch.dict(lab02.OPERATIONS["GetBalance"].__dict__, {"handler": lambda accountId: (time.sleep(1.0), {"balance": "1", "currency": "EUR"})[1]}):
        t = time.perf_counter()
        try:
            slow_client.service.GetBalance(accountId="ACC-1001")
        except Exception as e:
            print(f"  gave up after {time.perf_counter() - t:.2f}s with {type(e).__name__} (operation_timeout=0.3s)")
            assert time.perf_counter() - t < 0.9
    print("  Enterprise SOAP backends are often SLOW; without operation_timeout one hung call pins a thread forever.")

    print("\n== 7. the WSDL says one address, reality says another: override the endpoint ==")
    binding = "{http://bank.example.com/ws}BankBinding"
    proxy = client.create_service(binding, base)                            # e.g. WSDL advertised http://internal-host:9000/...
    print("  balance via overridden endpoint:", proxy.GetBalance(accountId="ACC-2002").balance)
    print("\nOK")
    srv.shutdown()
