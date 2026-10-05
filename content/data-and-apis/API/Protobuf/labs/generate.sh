#!/usr/bin/env bash
# Regenerates the Python and Go code for the Protobuf labs.
# Needs: protoc, protoc-gen-go (go install google.golang.org/protobuf/cmd/protoc-gen-go@latest),
#        and `pip install grpcio-tools` for the Python side.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PATH:$(go env GOPATH)/bin"

python3 -m grpc_tools.protoc -I proto --python_out=python proto/*.proto
protoc -I proto --go_out=golang/pb --go_opt=paths=source_relative proto/demo.proto
echo "generated: python/*_pb2.py and golang/pb/demo.pb.go"
