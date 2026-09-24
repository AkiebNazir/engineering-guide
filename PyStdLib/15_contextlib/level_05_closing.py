"""
LEVEL 05 (advanced) - closing(): for objects with .close() but no __exit__
==============================================================================
You will learn
  * some objects only expose .close(), not the full __enter__/__exit__ protocol
  * closing(obj) wraps ANY such object into a usable `with` context manager
  * it calls obj.close() on exit, exception or not -- nothing more, nothing less
  * unlike suppress(), closing() does NOT swallow exceptions raised in the block

Run: python level_05_closing.py
"""
from contextlib import closing


class LegacyConnection:
    """Simulates an old-style resource: it has a close() method, but was
    written before __enter__/__exit__ existed and never got them added."""
    def __init__(self, name: str):
        self.name = name
        self.closed = False

    def query(self, sql: str) -> str:
        if self.closed:
            raise RuntimeError("connection is closed")
        return f"result of {sql!r} on {self.name}"

    def close(self):
        self.closed = True


if __name__ == "__main__":
    # ---- LegacyConnection has NO __enter__/__exit__ at all -----------------
    conn = LegacyConnection("primary")
    assert not hasattr(conn, "__enter__")
    assert not hasattr(conn, "__exit__")

    # ---- closing() wraps it so `with` works anyway --------------------------
    with closing(LegacyConnection("primary")) as conn2:
        assert conn2.closed is False
        result = conn2.query("SELECT 1")
        assert result == "result of 'SELECT 1' on primary"
    assert conn2.closed is True         # close() was called automatically on exit

    # ---- close() runs even if the block raises ------------------------------
    conn3 = LegacyConnection("secondary")
    raised = None
    try:
        with closing(conn3):
            raise ValueError("query failed")
    except ValueError as e:
        raised = e
    assert raised is not None            # closing() does NOT suppress the exception
    assert conn3.closed is True           # but cleanup still ran

    # ---- confirms the connection is genuinely unusable after closing -------
    raised2 = None
    try:
        conn3.query("SELECT 2")
    except RuntimeError as e:
        raised2 = e
    assert raised2 is not None
    assert "connection is closed" in str(raised2)

    print("OK")
