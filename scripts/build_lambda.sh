#!/usr/bin/env bash
set -e  # 중간에 하나라도 실패하면 즉시 종료

echo "▶︎ Export requirements.txt from poetry"
poetry export -f requirements.txt --without-hashes -o requirements.txt

echo "▶︎ Clean package directory"
rm -rf package lambda.zip
mkdir package

echo "▶︎ Install dependencies in Lambda-compatible environment (Docker)"
docker run --rm \
  -v "$PWD":/var/task \
  --platform linux/amd64 \
  public.ecr.aws/sam/build-python3.11 \
  bash -c "
    pip install --upgrade pip &&
    pip install --no-cache-dir -r requirements.txt -t package
  "

echo "▶︎ Copy application code"
cp -r app package/

echo "▶︎ Create lambda.zip"
cd package
zip -r ../lambda.zip . > /dev/null
cd ..

echo "✅ Build complete: lambda.zip"
