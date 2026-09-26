import random
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class FlakyTaskError(Exception):
    pass

# Retry configuration:
# - Exponential backoff (wait = 2^x)
# - Max wait time of 10 seconds between retries
# - Stop after 5 total attempts
# - Only retry on FlakyTaskError
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(FlakyTaskError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def flaky_data_pull():
    logger.info("Attempting to pull data from upstream API...")
    if random.random() < 0.7:
        raise FlakyTaskError("Upstream API returned 503 Service Unavailable")
    
    logger.info("Data pull succeeded!")
    return {"data": [1, 2, 3]}

if __name__ == "__main__":
    try:
        result = flaky_data_pull()
        logger.info(f"Final result: {result}")
    except Exception as e:
        logger.error(f"Task ultimately failed after retries: {e}")
