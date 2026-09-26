import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_data_pipeline(pipeline_name: str):
    logger.info(f"Starting pipeline: {pipeline_name}")
    # Simulate pipeline execution
    time.sleep(2)
    logger.info(f"Completed pipeline: {pipeline_name}")

if __name__ == "__main__":
    # Initialize the scheduler
    scheduler = BackgroundScheduler()

    # Schedule a task to run every minute
    scheduler.add_job(
        run_data_pipeline,
        trigger=CronTrigger(minute="*"), # Equivalent to cron '* * * * *'
        args=["Hourly_Sales_Aggregation"],
        id="sales_pipeline_job",
        replace_existing=True
    )

    logger.info("Starting scheduler. Press Ctrl+C to exit.")
    scheduler.start()

    try:
        # Keep the main thread alive to allow background jobs to run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
