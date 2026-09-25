#!/bin/bash
rm -rf conflict-repo
mkdir conflict-repo && cd conflict-repo
git init
echo "Line 1" > file.txt
echo "Line 2" >> file.txt
git add file.txt
git commit -m "Initial commit"

# Feature branch changes Line 2
git checkout -b feature/update-line
echo "Line 1" > file.txt
echo "Line 2 - Feature Branch Edit" >> file.txt
git add file.txt
git commit -m "Feature: update line 2"

# Main branch changes Line 2
git checkout main
echo "Line 1" > file.txt
echo "Line 2 - Main Branch Edit" >> file.txt
git add file.txt
git commit -m "Main: hotfix line 2"

echo "Scenario created! You are currently on the 'main' branch."
