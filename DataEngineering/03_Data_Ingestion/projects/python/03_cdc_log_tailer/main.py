import time
import os

LOG_FILE = "cdc_mock.log"

def create_mock_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write("INIT: server started\n")

def tail_log(filepath):
    with open(filepath, 'r') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield line

def main():
    print('Starting Data Engineering Project: 03_cdc_log_tailer')
    create_mock_log()
    print(f"Tailing {LOG_FILE} for INSERT/UPDATE events (Ctrl+C to stop)...")
    
    try:
        for line in tail_log(LOG_FILE):
            if "INSERT" in line or "UPDATE" in line:
                print(f"Event detected: {line.strip()}")
    except KeyboardInterrupt:
        print("Stopped log tailing.")

if __name__ == '__main__':
    main()
