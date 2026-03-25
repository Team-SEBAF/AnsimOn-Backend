from app._server_cost.schemas import InfraStatusResponse
from app._server_cost.sse import utils as sse_utils


class ServerCostSseService:
    def start_sse(self) -> None:
        sse_utils.set_desired_count(1)

    def stop_sse(self) -> None:
        sse_utils.set_desired_count(0)

    def get_sse_status(self) -> InfraStatusResponse:
        if sse_utils.ecs_running_count_at_least_one():
            return InfraStatusResponse(status="available")
        return InfraStatusResponse(status="unavailable")


server_cost_sse_service = ServerCostSseService()
