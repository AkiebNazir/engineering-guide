# Chapter 14: Advanced CI/CD Patterns

<Exercise 4: Dynamic Pipeline Generator 🟡>
## 🎯 Objective
Create a Go script that dynamically generates a YAML CI/CD pipeline based on a configuration struct.

## 📋 Prerequisites
- Go 1.18+

## 📝 Instructions
1. Create a Go struct to represent a simple Pipeline.
2. Populate it programmatically based on a mock directory scan.
3. Marshal and print the YAML.

## 💡 Hints
- Use `gopkg.in/yaml.v3` if possible, but for standard library only, text/template works great.

## ✅ Expected Output / Solution
```go
package main

import (
	"os"
	"text/template"
)

type Job struct {
	Name string
	Path string
}

type Pipeline struct {
	Services []Job
}

const yamlTemplate = `name: Dynamic Monorepo Pipeline
on: [push]
jobs:
{{- range .Services }}
  build-{{ .Name }}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build {{ .Name }}
        run: cd {{ .Path }} && make build
{{- end }}
`

func main() {
	// Mock scanning directories
	pipeline := Pipeline{
		Services: []Job{
			{"auth", "services/auth"},
			{"billing", "services/billing"},
		},
	}

	tmpl, err := template.New("ci").Parse(yamlTemplate)
	if err != nil {
		panic(err)
	}

	err = tmpl.Execute(os.Stdout, pipeline)
	if err != nil {
		panic(err)
	}
}
```

## 🧠 Key Takeaway
Programmatically generating CI/CD pipelines ensures that as your architecture grows, your pipeline configuration naturally scales with it without massive copy-pasting.
</Exercise 4: Dynamic Pipeline Generator 🟡>
