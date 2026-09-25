# Exercise 3: Parallelism and Test Splitting 🟡

## 🎯 Objective
Optimize a slow test suite by splitting it across multiple concurrent runner nodes to reduce Lead Time.

## 📋 Prerequisites
- Python and Pytest knowledge.

## 📝 Instructions

1. Create a script simulating a slow test suite `test_slow.py`:
   ```python
   import time
   import pytest
   
   def test_feature_a():
       time.sleep(2)
       assert True
       
   def test_feature_b():
       time.sleep(2)
       assert True
       
   def test_feature_c():
       time.sleep(2)
       assert True
       
   def test_feature_d():
       time.sleep(2)
       assert True
   ```

2. Running sequentially takes 8+ seconds. We will write a script to split it. Create `split_runner.py`:
   ```python
   import sys
   import subprocess
   
   def run_split(total_nodes, current_node):
       # Get list of all tests
       result = subprocess.run(["pytest", "--collect-only", "-q"], capture_output=True, text=True)
       all_tests = [line for line in result.stdout.split('\n') if '::' in line]
       
       # Naive split: chunking
       chunk_size = max(1, len(all_tests) // total_nodes)
       start_idx = current_node * chunk_size
       
       if current_node == total_nodes - 1:
           end_idx = len(all_tests) # last node takes remainder
       else:
           end_idx = start_idx + chunk_size
           
       tests_to_run = all_tests[start_idx:end_idx]
       
       if not tests_to_run:
           print(f"Node {current_node}: No tests assigned.")
           return
           
       print(f"Node {current_node} running {len(tests_to_run)} tests...")
       cmd = ["pytest"] + tests_to_run
       subprocess.run(cmd)
   
   if __name__ == "__main__":
       total = int(sys.argv[1])
       node = int(sys.argv[2])
       run_split(total, node)
   ```

3. Test it locally in terminal 1: `python split_runner.py 2 0` (runs A & B in ~4s)
4. Test it locally in terminal 2: `python split_runner.py 2 1` (runs C & D in ~4s)

## 💡 Hints
- In a real CI system like GitLab or GitHub Actions, you use matrix strategies to spawn the nodes automatically.
- Advanced splitting tools (like `pytest-split`) balance tests based on historical execution time, not just count.

## ✅ Expected Output / Solution
The suite execution time drops from 8 seconds to 4 seconds because the workload is distributed across two independent processes.

## 🧠 Key Takeaway
Horizontal scaling (parallelism) is the most effective way to reduce pipeline execution time at enterprise scale, directly improving Developer Experience and DORA metrics.
