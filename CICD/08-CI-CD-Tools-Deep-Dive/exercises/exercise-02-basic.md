# Exercise 2: Basic GitLab CI/CD Pipeline 🟢

## 🎯 Objective
Create a `.gitlab-ci.yml` file to compile and test a basic Go application using pipeline stages.

## 📋 Prerequisites
- Basic understanding of YAML.
- Familiarity with Go project structure.

## 📝 Instructions

1. **Create the Project Files**
   Imagine a simple Go application. Here is our `main.go`:

   ```go
   // main.go
   package main

   import "fmt"

   func CalculateTotal(a int, b int) int {
       return a + b
   }

   func main() {
       fmt.Println("Total is:", CalculateTotal(10, 20))
   }
   ```

   And the test file `main_test.go`:

   ```go
   // main_test.go
   package main

   import "testing"

   func TestCalculateTotal(t *testing.T) {
       result := CalculateTotal(10, 20)
       if result != 30 {
           t.Errorf("Expected 30, got %d", result)
       }
   }
   ```

2. **Define the GitLab Pipeline**
   Create a file named `.gitlab-ci.yml` in the root of your project.

   ```yaml
   # .gitlab-ci.yml
   # 1. Define global image (Docker container to run our jobs)
   image: golang:1.21

   # 2. Define the stages in exact execution order
   stages:
     - test
     - build

   # 3. Create the test job
   test_app:
     stage: test
     script:
       - echo "Running unit tests..."
       - go test -v ./...

   # 4. Create the build job
   build_app:
     stage: build
     script:
       - echo "Compiling the Go application..."
       - go build -o bin/myapp main.go
     
     # 5. Save the compiled binary as an artifact
     artifacts:
       paths:
         - bin/myapp
       expire_in: 1 week
   ```

## 💡 Hints
- GitLab CI heavily relies on Docker. The `image: golang:1.21` tells GitLab's runner to spin up a Go container to execute the script commands.
- `stages` enforce order. All jobs in `test` must pass before any job in `build` begins.
- `artifacts` allow you to download the `bin/myapp` executable from the GitLab UI after the pipeline finishes.

## ✅ Expected Output / Solution
In the GitLab CI/CD pipelines view, you will see a pipeline with two stages:
1. `test_app` (Stage: test) - executes `go test` and passes.
2. `build_app` (Stage: build) - executes `go build` and uploads `bin/myapp`.

```text
$ go test -v ./...
=== RUN   TestCalculateTotal
--- PASS: TestCalculateTotal (0.00s)
PASS

$ go build -o bin/myapp main.go
Uploading artifacts for successful job...
```

## 🧠 Key Takeaway
GitLab CI/CD is fundamentally stage-driven. By simply mapping out your `stages` and assigning jobs to them, you can easily control the flow of execution. The native Docker integration (`image`) means you don't need to manually configure the environment.
