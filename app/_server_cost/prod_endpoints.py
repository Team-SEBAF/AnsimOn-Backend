import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app._server_cost.ai_worker.service import server_cost_ai_worker_service
from app._server_cost.db.service import server_cost_db_service
from app._server_cost.schemas import ProdServerCostStatusResponse
from app._server_cost.sse.service import server_cost_sse_service
from app.base.base_response import BaseSuccessResponse
from app.core.database import get_db

router = APIRouter(
    prefix="/api/v1/server_cost",
    tags=["Server On/Off (배포 웹사이트 사용하기 전, Prod 서버 실행 필요)"],
)
logger = logging.getLogger(__name__)


@router.post(
    "/on",
    summary="Prod 서버 시작 (대략 8~12분 소요)",
    response_model=BaseSuccessResponse,
)
async def server_on():
    try:
        results = await asyncio.gather(
            asyncio.to_thread(server_cost_db_service.start_db),
            asyncio.to_thread(server_cost_sse_service.start_sse),
            asyncio.to_thread(server_cost_ai_worker_service.raise_min_for_warm_pool),
            return_exceptions=True,
        )
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("server_on partial failure index=%s error=%s", idx, result)
    except Exception as e:
        logger.exception("server_on unexpected failure: %s", e)
    return BaseSuccessResponse(
        message="Prod 서버 시작 요청을 보냈습니다. 대략 8~12분 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다."
    )


@router.get(
    "/status",
    summary="Prod 서버 실행 여부 조회 (DB / SSE / AI 모두 available 이어야 배포 웹사이트 정상 동작)",
    response_model=ProdServerCostStatusResponse,
)
def server_status(db: Session = Depends(get_db)):
    db_st = server_cost_db_service.get_db_connection_status(db)
    sse_st = server_cost_sse_service.get_sse_status()
    ai_ok = server_cost_ai_worker_service.running_count_at_least_warm_min()

    network_sync = server_cost_sse_service.get_prod_sse_network_sync()
    sse_synced = network_sync[3]
    sse_available = sse_st.status == "available" and sse_synced
    return ProdServerCostStatusResponse(
        db=db_st.status,
        sse="available" if sse_available else "unavailable",
        ai="available" if ai_ok else "unavailable",
    )


@router.post(
    "/off",
    summary="Prod 서버 중지 (대략 8~15분 소요, 결과 기다리지 않아도 됨)",
    response_model=BaseSuccessResponse,
)
async def server_off():
    await asyncio.gather(
        asyncio.to_thread(server_cost_db_service.stop_db),
        asyncio.to_thread(server_cost_sse_service.stop_sse),
        asyncio.to_thread(server_cost_ai_worker_service.scale_down_off),
    )
    return BaseSuccessResponse(
        message="Prod 서버 중지 요청을 보냈습니다. 대략 8~15분 소요될 수 있습니다."
    )
