import time
import random
import logging
from prometheus_client import start_http_server, Summary, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define Prometheus metrics
PIPELINE_DURATION = Summary('pipeline_processing_seconds', 'Time spent processing pipeline tasks', ['task_name'])
PIPELINE_STATUS = Counter('pipeline_task_status_total', 'Count of pipeline task statuses', ['task_name', 'status'])

class DataPipelineException(Exception):
    pass

def execute_task(task_name: str):
    logger.info(f"Executing task: {task_name}")
    
    # Track the duration of the task
    with PIPELINE_DURATION.labels(task_name=task_name).time():
        # Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simulate occasional failures for monitoring demonstration
        if random.random() < 0.2:
            PIPELINE_STATUS.labels(task_name=task_name, status="failed").inc()
            logger.error(f"Task failed: {task_name}")
            raise DataPipelineException(f"Task {task_name} encountered an error.")
            
        PIPELINE_STATUS.labels(task_name=task_name, status="success").inc()
        logger.info(f"Task completed: {task_name}")

def run_pipeline():
    tasks = ["Extract", "Transform", "Load"]
    for task in tasks:
        try:
            execute_task(task)
        except DataPipelineException as e:
            logger.critical(f"Pipeline halted due to error: {e}")
            break
    logger.info("Pipeline run finished.")

if __name__ == "__main__":
    # Start the Prometheus metrics HTTP server on port 8000
    # Data Engineers use Prometheus + Grafana to scrape these metrics and build dashboards
    logger.info("Starting Prometheus metrics server on port 8000")
    start_http_server(8000)
    
    # Run the pipeline periodically to generate metrics continuously
    try:
        while True:
            run_pipeline()
            logger.info("Sleeping before next pipeline run...")
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down data pipeline monitor.")
