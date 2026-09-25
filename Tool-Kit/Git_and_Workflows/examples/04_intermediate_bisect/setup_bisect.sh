#!/bin/bash
rm -rf bisect-repo
mkdir bisect-repo && cd bisect-repo
git init

for i in {1..4}
do
   echo "function calc(a, b) { return a + b; }" > math.js
   git add math.js
   git commit -m "Commit $i: Good code"
done

# The Bug
echo "function calc(a, b) { return a - b; }" > math.js
git add math.js
git commit -m "Commit 5: Feature update (Introduces Bug)"

for i in {6..10}
do
   echo "// Random comment $i" >> math.js
   git add math.js
   git commit -m "Commit $i: More code"
done

echo "Scenario created! There are 10 commits. A bug was introduced somewhere in the middle."
