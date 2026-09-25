import time
import random
from datetime import datetime

class DataPipelineMonitor:
    def __init__(self):
        self.logs = []
        
    def log_status(self, task_name, status, duration):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task_name,
            "status": status,
            "duration": duration
        }
        self.logs.append(log_entry)
        print(f"[{log_entry['timestamp']}] Task '{task_name}': {status} ({duration:.2f}s)")
        
    def alert(self, task_name, error_msg):
        print(f"\n[ALERT] Pipeline failed at task '{task_name}'")
        print(f"Reason: {error_msg}")
        print("Summary of execution:")
        for log in self.logs:
            print(f"  - {log['task']}: {log['status']} ({log['duration']:.2f}s)")

def run_pipeline():
    monitor = DataPipelineMonitor()
    tasks = ["Extract", "Transform", "Load"]
    
    for task in tasks:
        start_time = time.time()
        time.sleep(random.uniform(0.5, 1.5))
        duration = time.time() - start_time
        
        # Simulate failure
        if task == "Transform" and random.random() < 0.5:
            monitor.log_status(task, "FAILED", duration)
            monitor.alert(task, "Data validation error during transformation.")
            return
            
        monitor.log_status(task, "SUCCESS", duration)
        
    print("\nPipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline()
