import os
import time
import threading

def simulate_file_creation(file_path, delay):
    print(f"Simulation: File will be created in {delay} seconds...")
    time.sleep(delay)
    with open(file_path, "w") as f:
        f.write("data")
    print(f"Simulation: File '{file_path}' created.")

def file_sensor(file_path, check_interval=1, timeout=10):
    print(f"Sensor: Waiting for file '{file_path}' to appear...")
    start_time = time.time()
    
    while True:
        if os.path.exists(file_path):
            print(f"Sensor: File '{file_path}' detected!")
            return True
            
        if time.time() - start_time > timeout:
            print(f"Sensor: Timeout reached. File '{file_path}' not found.")
            return False
            
        time.sleep(check_interval)

if __name__ == "__main__":
    target_file = "trigger.txt"
    
    if os.path.exists(target_file):
        os.remove(target_file)
        
    # Start a background thread to simulate file creation
    threading.Thread(target=simulate_file_creation, args=(target_file, 4)).start()
    
    # Run the sensor
    if file_sensor(target_file):
        print("Executing next task: Processing data...")
    else:
        print("Pipeline aborted due to missing file.")
        
    if os.path.exists(target_file):
        os.remove(target_file)
