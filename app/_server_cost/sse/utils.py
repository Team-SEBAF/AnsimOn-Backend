import socket
import time

import boto3
import httpx
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.settings import settings
from app.sse.service import get_sse_public_ip


def get_ecs_client():
    return boto3.client("ecs", region_name=settings.AWS_REGION)


def get_route53_client():
    return boto3.client("route53", region_name=settings.AWS_REGION)


def require_cluster_and_service() -> tuple[str, str]:
    cluster = (settings.ECS_CLUSTER or "").strip()
    service = (settings.SSE_ECS_SERVICE or "").strip()
    if not cluster or not service:
        raise HTTPException(
            status_code=503,
            detail="ECS_CLUSTER / SSE_ECS_SERVICE 환경 변수가 설정되어 있지 않습니다.",
        )
    return cluster, service


def set_desired_count(desired: int) -> None:
    cluster, service = require_cluster_and_service()
    ecs = get_ecs_client()
    try:
        ecs.update_service(
            cluster=cluster,
            service=service,
            desiredCount=desired,
        )
    except ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ECS update_service 실패: {e}",
        ) from e


def ecs_running_count_at_least_one() -> bool:
    cluster, service = require_cluster_and_service()
    ecs = get_ecs_client()
    try:
        resp = ecs.describe_services(cluster=cluster, services=[service])
    except ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ECS describe_services 실패: {e}",
        ) from e

    svcs = resp.get("services") or []
    if not svcs:
        raise HTTPException(
            status_code=404,
            detail="ECS 서비스를 찾을 수 없습니다.",
        )

    running_count = int(svcs[0].get("runningCount") or 0)
    return running_count >= 1


def wait_until_running_task_exists(
    timeout_seconds: int = 120, interval_seconds: float = 5.0
) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if ecs_running_count_at_least_one():
            return True
        time.sleep(interval_seconds)
    return ecs_running_count_at_least_one()


def _find_hosted_zone_id(zone_name: str) -> str | None:
    route53 = get_route53_client()
    try:
        zones = route53.list_hosted_zones_by_name(DNSName=zone_name).get("HostedZones") or []
    except ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Route53 hosted zone 조회 실패: {e}",
        ) from e

    for zone in zones:
        if zone.get("Name", "").rstrip(".") == zone_name.rstrip("."):
            return str(zone.get("Id", "")).split("/")[-1]
    return None


def request_upsert_prod_sse_record() -> None:
    record_name = settings.SSE_RECORD_NAME
    zone_name = settings.DOMAIN_ZONE_NAME
    try:
        public_ip = get_sse_public_ip()
    except Exception:
        return

    hosted_zone_id = _find_hosted_zone_id(zone_name)
    if not hosted_zone_id:
        raise HTTPException(
            status_code=503,
            detail=f"Route53 hosted zone을 찾을 수 없습니다: {zone_name}",
        )

    route53 = get_route53_client()
    try:
        route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "Sync SSE prod domain to latest ECS public IP",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": record_name,
                            "Type": "A",
                            "TTL": 300,
                            "ResourceRecords": [{"Value": public_ip}],
                        },
                    }
                ],
            },
        )
    except ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Route53 record 갱신 실패: {e}",
        ) from e


def get_route53_record_ip() -> str | None:
    record_name = settings.SSE_RECORD_NAME
    zone_name = settings.DOMAIN_ZONE_NAME
    hosted_zone_id = _find_hosted_zone_id(zone_name)
    if not hosted_zone_id:
        return None

    route53 = get_route53_client()
    try:
        resp = route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=record_name,
            StartRecordType="A",
            MaxItems="1",
        )
    except ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Route53 record 조회 실패: {e}",
        ) from e

    records = resp.get("ResourceRecordSets") or []
    if not records:
        return None
    first = records[0]
    if first.get("Name", "").rstrip(".") != record_name or first.get("Type") != "A":
        return None
    resource_records = first.get("ResourceRecords") or []
    if not resource_records:
        return None
    return resource_records[0].get("Value")


def resolve_dns_ip() -> str | None:
    try:
        return socket.gethostbyname(settings.SSE_RECORD_NAME)
    except OSError:
        return None


def is_record_url_reachable() -> bool:
    record_name = settings.SSE_RECORD_NAME
    try:
        response = httpx.get(f"https://{record_name}/docs", timeout=5.0)
        return response.status_code < 500
    except httpx.HTTPError:
        return False
