#!/usr/bin/env bash
# Regenerates the Python and Go code for the Protobuf Foundation levels.
# Needs: protoc, protoc-gen-go (go install google.golang.org/protobuf/cmd/protoc-gen-go@latest),
#        `pip install grpcio-tools` for the Python side, and - only for level
#        08 - buf (go install github.com/bufbuild/buf/cmd/buf@latest).
#
# The generated files are CHECKED IN, exactly like ../labs/, so every level
# runs straight from a fresh clone without running this script first.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PATH:$(go env GOPATH)/bin"

# ---- the official toolchain: protoc, one flag per concern ------------------
# --python_out : where the *_pb2.py files go (flat, next to the level files)
# --go_out=.   : output root
# --go_opt=module=... : strip this prefix off each file's `option go_package`
#                       to decide its path under the output root
python3 -m grpc_tools.protoc -I proto --python_out=python proto/*.proto
protoc -I proto --go_out=. --go_opt=module=dsapractice/api/Protobuf/Foundation proto/*.proto
echo "protoc : generated python/*_pb2.py and golang/pb/*/*.pb.go"

# ---- level 08 only: the same schema through buf ---------------------------
# Everything protoc needed on the command line above is already declared in
# buf.yaml + buf.gen.yaml, so this call takes no flags except the filter.
if command -v buf >/dev/null 2>&1; then
  buf generate --path proto/l08_toolchains.proto
  echo "buf    : generated buf_out/ (level 08 compares it against protoc's output)"
else
  echo "buf    : NOT INSTALLED - skipping. Level 08 still runs; it falls back to"
  echo "         the checked-in buf output. Install with:"
  echo "         go install github.com/bufbuild/buf/cmd/buf@latest"
fi
