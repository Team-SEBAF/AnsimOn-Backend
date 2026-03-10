#!/usr/bin/env python3
"""
S3 trackings -> victims 폴더명 변경 일회용 마이그레이션 스크립트.

사용법:
  python scripts/migrate_s3_trackings_to_victims.py --env dev --dev-bucket ansimon-storage
  python scripts/migrate_s3_trackings_to_victims.py --env prod --prod-bucket ansimon-storage-prod
  python scripts/migrate_s3_trackings_to_victims.py --env both --dev-bucket ansimon-storage --prod-bucket ansimon-storage-prod
  python scripts/migrate_s3_trackings_to_victims.py --env both --dev-bucket ansimon-storage --prod-bucket ansimon-storage-prod --dry-run
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boto3

from app.core.settings import settings

OLD_SEGMENT = "evidences/trackings/"
NEW_SEGMENT = "evidences/victims/"


def run_migration(
    bucket: str,
    client: boto3.client,
    dry_run: bool,
    env_label: str,
) -> int:
    paginator = client.get_paginator("list_objects_v2")
    to_migrate: list[dict] = []

    print(f"\n[{env_label}] 버킷 '{bucket}'에서 '{OLD_SEGMENT}' 포함 객체 검색 중...")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents") or []:
            key = obj["Key"]
            if OLD_SEGMENT in key:
                new_key = key.replace(OLD_SEGMENT, NEW_SEGMENT, 1)
                to_migrate.append({"old_key": key, "new_key": new_key})

    if not to_migrate:
        print(f"[{env_label}] 변경할 객체가 없습니다.")
        return 0

    print(f"[{env_label}] 총 {len(to_migrate)}개 객체 발견")
    for i, item in enumerate(to_migrate[:3], 1):
        print(f"  {i}. {item['old_key']} -> {item['new_key']}")
    if len(to_migrate) > 3:
        print(f"  ... 외 {len(to_migrate) - 3}개")

    if dry_run:
        print(f"[{env_label}] [DRY-RUN] 건너뜀")
        return len(to_migrate)

    copied = 0
    deleted = 0
    for item in to_migrate:
        try:
            client.copy_object(
                Bucket=bucket,
                Key=item["new_key"],
                CopySource={"Bucket": bucket, "Key": item["old_key"]},
                MetadataDirective="COPY",
            )
            copied += 1
            client.delete_object(Bucket=bucket, Key=item["old_key"])
            deleted += 1
            if (copied + deleted) % 10 == 0:
                print(f"[{env_label}] 진행: {copied}개 복사/삭제 완료")
        except Exception as e:
            print(f"[{env_label}] 오류 ({item['old_key']}): {e}")

    print(f"[{env_label}] 완료: {copied}개 복사, {deleted}개 삭제")
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="S3 trackings -> victims 마이그레이션")
    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "prod", "both"],
        help="대상 환경 (dev, prod, both)",
    )
    parser.add_argument(
        "--dev-bucket",
        help="dev S3 버킷명 (--env dev 또는 both 시 필요)",
    )
    parser.add_argument(
        "--prod-bucket",
        help="prod S3 버킷명 (--env prod 또는 both 시 필요)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변경 없이 대상 객체만 출력",
    )
    args = parser.parse_args()

    buckets: list[tuple[str, str]] = []
    if args.env in ("dev", "both"):
        if not args.dev_bucket:
            print("--dev-bucket이 필요합니다.")
            sys.exit(1)
        buckets.append((args.dev_bucket, "dev"))
    if args.env in ("prod", "both"):
        if not args.prod_bucket:
            print("--prod-bucket이 필요합니다.")
            sys.exit(1)
        buckets.append((args.prod_bucket, "prod"))

    session_kwargs: dict = {"region_name": settings.AWS_REGION}
    if settings.AWS_PROFILE:
        session_kwargs["profile_name"] = settings.AWS_PROFILE

    session = boto3.Session(**session_kwargs)
    client = session.client(
        "s3",
        endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com",
    )

    if args.dry_run:
        print("[DRY-RUN] 실제 변경 없이 대상만 출력합니다.")
    else:
        labels = ", ".join(l for _, l in buckets)
        confirm = input(
            f"\n{labels} 버킷에서 trackings->victims 마이그레이션을 실행합니다. "
            "(--dry-run으로 먼저 확인 권장) 계속? (y/N): "
        )
        if confirm.lower() != "y":
            print("취소됨")
            sys.exit(0)

    for bucket, label in buckets:
        run_migration(
            bucket=bucket,
            client=client,
            dry_run=args.dry_run,
            env_label=label,
        )

    if not args.dry_run and buckets:
        print("\n모든 환경 마이그레이션 완료.")


if __name__ == "__main__":
    main()
