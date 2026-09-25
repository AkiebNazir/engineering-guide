#!/bin/bash

echo "This script demonstrates how to set up a systemd service."
echo "Note: Running these commands usually requires root (sudo) and a Linux system with systemd."

echo "1. Copying the unit file to /etc/systemd/system/..."
echo "sudo cp my-app.service /etc/systemd/system/"

echo "2. Reloading systemd manager configuration..."
echo "sudo systemctl daemon-reload"

echo "3. Starting the service..."
echo "sudo systemctl start my-app"

echo "4. Enabling the service to start on boot..."
echo "sudo systemctl enable my-app"

echo "5. Checking the status of the service..."
echo "sudo systemctl status my-app"

echo "6. Viewing the logs using journalctl..."
echo "sudo journalctl -u my-app -f"

echo "\nNote: On macOS, launchd is used instead of systemd. These commands are simulated for documentation."
