import logging
import json
import time

# Create a logger that writes raw JSON to a file (Best Practice for ELK)
logger = logging.getLogger("json_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('/var/log/app/app.log')
logger.addHandler(file_handler)

def log_json(level, message, user_id=None):
    log_record = {
        "timestamp": time.time(),
        "level": level,
        "message": message,
        "user_id": user_id,
        "service": "python-backend"
    }
    logger.info(json.dumps(log_record))

print("Starting logging simulation...")
i = 0
while True:
    log_json("INFO", f"Processed task {i}", user_id=i%5)
    time.sleep(2)
    i += 1
