#!/bin/bash

TARGET="example.com"

echo "--- 1. Pinging $TARGET ---"
# Ping sends ICMP ECHO_REQUEST to network hosts
ping -c 3 $TARGET

echo -e "\n--- 2. DNS Resolution with dig ---"
# dig is a tool for interrogating DNS name servers
dig $TARGET +short

echo -e "\n--- 3. Fetching HTTP Headers with curl -I ---"
# curl -I fetches only the HTTP headers
curl -I https://$TARGET

echo -e "\n--- 4. Checking Listening Ports ---"
# On Linux, `ss -tulpn` shows listening TCP/UDP ports and their processes.
# On macOS, `ss` is not available, so we fallback to `lsof` or `netstat`.
if command -v ss &> /dev/null; then
    echo "Using ss:"
    # Note: Requires root to show process names
    ss -tulpn | head -n 10
else
    echo "ss not found (common on macOS). Using netstat -an | grep LISTEN"
    netstat -an | grep LISTEN | head -n 10
fi
