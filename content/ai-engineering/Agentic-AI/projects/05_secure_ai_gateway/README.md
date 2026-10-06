# Secure AI Gateway & Semantic Cache

## Overview
This project demonstrates an enterprise AI Gateway designed in Golang to handle high-throughput LLM traffic. To reduce API costs and latency, it utilizes a Semantic Cache microservice written in Python.

## Architecture
- **Golang API Gateway**: Intercepts REST requests, calls the caching microservice via gRPC, and routes misses to the upstream LLM provider.
- **Python Semantic Cache (gRPC)**: Uses `sentence-transformers` and ChromaDB to evaluate if a new prompt is semantically identical to a previously cached prompt.
- **Redis (Optional)**: Acts as the exact-match caching layer before hitting the vector DB.

## Directory Structure
```
├── _project.md          # Design Challenge
├── proto/               # gRPC protobuf definitions
├── gateway/             # Golang API Gateway implementation
└── cache/               # Python Semantic Cache gRPC service
```
