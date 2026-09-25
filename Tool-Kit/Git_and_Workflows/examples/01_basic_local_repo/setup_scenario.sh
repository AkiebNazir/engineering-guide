#!/bin/bash
# Run this script to generate a basic Git repository
rm -rf my-project
mkdir my-project && cd my-project
git init
echo "Hello World" > index.txt
git add index.txt
git commit -m "Initial commit: Add index.txt"

git checkout -b feature/add-styles
echo "body { color: red; }" > style.css
git add style.css
git commit -m "Add basic styling"

git checkout main
echo "Footer" >> index.txt
git add index.txt
git commit -m "Update index footer"

echo "Repository generated! Check the branch history."
