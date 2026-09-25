#!/bin/bash

# Create a fake server.log file
cat <<EOF > server.log
2023-10-01 10:00:01 INFO 192.168.1.10 User logged in
2023-10-01 10:05:22 ERROR 10.0.0.5 Database connection failed {"user_id": 12, "db": "main"}
2023-10-01 10:06:00 INFO 192.168.1.11 Data exported
2023-10-01 10:10:15 ERROR 172.16.0.4 Timeout while waiting for response {"endpoint": "/api/v1/data"}
2023-10-01 10:15:30 ERROR 10.0.0.5 Database connection failed {"user_id": 12, "db": "main"}
EOF

echo "--- Original Log File ---"
cat server.log
echo

echo "--- Extracting Error IPs and Formatting ---"
# We pipeline cat, grep, awk, and sed:
# 1. cat: read the file
# 2. grep: find lines containing "ERROR"
# 3. awk: print the 4th column (the IP address)
# 4. sort & uniq: get unique IPs
# 5. sed: prefix with "Blocked IP: "

cat server.log | grep "ERROR" | awk '{print $4}' | sort | uniq | sed 's/^/Blocked IP: /'

echo "--- Done ---"
