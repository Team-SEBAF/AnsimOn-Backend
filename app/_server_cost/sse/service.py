import logging

from app._server_cost.schemas import InfraStatusResponse
from app._server_cost.sse import utils as sse_utils
from app.core.settings import settings
from app.sse.service import get_sse_public_ip

logger = logging.getLogger(__name__)


class ServerCostSseService:
    def start_sse(self) -> None:
        sse_utils.set_desired_count(1)
        if settings.env == "prod":
            try:
                ready = sse_utils.wait_until_running_task_exists()
                if not ready:
                    logger.warning("prod sse task is not running yet; skip route53 upsert request")
                    return
                sse_utils.request_upsert_prod_sse_record()
            except Exception as e:
                logger.warning("prod sse route53 upsert request failed: %s", e)

    def stop_sse(self) -> None:
        sse_utils.set_desired_count(0)

    def get_sse_status(self) -> InfraStatusResponse:
        if sse_utils.ecs_running_count_at_least_one():
            return InfraStatusResponse(status="available")
        return InfraStatusResponse(status="unavailable")

    def get_prod_sse_network_sync(self) -> tuple[str | None, str | None, str | None, bool]:
        try:
            actual_ip = get_sse_public_ip()
        except Exception:
            actual_ip = None
        route53_ip = sse_utils.get_route53_record_ip()
        dns_ip = sse_utils.resolve_dns_ip()
        reachable = sse_utils.is_record_url_reachable()
        synced = bool(
            actual_ip and route53_ip and dns_ip and actual_ip == route53_ip == dns_ip and reachable
        )
        return actual_ip, route53_ip, dns_ip, synced


server_cost_sse_service = ServerCostSseService()
