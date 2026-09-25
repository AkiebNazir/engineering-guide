#!/bin/bash

echo "Starting a background sleep process..."
# Launch a background job using '&'
sleep 300 &

# Find its PID using pgrep
# We match the specific sleep command to be safe, but $$ or $! is more direct in a script.
# $! contains the process ID of the most recently executed background pipeline.
PID=$!
echo "Started sleep process with PID: $PID"

echo "Checking if process is running using pgrep..."
pgrep -f "sleep 300" 

echo "Checking open files for this process using lsof..."
# lsof might require elevated privileges or fail on some macOS setups without sudo, but we try:
lsof -p $PID || echo "lsof failed or found no files (normal for sleep without sudo)."

echo "Gracefully killing the background process with SIGTERM (15)..."
kill -15 $PID

echo "Verifying process termination..."
sleep 1
if ps -p $PID > /dev/null
then
   echo "Process $PID is still running. Force killing (SIGKILL)..."
   kill -9 $PID
else
   echo "Process $PID has been terminated."
fi
