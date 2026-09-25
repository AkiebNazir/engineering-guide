# Exercise 02: Python Pytest Fixtures and Parametrize 🟢

## 🎯 Objective
Learn how to use Python's `pytest` framework, utilizing fixtures for setup and `@pytest.mark.parametrize` for data-driven testing.

## 📋 Prerequisites
- Python installed.
- Install pytest: `pip install pytest`

## 📝 Instructions

1. Create a file named `string_utils.py` containing a class that processes strings.
2. Create a test file `test_string_utils.py`.
3. Use a `pytest` fixture to provide a reusable instance of the class.
4. Use `parametrize` to test multiple string inputs.

### Step 1: Write the Code
Create `string_utils.py`:

```python
class StringProcessor:
    def __init__(self, prefix=""):
        self.prefix = prefix
        
    def format_string(self, text):
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if not text:
            return ""
        return f"{self.prefix}{text.strip().upper()}"
```

### Step 2: Write the Test
Create `test_string_utils.py`:

```python
import pytest
from string_utils import StringProcessor

# 1. Define a fixture that provides a configured instance for our tests
@pytest.fixture
def processor():
    # Setup: Create instance with a specific prefix
    return StringProcessor(prefix="ID-")

# 2. Use the fixture in a basic test
def test_format_empty_string(processor):
    assert processor.format_string("   ") == ""

# 3. Use parametrize for table-driven testing
@pytest.mark.parametrize("input_text, expected", [
    ("hello", "ID-HELLO"),
    ("  world  ", "ID-WORLD"),
    ("PYTHON", "ID-PYTHON"),
])
def test_format_valid_strings(processor, input_text, expected):
    assert processor.format_string(input_text) == expected

# 4. Test exceptions
def test_format_invalid_type(processor):
    with pytest.raises(TypeError, match="Input must be a string"):
        processor.format_string(123)
```

### Step 3: Run the tests
Run pytest with verbose output:
```bash
pytest -v test_string_utils.py
```

## 💡 Hints
- Fixtures are injected automatically into test functions simply by adding the fixture's name as an argument.
- `pytest.raises` is a context manager used to cleanly verify that exceptions are thrown.

## ✅ Expected Output
```
============================= test session starts ==============================
collected 5 items                                                              

test_string_utils.py::test_format_empty_string PASSED                    [ 20%]
test_string_utils.py::test_format_valid_strings[hello-ID-HELLO] PASSED   [ 40%]
test_string_utils.py::test_format_valid_strings[  world  -ID-WORLD] PASSED [ 60%]
test_string_utils.py::test_format_valid_strings[PYTHON-ID-PYTHON] PASSED [ 80%]
test_string_utils.py::test_format_invalid_type PASSED                    [100%]

============================== 5 passed in 0.02s ===============================
```

## 🧠 Key Takeaway
Pytest fixtures separate setup code from test logic, promoting reusability. `parametrize` offers the same benefits as Go's table-driven tests, keeping test suites concise and comprehensive.
