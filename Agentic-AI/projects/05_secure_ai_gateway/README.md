# Secure <abbr title="Artificial Intelligence">AI</abbr> Gateway & Semantic Cache

## Overview
This project demonstrates an enterprise <abbr title="Artificial Intelligence">AI</abbr> Gateway designed in Golang to handle high-throughput <abbr title="Large Language Model">LLM</abbr> traffic. To reduce <abbr title="Application Programming Interface">API</abbr> costs and latency, it utilizes a Semantic Cache microservice written in Python.

## Architecture
- **Golang <abbr title="Application Programming Interface">API</abbr> Gateway**: Intercepts REST requests, calls the caching microservice via gRPC, and routes misses to the upstream <abbr title="Large Language Model">LLM</abbr> provider.
- **Python Semantic Cache (gRPC)**: Uses `sentence-transformers` and ChromaDB to evaluate if a new prompt is semantically identical to a previously cached prompt.
- **Redis (Optional)**: Acts as the exact-match caching layer before hitting the vector DB.

## Directory Structure
```
├── _project.md          # Design Challenge
├── proto/               # gRPC protobuf definitions
├── gateway/             # Golang API Gateway implementation
└── cache/               # Python Semantic Cache gRPC service
```
