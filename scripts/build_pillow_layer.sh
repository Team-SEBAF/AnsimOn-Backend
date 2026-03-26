#!/usr/bin/env bash
# Lambda 레이어용 pillow + pillow-heif ZIP 생성 → 프로젝트 루트 pillow-layer.zip
# 대상: Python 3.11, manylinux x86_64 (Lambda x86_64 런타임과 동일 휠)
# Graviton(arm64) 람다면 --platform manylinux2014_aarch64 등으로 바꿔서 다시 빌드할 것.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -f pillow-layer.zip
rm -rf layer_build
mkdir -p layer_build/python/lib/python3.11/site-packages

pip install --no-cache-dir \
  "pillow>=12.1.0,<13" "pillow-heif>=0.21.0,<1" \
  -t layer_build/python/lib/python3.11/site-packages \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  --upgrade

find layer_build -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find layer_build -name "*.pyc" -delete 2>/dev/null || true

( cd layer_build && zip -r ../pillow-layer.zip python )
rm -rf layer_build

ls -lh "$ROOT/pillow-layer.zip"
