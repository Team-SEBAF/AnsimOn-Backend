#!/usr/bin/env bash
# Lambda 레이어용 ffmpeg 단일 바이너리 ZIP → 프로젝트 루트 ffmpeg-layer.zip
#
# 레이어 안 경로: bin/ffmpeg  →  런타임에서 /opt/bin/ffmpeg (앱 코드와 동일)
# 대상: Lambda x86_64 (패키지명 amd64-static = x86_64와 동일 아키텍처)
#
# 참고: publish-layer-version 시 ZIP을 직접 올리면 50MB 제한이 있음.
#       초과 시 S3에 올린 뒤 --content 로 S3 키를 지정해 레이어 버전을 만든다.
#
# Graviton(arm64) 람다면 이 스크립트 대신 arm64용 정적 빌드를 써야 함.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
ARCHIVE="ffmpeg-release-amd64-static.tar.xz"
OUT_ZIP="ffmpeg-layer.zip"
WORKDIR="layer_build_ffmpeg"

rm -f "$OUT_ZIP"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Downloading $URL ..."
curl -fsSL -o "$ARCHIVE" "$URL"

echo "Extracting ..."
tar -xJf "$ARCHIVE"
rm -f "$ARCHIVE"

FFMPEG_BIN=$(find . -type f -name ffmpeg -perm -111 | head -1)
if [[ -z "$FFMPEG_BIN" ]]; then
  echo "ffmpeg binary not found in archive" >&2
  exit 1
fi

mkdir -p bin
cp -f "$FFMPEG_BIN" bin/ffmpeg
chmod 755 bin/ffmpeg

if command -v strip >/dev/null 2>&1; then
  strip --strip-unneeded bin/ffmpeg 2>/dev/null || true
fi

cd "$ROOT"
( cd "$WORKDIR" && zip -9 -r "../$OUT_ZIP" bin )
rm -rf "$WORKDIR"

ls -lh "$ROOT/$OUT_ZIP"
SIZE_BYTES=$(stat -f%z "$ROOT/$OUT_ZIP" 2>/dev/null || stat -c%s "$ROOT/$OUT_ZIP" 2>/dev/null)
MAX_DIRECT=$((50 * 1024 * 1024))
if [[ "$SIZE_BYTES" -gt "$MAX_DIRECT" ]]; then
  echo ""
  echo "WARN: ZIP이 ${SIZE_BYTES} bytes (> 50MB). Lambda에 직접 업로드 불가 → S3 업로드 후 publish-layer-version --content S3Bucket=...,S3Key=... 사용." >&2
else
  echo "OK: 50MB 이하 — aws lambda publish-layer-version --zip-file fileb://ffmpeg-layer.zip 가능"
fi
