"""
LEVEL 02 (basic) - functools.partial: pre-binding arguments
=============================================================
You will learn
  * how partial() freezes some positional and/or keyword arguments of a
    callable, producing a new, narrower callable
  * that partial fills positional slots left-to-right, and extra positional
    args at call time are appended after the ones already bound
  * partial as a cleaner alternative to a one-off lambda wrapper
  * inspecting a partial's frozen args via .func / .args / .keywords

Run: python level_02_partial.py
"""
from functools import partial


def power(base: float, exponent: float) -> float:
    return base ** exponent


def greet(greeting: str, name: str, punctuation: str = "!") -> str:
    return f"{greeting}, {name}{punctuation}"


def main() -> None:
    # --- binding a leading positional argument ----------------------------
    square = partial(power, exponent=2)  # base is left open
    cube = partial(power, exponent=3)
    assert square(4) == 16
    assert cube(2) == 8

    # --- partial vs an equivalent lambda: same behavior, clearer intent ---
    square_lambda = lambda base: power(base, exponent=2)
    assert square(5) == square_lambda(5) == 25

    # --- binding a keyword argument, leaving others open -------------------
    shout = partial(greet, punctuation="!!!")
    assert shout("Hello", "World") == "Hello, World!!!"

    # --- binding the FIRST positional argument freezes it in place --------
    # extra positional args supplied at call time fill the remaining slots
    # left to right -- this is the "binds positionally first" gotcha.
    hello = partial(greet, "Hello")
    assert hello("Ana") == "Hello, Ana!"
    assert hello("Ana", "?") == "Hello, Ana?"  # 2nd positional -> punctuation

    # --- introspecting a partial object ------------------------------------
    assert square.func is power
    assert square.args == ()
    assert square.keywords == {"exponent": 2}

    # --- a realistic use: pre-configuring a callback for map() -------------
    to_the_fourth = partial(power, exponent=4)
    assert list(map(to_the_fourth, [1, 2, 3])) == [1, 16, 81]

    # --- partials can stack: partial-of-a-partial keeps composing ---------
    hello_bang = partial(hello, punctuation=".")
    assert hello_bang("Zed") == "Hello, Zed."

    print("OK")


if __name__ == "__main__":
    main()
