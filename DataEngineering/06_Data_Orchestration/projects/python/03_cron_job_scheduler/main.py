import time
from datetime import datetime

def data_pull():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pulling data from source...")
    time.sleep(1)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data pull complete.")

def run_scheduler(interval_seconds, duration_seconds):
    print(f"Starting cron scheduler (interval: {interval_seconds}s, duration: {duration_seconds}s)")
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        data_pull()
        time.sleep(interval_seconds)
        
    print("Scheduler finished.")

if __name__ == "__main__":
    run_scheduler(interval_seconds=3, duration_seconds=10)
