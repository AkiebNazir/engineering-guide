#!/usr/bin/env bash
# Regenerates the Python and Go gRPC stubs for the labs.
# Needs: protoc, protoc-gen-go and protoc-gen-go-grpc on PATH
#   go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
#   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
# and `pip install grpcio-tools` for the Python side.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PATH:$(go env GOPATH)/bin"

python3 -m grpc_tools.protoc -I proto --python_out=python --grpc_python_out=python proto/shop.proto
protoc -I proto --go_out=golang/shoppb --go_opt=paths=source_relative \
       --go-grpc_out=golang/shoppb --go-grpc_opt=paths=source_relative proto/shop.proto
echo "generated: python/shop_pb2*.py and golang/shoppb/shop*.pb.go"
