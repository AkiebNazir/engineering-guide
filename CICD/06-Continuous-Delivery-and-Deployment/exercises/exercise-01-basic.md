# Exercise 1: Basic Deployment Script 🚀

## 🎯 Objective
Write a basic bash script to simulate a deployment by checking for a version parameter and setting up a directory structure.

## 📋 Prerequisites
- A Unix-like terminal (macOS/Linux)
- Basic shell scripting knowledge

## 📝 Instructions
1. Create a file named `deploy.sh`.
2. Make it executable (`chmod +x deploy.sh`).
3. The script should accept one argument: the version number.
4. If no version is provided, it should print an error and exit.
5. Create a fake application directory `/tmp/app_deploy/<version>`.
6. Update a symlink `/tmp/app_deploy/current` to point to the new version.

## 💡 Hints
- Use `$1` to get the first argument in bash.
- Use `ln -sfn <target> <link_name>` to force-update a symbolic link.

## ✅ Expected Output / Solution

```bash
#!/bin/bash
# deploy.sh

VERSION=$1

# 1. Check for version argument
if [ -z "$VERSION" ]; then
    echo "Error: Version argument is required."
    echo "Usage: ./deploy.sh v1.0.0"
    exit 1
fi

echo "Starting deployment for version: $VERSION"

BASE_DIR="/tmp/app_deploy"
TARGET_DIR="$BASE_DIR/$VERSION"
CURRENT_LINK="$BASE_DIR/current"

# 2. Create the target directory
mkdir -p "$TARGET_DIR"
echo "Dummy app content for $VERSION" > "$TARGET_DIR/app.txt"

# 3. Update the symlink
ln -sfn "$TARGET_DIR" "$CURRENT_LINK"

echo "Deployment successful! Current version points to:"
ls -l "$CURRENT_LINK"
```

## 🧠 Key Takeaway
Using a symbolic link (symlink) to point to the `current` version is a classic deployment pattern. It allows you to quickly update what version the web server points to instantly, and easily swap it back if you need to roll back.
