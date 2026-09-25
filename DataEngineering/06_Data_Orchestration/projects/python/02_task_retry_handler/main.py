import time
import random
from functools import wraps

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        print(f"Attempt {x+1} failed. Max retries reached.")
                        raise e
                    sleep_time = (backoff_in_seconds * 2 ** x) + random.uniform(0, 1)
                    print(f"Attempt {x+1} failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    x += 1
        return wrapper
    return decorator

@retry_with_backoff(retries=3, backoff_in_seconds=1)
def flaky_task():
    if random.random() < 0.7:
        raise ValueError("Random failure occurred")
    print("Task succeeded!")
    return True

if __name__ == "__main__":
    try:
        flaky_task()
    except Exception as e:
        print(f"Task ultimately failed: {e}")
