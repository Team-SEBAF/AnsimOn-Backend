import boto3

from app.core.settings import settings


def get_ecs_client():
    return boto3.client("ecs", region_name=settings.AWS_REGION)


def get_application_autoscaling_client():
    return boto3.client("application-autoscaling", region_name=settings.AWS_REGION)


def get_ai_worker_cluster_service() -> tuple[str, str] | None:
    cluster = (settings.ECS_CLUSTER or "").strip()
    service = (settings.AI_WORKER_ECS_SERVICE or "").strip()
    if not cluster or not service:
        return None
    return cluster, service


def ai_worker_resource_id(cluster: str, service: str) -> str:
    return f"service/{cluster}/{service}"
