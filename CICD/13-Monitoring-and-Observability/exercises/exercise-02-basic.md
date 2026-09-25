# Exercise 2: Structured Logging 📝

## 🎯 Objective
Implement structured JSON logging in an application so logs can be easily parsed by observability tools.

## 📋 Prerequisites
- Python 3.9+ installed

## 📝 Instructions

Unstructured logs like `print("User logged in")` are hard for machines to search. Structured logs in JSON format solve this.

### Step 1: Create a Python Application
Create a file named `app.py`.

```python
import logging
import json
import time
import random
import uuid

class StructuredJSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        
        # Add any extra fields passed in
        if hasattr(record, 'extra_context'):
            log_record.update(record.extra_context)
            
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger():
    logger = logging.getLogger("payment_service")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(handler)
    
    return logger

def process_payment(logger, user_id, amount):
    trace_id = str(uuid.uuid4())
    context = {"user_id": user_id, "amount": amount, "trace_id": trace_id}
    
    logger.info("Starting payment processing", extra={"extra_context": context})
    time.sleep(0.5)
    
    if random.random() < 0.2:
        try:
            raise ValueError("Insufficient funds")
        except Exception as e:
            logger.error("Payment failed", extra={"extra_context": context}, exc_info=True)
            return False
            
    logger.info("Payment successful", extra={"extra_context": context})
    return True

if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Service started", extra={"extra_context": {"version": "1.0.0"}})
    
    for i in range(3):
        process_payment(logger, f"user_{i}", random.randint(10, 100))
```

### Step 2: Run and Observe
Run the application: `python app.py`

## 💡 Hints
- Notice how we pass `extra={"extra_context": context}`. This allows us to append contextual data like `trace_id` and `user_id` to the JSON payload.
- Log aggregators like Datadog or ELK (Elasticsearch, Logstash, Kibana) can automatically index every key in this JSON.

## ✅ Expected Output / Solution
```json
{"timestamp": "2023-10-25 10:15:22,123", "level": "INFO", "message": "Service started", "module": "app", "funcName": "<module>", "version": "1.0.0"}
{"timestamp": "2023-10-25 10:15:22,124", "level": "INFO", "message": "Starting payment processing", "module": "app", "funcName": "process_payment", "user_id": "user_0", "amount": 42, "trace_id": "123e4567-e89b-12d3-a456-426614174000"}
{"timestamp": "2023-10-25 10:15:22,625", "level": "INFO", "message": "Payment successful", "module": "app", "funcName": "process_payment", "user_id": "user_0", "amount": 42, "trace_id": "123e4567-e89b-12d3-a456-426614174000"}
```

## 🧠 Key Takeaway
Structured logging treats logs as data records rather than text strings, making debugging distributed systems significantly easier.
