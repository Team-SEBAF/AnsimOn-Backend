from botocore.exceptions import ClientError
from fastapi import HTTPException

from app._server_cost.ai_worker import utils as ai_worker_utils
from app.core.settings import settings


class ServerCostAiWorkerService:
    def _require_config(self) -> tuple[str, str]:
        cfg = ai_worker_utils.get_ai_worker_cluster_service()
        if not cfg:
            raise HTTPException(
                status_code=503,
                detail="ECS_CLUSTER / AI_WORKER_ECS_SERVICE 환경 변수가 설정되어 있지 않습니다.",
            )
        return cfg

    def _resource_id(self, cluster: str, service: str) -> str:
        return ai_worker_utils.ai_worker_resource_id(cluster, service)

    def _describe_scalable_target(self, resource_id: str) -> dict | None:
        client = ai_worker_utils.get_application_autoscaling_client()
        try:
            resp = client.describe_scalable_targets(
                ServiceNamespace="ecs",
                ResourceIds=[resource_id],
                ScalableDimension="ecs:service:DesiredCount",
            )
        except ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Application Auto Scaling describe_scalable_targets 실패: {e}",
            ) from e
        targets = resp.get("ScalableTargets") or []
        return targets[0] if targets else None

    def _register_min_max(self, resource_id: str, min_capacity: int, max_capacity: int) -> None:
        if max_capacity < min_capacity:
            max_capacity = min_capacity
        client = ai_worker_utils.get_application_autoscaling_client()
        try:
            client.register_scalable_target(
                ServiceNamespace="ecs",
                ResourceId=resource_id,
                ScalableDimension="ecs:service:DesiredCount",
                MinCapacity=min_capacity,
                MaxCapacity=max_capacity,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Application Auto Scaling register_scalable_target 실패: {e}",
            ) from e

    def raise_min_for_warm_pool(self) -> None:
        cluster, service = self._require_config()
        resource_id = self._resource_id(cluster, service)
        warm_min = settings.AI_WORKER_WARM_MIN_TASKS
        default_max = settings.AI_WORKER_AUTOSCALING_MAX_CAPACITY

        existing = self._describe_scalable_target(resource_id)
        max_cap = int(existing["MaxCapacity"]) if existing else default_max
        if max_cap < warm_min:
            max_cap = warm_min

        self._register_min_max(resource_id, warm_min, max_cap)

    def scale_down_off(self) -> None:
        cluster, service = self._require_config()
        resource_id = self._resource_id(cluster, service)
        default_max = settings.AI_WORKER_AUTOSCALING_MAX_CAPACITY

        existing = self._describe_scalable_target(resource_id)
        max_cap = int(existing["MaxCapacity"]) if existing else default_max

        self._register_min_max(resource_id, 0, max_cap)

        ecs = ai_worker_utils.get_ecs_client()
        try:
            ecs.update_service(
                cluster=cluster,
                service=service,
                desiredCount=0,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"AI Worker ECS update_service(desiredCount=0) 실패: {e}",
            ) from e

    def running_count_at_least_warm_min(self) -> bool:
        cfg = ai_worker_utils.get_ai_worker_cluster_service()
        if not cfg:
            return False
        cluster, service = cfg
        warm_min = settings.AI_WORKER_WARM_MIN_TASKS

        ecs = ai_worker_utils.get_ecs_client()
        try:
            resp = ecs.describe_services(cluster=cluster, services=[service])
        except ClientError:
            return False

        svcs = resp.get("services") or []
        if not svcs:
            return False

        running = int(svcs[0].get("runningCount") or 0)
        return running >= warm_min


server_cost_ai_worker_service = ServerCostAiWorkerService()
