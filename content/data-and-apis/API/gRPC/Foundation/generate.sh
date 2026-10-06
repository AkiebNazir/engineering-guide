#!/usr/bin/env bash
# Regenerates the Python and Go gRPC stubs for every Foundation level.
#
# Each level owns ONE small, self-contained .proto in proto/ so that no level
# depends on another level's contract. The generated code is committed, so you
# only need to run this if you EDIT a .proto (which is the whole point of the
# contract-first workflow taught in level 01: edit .proto -> regenerate -> code).
#
# Needs: protoc, protoc-gen-go and protoc-gen-go-grpc on PATH
#   go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
#   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
# and `pip install grpcio-tools` for the Python side.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PATH:$(go env GOPATH)/bin"

for p in proto/*.proto; do
  base="$(basename "$p" .proto)"   # e.g. "ping"
  pkg="${base}pb"                  # e.g. "pingpb", matching this proto's go_package
  mkdir -p "golang/pb/$pkg"

  python3 -m grpc_tools.protoc -I proto --python_out=python --grpc_python_out=python "$p"
  protoc -I proto --go_out="golang/pb/$pkg" --go_opt=paths=source_relative \
         --go-grpc_out="golang/pb/$pkg" --go-grpc_opt=paths=source_relative "$p"

  echo "generated: python/${base}_pb2*.py and golang/pb/$pkg/${base}*.pb.go"
done
