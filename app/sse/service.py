import boto3
from botocore.exceptions import ClientError

from app.base.base_error import CodeException
from app.core.settings import settings
from app.sse.errors.sse_url_error import SseUrlErrorCode


def _ecs_client():
    return boto3.client("ecs", region_name=settings.AWS_REGION)


def _ec2_client():
    return boto3.client("ec2", region_name=settings.AWS_REGION)


def _route53_client():
    return boto3.client("route53", region_name=settings.AWS_REGION)


def _eni_id_from_task(task: dict) -> str | None:
    for att in task.get("attachments") or []:
        if att.get("type") != "ElasticNetworkInterface":
            continue
        for d in att.get("details") or []:
            if d.get("name") == "networkInterfaceId" and d.get("value"):
                return d["value"]
    return None


def _get_sse_public_ip() -> str:
    """
    ECS Fargate 서비스의 RUNNING 태스크 1개의 Public IP를 반환.
    """
    cluster = (settings.ECS_CLUSTER or "").strip()
    service = (settings.SSE_ECS_SERVICE or "").strip()
    if not cluster or not service:
        raise CodeException(
            code=SseUrlErrorCode.SSE_NOT_CONFIGURED,
            message="SSE ECS 클러스터·서비스가 설정되어 있지 않습니다.",
            debug_message="환경 변수 ECS_CLUSTER, SSE_ECS_SERVICE를 설정하세요.",
            status_code=503,
        )

    ecs = _ecs_client()
    ec2 = _ec2_client()

    try:
        listed = ecs.list_tasks(
            cluster=cluster,
            serviceName=service,
            desiredStatus="RUNNING",
        )
    except ClientError as e:
        raise CodeException(
            code=SseUrlErrorCode.SSE_NOT_CONFIGURED,
            message="ECS API 호출에 실패했습니다.",
            debug_message=str(e),
            status_code=503,
        ) from e

    task_arns = listed.get("taskArns") or []
    if not task_arns:
        raise CodeException(
            code=SseUrlErrorCode.SSE_SERVER_NOT_RUNNING,
            message="실행 중인 SSE 서버 태스크가 없습니다.",
            debug_message=f"cluster={cluster}, service={service} 에 RUNNING 태스크가 없습니다.",
            status_code=503,
        )

    try:
        described = ecs.describe_tasks(cluster=cluster, tasks=task_arns[:1])
    except ClientError as e:
        raise CodeException(
            code=SseUrlErrorCode.SSE_SERVER_NOT_RUNNING,
            message="ECS 태스크 정보를 조회할 수 없습니다.",
            debug_message=str(e),
            status_code=503,
        ) from e

    tasks = described.get("tasks") or []
    if not tasks:
        raise CodeException(
            code=SseUrlErrorCode.SSE_SERVER_NOT_RUNNING,
            message="실행 중인 SSE 서버 태스크가 없습니다.",
            debug_message="describe_tasks 결과가 비어 있습니다.",
            status_code=503,
        )

    task = tasks[0]
    eni_id = _eni_id_from_task(task)
    if not eni_id:
        raise CodeException(
            code=SseUrlErrorCode.SSE_PUBLIC_IP_UNAVAILABLE,
            message="태스크에 네트워크 인터페이스를 찾을 수 없습니다.",
            debug_message="ElasticNetworkInterface attachment에 networkInterfaceId가 없습니다.",
            status_code=503,
        )

    try:
        ni_resp = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
    except ClientError as e:
        raise CodeException(
            code=SseUrlErrorCode.SSE_PUBLIC_IP_UNAVAILABLE,
            message="네트워크 인터페이스를 조회할 수 없습니다.",
            debug_message=str(e),
            status_code=503,
        ) from e

    interfaces = ni_resp.get("NetworkInterfaces") or []
    if not interfaces:
        raise CodeException(
            code=SseUrlErrorCode.SSE_PUBLIC_IP_UNAVAILABLE,
            message="네트워크 인터페이스를 찾을 수 없습니다.",
            debug_message=f"eni_id={eni_id}",
            status_code=503,
        )

    public_ip = (interfaces[0].get("Association") or {}).get("PublicIp")
    if not public_ip:
        raise CodeException(
            code=SseUrlErrorCode.SSE_PUBLIC_IP_UNAVAILABLE,
            message="태스크에 Public IP를 조회할 수 없습니다.",
            debug_message="assignPublicIp 미사용이거나 아직 할당되지 않았을 수 있습니다.",
            status_code=503,
        )

    return public_ip


def _ensure_prod_sse_domain_points_to_ip(public_ip: str) -> None:
    route53 = _route53_client()
    record_name = "prod.ansimon-sse.com"
    zone_name = "ansimon-sse.com"

    try:
        zones = route53.list_hosted_zones_by_name(DNSName=zone_name).get("HostedZones") or []
    except ClientError as e:
        raise CodeException(
            code=SseUrlErrorCode.SSE_NOT_CONFIGURED,
            message="Route53 호스팅 영역 조회에 실패했습니다.",
            debug_message=str(e),
            status_code=503,
        ) from e

    hosted_zone_id = ""
    for zone in zones:
        if zone.get("Name") == zone_name:
            hosted_zone_id = str(zone.get("Id", "")).split("/")[-1]
            break

    if not hosted_zone_id:
        raise CodeException(
            code=SseUrlErrorCode.SSE_NOT_CONFIGURED,
            message="SSE Route53 호스팅 영역을 찾을 수 없습니다.",
            debug_message=f"zone_name={zone_name}",
            status_code=503,
        )

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
        raise CodeException(
            code=SseUrlErrorCode.SSE_NOT_CONFIGURED,
            message="Route53 레코드 갱신에 실패했습니다.",
            debug_message=str(e),
            status_code=503,
        ) from e


def get_sse_server_url() -> str:
    public_ip = _get_sse_public_ip()

    if settings.env == "prod":
        _ensure_prod_sse_domain_points_to_ip(public_ip)
        return "https://prod.ansimon-sse.com"

    port = settings.SSE_SERVER_PORT
    return f"http://{public_ip}:{port}"
