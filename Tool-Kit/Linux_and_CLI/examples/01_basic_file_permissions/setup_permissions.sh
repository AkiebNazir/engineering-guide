#!/bin/bash

# This script demonstrates basic file permissions, chown, and the sticky bit.

# Create a shared directory
mkdir -p shared_dir
echo "Created shared_dir"

# Simulate creating a file inside
touch shared_dir/project_file.txt
echo "Created shared_dir/project_file.txt"

# Change permissions: owner rwx, group rx, others rx
chmod 755 shared_dir
echo "Set 755 permissions on shared_dir"

# Change permissions on file: rw for owner, r for group/others
chmod 644 shared_dir/project_file.txt
echo "Set 644 permissions on shared_dir/project_file.txt"

# Set the sticky bit on the directory
# This ensures only the file owner, directory owner, or root can delete files within it
chmod +t shared_dir
echo "Set sticky bit (+t) on shared_dir. (Drwxr-xr-t)"

# Show permissions
ls -ld shared_dir
ls -l shared_dir/project_file.txt

# Note: chown requires root privileges for changing ownership to another user.
# We will simulate the command as a comment:
# sudo chown alice:developers shared_dir
# sudo chown alice:developers shared_dir/project_file.txt
echo "To change ownership, you would use: sudo chown user:group filename"
