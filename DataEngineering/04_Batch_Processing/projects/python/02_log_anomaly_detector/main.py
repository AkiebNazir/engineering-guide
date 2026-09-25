import re
from collections import defaultdict

def generate_logs(filename="server.log"):
    logs = [
        "192.168.1.1 - - [10/Oct/2023:13:55:36 -0700] \"GET /index.html HTTP/1.1\" 200 2326\n",
        "10.0.0.5 - - [10/Oct/2023:13:55:37 -0700] \"GET /missing.html HTTP/1.1\" 404 232\n",
    ] * 100
    logs.extend(["10.0.0.5 - - [10/Oct/2023:13:56:00 -0700] \"GET /missing2.html HTTP/1.1\" 404 232\n"] * 50)
    with open(filename, "w") as f:
        f.writelines(logs)

def detect_anomalies(filename="server.log", threshold=10):
    error_counts = defaultdict(int)
    log_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+).*" \w+ .* HTTP/1.\d" (\d{3})')
    
    with open(filename, "r") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                ip = match.group(1)
                status = match.group(2)
                if status == '404':
                    error_counts[ip] += 1
                    
    print("Anomalous IPs (high 404 rate):")
    for ip, count in error_counts.items():
        if count > threshold:
            print(f"{ip}: {count} errors")

if __name__ == "__main__":
    generate_logs()
    detect_anomalies()
