# Exercise 4: Declarative Jenkins Pipeline 🟡

## 🎯 Objective
Create a declarative `Jenkinsfile` that leverages parallel stages to build and test both a Go and Python application simultaneously, then archives the output.

## 📋 Prerequisites
- Familiarity with Groovy-like syntax used in Jenkinsfiles.
- Understanding of Jenkins pipeline structure.

## 📝 Instructions

1. **The Scenario**
   You have a repository containing a frontend application written in Python and a backend service written in Go. You want Jenkins to build both as fast as possible by running them in parallel. 

2. **Create the Jenkinsfile**
   Create a file named `Jenkinsfile` in the root of your project:

   ```groovy
   // Jenkinsfile
   pipeline {
       // 1. Do not use a global agent, as we want specific docker images for each language
       agent none
       
       stages {
           stage('Build and Test') {
               // 2. Define parallel execution
               parallel {
                   
                   // Branch A: Go Backend
                   stage('Go Backend') {
                       // Spin up a specific Go docker container for this stage
                       agent {
                           docker { image 'golang:1.21' }
                       }
                       steps {
                           echo "Building Go application..."
                           sh 'go build -o api-server ./cmd/api'
                           sh 'go test ./...'
                       }
                       // Archive the Go binary
                       post {
                           success {
                               archiveArtifacts artifacts: 'api-server', fingerprint: true
                           }
                       }
                   }
                   
                   // Branch B: Python Frontend Worker
                   stage('Python Worker') {
                       // Spin up a specific Python docker container for this stage
                       agent {
                           docker { image 'python:3.11' }
                       }
                       steps {
                           echo "Installing dependencies..."
                           sh 'pip install flake8'
                           echo "Linting Python code..."
                           sh 'flake8 .'
                       }
                   }
               }
           }
       }
       
       // 3. Define global post-actions
       post {
           always {
               echo "Pipeline execution finished."
           }
           failure {
               echo "Slack Notification: Pipeline Failed!"
           }
           success {
               echo "Slack Notification: Pipeline Succeeded!"
           }
       }
   }
   ```

## 💡 Hints
- `agent none` at the top level is important when you want to define specific `agent { docker { ... } }` blocks at the stage level. Otherwise, Jenkins would spin up a default agent, then spin up Docker containers inside or alongside it unnecessarily.
- The `parallel` block allows independent stages to run concurrently, drastically reducing build times for polyglot repositories.
- The `post` block can be attached to the entire pipeline or individual stages.

## ✅ Expected Output / Solution
In Jenkins Blue Ocean UI, you will see a graph that splits into two concurrent tracks: `Go Backend` and `Python Worker`. 
- If both succeed, the pipeline joins back together, executes the global `success` post-action, and you will see `api-server` available for download in the Artifacts tab.

## 🧠 Key Takeaway
Jenkins Declarative Pipelines provide a highly readable, structured way to define complex CI workflows. By leveraging `parallel` tracks and stage-specific Docker agents, Jenkins can effortlessly handle multi-language enterprise repositories in a single run.
