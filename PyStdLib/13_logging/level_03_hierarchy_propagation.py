"""
LEVEL 03 (core) - getLogger(__name__) hierarchy and propagation
==================================================================
You will learn
  * logging.getLogger(name) builds a dotted hierarchy, mirroring package structure
  * getLogger(same_name) always returns the exact same Logger object
  * a record raised on a child logger propagates UP to every ancestor's handlers
  * a child's own effective level can differ from its parent's

Run: python level_03_hierarchy_propagation.py
"""
import io
import logging


if __name__ == "__main__":
    # ---- getLogger is a registry: same name -> same object ---------------
    a = logging.getLogger("myapp.orders")
    b = logging.getLogger("myapp.orders")
    assert a is b

    # ---- dotted names form a parent/child tree ----------------------------
    parent = logging.getLogger("myapp")
    child = logging.getLogger("myapp.orders")
    grandchild = logging.getLogger("myapp.orders.payment")
    assert child.parent is parent
    assert grandchild.parent is child

    # ---- clean slate for a repeatable demo --------------------------------
    for lg in (parent, child, grandchild):
        lg.handlers.clear()
        lg.setLevel(logging.NOTSET)
        lg.propagate = True

    # ---- a handler on the PARENT sees records from children too ----------
    parent_stream = io.StringIO()
    handler = logging.StreamHandler(parent_stream)
    handler.setFormatter(logging.Formatter("%(name)s:%(levelname)s:%(message)s"))
    parent.addHandler(handler)
    parent.setLevel(logging.INFO)

    grandchild.info("payment captured")   # emitted on the grandchild...
    output = parent_stream.getvalue()
    print("parent handler received:")
    print(output)
    # ...but PROPAGATED all the way up to the parent's handler
    assert "myapp.orders.payment:INFO:payment captured" in output

    # ---- effective level: NOTSET climbs the tree until it finds one ------
    assert child.level == logging.NOTSET               # child never set its own level
    assert child.getEffectiveLevel() == logging.INFO    # ...so it inherits the parent's
    assert grandchild.getEffectiveLevel() == logging.INFO

    # ---- a child can override its own level independently -----------------
    child.setLevel(logging.ERROR)
    assert child.getEffectiveLevel() == logging.ERROR
    # grandchild's own level is still NOTSET, so it climbs to its NEAREST ancestor
    # with an explicit level -- that's now `child` (ERROR), not the further `parent` (INFO)
    assert grandchild.getEffectiveLevel() == logging.ERROR
    parent_stream.truncate(0)
    parent_stream.seek(0)
    child.info("this is now below child's own ERROR threshold")
    assert parent_stream.getvalue() == ""    # filtered at the child, never even propagated

    # ---- disabling propagation stops the climb ----------------------------
    grandchild.propagate = False
    parent_stream.truncate(0)
    parent_stream.seek(0)
    grandchild.error("captured but should not reach the parent handler")
    assert parent_stream.getvalue() == ""    # nothing arrived: propagation was cut

    print("OK")
