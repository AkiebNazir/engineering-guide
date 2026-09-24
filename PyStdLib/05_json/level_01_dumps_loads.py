"""
LEVEL 01 (basic) - json.dumps() / json.loads(): the round trip
=================================================================
You will learn
  * dumps() turns a Python value into a JSON string
  * loads() turns a JSON string back into a Python value
  * which Python types map onto which JSON types (and which don't survive intact)

Run: python level_01_dumps_loads.py
"""
import json


def main() -> None:
    data = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "nickname": None,
        "scores": [10, 9.5, 8],
    }

    text = json.dumps(data)
    assert isinstance(text, str)
    assert text == '{"name": "Ada", "age": 36, "active": true, "nickname": null, "scores": [10, 9.5, 8]}'

    back = json.loads(text)
    assert back == data                 # values round-trip exactly...
    assert back is not data             # ...but it's a brand new object

    # Python True/False/None map to JSON true/false/null -- lowercase, no exceptions.
    assert json.dumps(True) == "true"
    assert json.dumps(None) == "null"

    # tuples encode as JSON arrays, but decode back as lists -- the tuple-ness is lost.
    assert json.dumps((1, 2, 3)) == "[1, 2, 3]"
    assert json.loads(json.dumps((1, 2, 3))) == [1, 2, 3]

    # JSON has no int/float distinction issue here: whole numbers stay ints.
    assert json.loads("42") == 42 and isinstance(json.loads("42"), int)
    assert json.loads("42.0") == 42.0 and isinstance(json.loads("42.0"), float)

    print("OK")


if __name__ == "__main__":
    main()
