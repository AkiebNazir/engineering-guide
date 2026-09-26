import os
import time
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TriggerFileHandler(FileSystemEventHandler):
    """Event handler that sets an event flag when a specific file is created."""
    def __init__(self, target_filename, event_detected):
        self.target_filename = target_filename
        self.event_detected = event_detected

    def on_created(self, event):
        # Check if the created file matches our target
        if not event.is_directory and os.path.basename(event.src_path) == self.target_filename:
            logger.info(f"Detected creation of trigger file: {event.src_path}")
            self.event_detected.set()

def wait_for_file(watch_directory, target_filename, timeout_seconds=30):
    """
    Acts as a sensor, waiting for a file to appear in a directory.
    Uses 'watchdog' to listen for file system events instead of busy polling.
    """
    event_detected = threading.Event()
    event_handler = TriggerFileHandler(target_filename, event_detected)
    
    observer = Observer()
    observer.schedule(event_handler, path=watch_directory, recursive=False)
    
    logger.info(f"Starting sensor on directory '{watch_directory}' for file '{target_filename}'")
    observer.start()
    
    try:
        # Block until the file is created or the timeout is reached
        file_found = event_detected.wait(timeout=timeout_seconds)
    finally:
        observer.stop()
        observer.join()
        
    return file_found

def simulate_upstream_system(directory, filename, delay):
    """Simulates an external process dropping a file into the directory."""
    time.sleep(delay)
    file_path = os.path.join(directory, filename)
    logger.info(f"Upstream system creating file: {file_path}")
    with open(file_path, "w") as f:
        f.write("ready")

if __name__ == "__main__":
    watch_dir = "."
    trigger_file = "data_ready.trigger"
    
    # Ensure a clean state for the demo
    if os.path.exists(trigger_file):
        os.remove(trigger_file)
        
    # Simulate an external system dropping a file after some delay
    threading.Thread(target=simulate_upstream_system, args=(watch_dir, trigger_file, 5)).start()
    
    # Run the sensor
    if wait_for_file(watch_dir, trigger_file, timeout_seconds=15):
        logger.info("Sensor condition met! Triggering downstream pipeline...")
        # Clean up afterwards
        os.remove(trigger_file)
    else:
        logger.error("Sensor timed out waiting for the file.")
