# Exercise 2: Post-Deployment Smoke Test 💨

## 🎯 Objective
Write a Python script that acts as a post-deployment smoke test, verifying that a newly deployed service is healthy.

## 📋 Prerequisites
- Python 3 installed
- Standard libraries only (`urllib`)

## 📝 Instructions
1. Create a file named `smoke_test.py`.
2. The script should take a URL as a command-line argument.
3. It should make an HTTP GET request to the URL.
4. If the response status is 200, print success and exit with code `0`.
5. If the response status is anything else, or if the connection fails, print failure and exit with code `1`.

## 💡 Hints
- Use `sys.argv[1]` to get the URL argument.
- Use `urllib.request.urlopen` for standard library HTTP requests.
- Use `sys.exit(0)` for success and `sys.exit(1)` for failure.

## ✅ Expected Output / Solution

```python
# smoke_test.py
import sys
import urllib.request
from urllib.error import URLError, HTTPError

def run_smoke_test(url):
    print(f"Running smoke test against: {url}")
    try:
        response = urllib.request.urlopen(url, timeout=5)
        if response.getcode() == 200:
            print("✅ Smoke test passed! Service is healthy.")
            sys.exit(0)
        else:
            print(f"❌ Smoke test failed! Status code: {response.getcode()}")
            sys.exit(1)
            
    except HTTPError as e:
        print(f"❌ Smoke test failed! HTTP Error: {e.code}")
        sys.exit(1)
    except URLError as e:
        print(f"❌ Smoke test failed! Connection Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Smoke test failed! Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    run_smoke_test(target_url)
```

## 🧠 Key Takeaway
Smoke tests are critical gates in Continuous Delivery. By running this immediately after a deployment step, your pipeline can automatically detect catastrophic failures and trigger an automatic rollback before users are severely impacted.
