import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.settings import settings


def get_ecs_client():
    return boto3.client("ecs", region_name=settings.AWS_REGION)


def require_cluster_and_service() -> tuple[str, str]:
    cluster = (settings.SSE_ECS_CLUSTER or "").strip()
    service = (settings.SSE_ECS_SERVICE or "").strip()
    if not cluster or not service:
        raise HTTPException(
            status_code=503,
            detail="SSE_ECS_CLUSTER / SSE_ECS_SERVICE 환경 변수가 설정되어 있지 않습니다.",
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
