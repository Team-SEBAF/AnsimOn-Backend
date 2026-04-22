import logging
import shutil
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app._server_cost.db.service import server_cost_db_service
from app.core.aws import delete_s3_objects_by_prefix, get_s3_client
from app.core.database import SessionLocal
from app.core.settings import settings
from app.domain.user import UserRepository
from app.main import app

logger = logging.getLogger(__name__)

DEV_BASE_URL = "https://fvccs6z1m1.execute-api.ap-northeast-2.amazonaws.com/dev"
PROD_BASE_URL = "https://cus4odof27.execute-api.ap-northeast-2.amazonaws.com/prod"
INTEGRATION_DATASET_PREFIX = "integration_test_set/"
INTEGRATION_DATASET_DOWNLOAD_DIR = Path(__file__).resolve().parent / "integration_test_set"


def _get_test_target() -> str:
    return settings.env.lower()


def _get_base_url(test_target: str) -> str | None:
    if test_target == "dev":
        return DEV_BASE_URL
    if test_target == "prod":
        return PROD_BASE_URL
    return None


def _url(base_url: str | None, path: str) -> str:
    if base_url is None:
        return path
    return f"{base_url}{path}"


def _download_integration_dataset() -> None:
    logger.info("(4) 테스트 데이터셋 다운로드 시작")

    if INTEGRATION_DATASET_DOWNLOAD_DIR.exists():
        shutil.rmtree(INTEGRATION_DATASET_DOWNLOAD_DIR)
    INTEGRATION_DATASET_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    downloaded_count = 0

    for page in paginator.paginate(
        Bucket=settings.S3_BUCKET_NAME,
        Prefix=INTEGRATION_DATASET_PREFIX,
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue

            relative_key = key.removeprefix(INTEGRATION_DATASET_PREFIX)
            if not relative_key:
                continue

            local_path = INTEGRATION_DATASET_DOWNLOAD_DIR / relative_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(settings.S3_BUCKET_NAME, key, str(local_path))
            downloaded_count += 1

    logger.info(
        "(4) 테스트 데이터셋 다운로드 완료 (files=%s, dir=%s)",
        downloaded_count,
        INTEGRATION_DATASET_DOWNLOAD_DIR,
    )


@pytest.fixture(scope="session")
def client() -> Any:
    test_target = _get_test_target()
    logger.info("ENV=%s", test_target)

    if test_target == "local":
        with TestClient(app) as local_client:
            yield local_client
        return

    base_url = _get_base_url(test_target)
    if base_url is None:
        raise ValueError("ENV must be one of: local, dev, prod")

    with httpx.Client(timeout=30.0) as remote_client:
        remote_client.base_url = httpx.URL(base_url)
        yield remote_client


@pytest.fixture(scope="session")
def integration_context(client: Any) -> dict[str, str]:
    test_target = _get_test_target()
    base_url = _get_base_url(test_target)
    db = SessionLocal()
    try:
        logger.info("integration_context 시작")

        # 1. DB 연결 상태 확인
        logger.info("(1) DB 연결 상태 확인")
        db_status = server_cost_db_service.get_db_connection_status(db).status
        if db_status != "available":
            logger.warning("DB를 먼저 켜주세요")
            pytest.skip("DB를 먼저 켜주세요")
        logger.info("(1) 완료")

        # 2. 로그인 후 access_token, user_sub, complaint_id 불러오기
        logger.info("(2) 로그인 후 access_token, user_sub, complaint_id 불러오기")
        login_payload = (
            {"email": "test_prod_9090@example.com", "password": "SecurePass123!"}
            if test_target == "prod"
            else {"email": "test_dev_9090@example.com", "password": "SecurePass123!"}
        )
        login_response = client.post(
            _url(base_url, "/api/v1/users/login/email"), json=login_payload
        )
        access_token = login_response.json()["access_token"]

        me_response = client.get(
            _url(base_url, "/api/v1/users/me"),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        me_data = me_response.json()
        user_sub = me_data["user_sub"]
        complaint_id = str(me_data["complaint_id"])

        logger.info("access_token=%s", access_token)
        logger.info("user_sub=%s", user_sub)
        logger.info("complaint_id=%s", complaint_id)
        logger.info("(2) 완료")

        # 3. 기존 데이터 초기화
        logger.info("(3) 기존 데이터 초기화 시작")
        user_repo = UserRepository(db)
        user_repo.delete_by_user_sub(user_sub)
        db.commit()

        delete_s3_objects_by_prefix(settings.S3_BUCKET_NAME, f"{user_sub}/")
        logger.info("(3) 완료")

        # 4. 스토리지 테스트 데이터셋 다운로드
        _download_integration_dataset()

        return {
            "access_token": access_token,
            "user_sub": user_sub,
            "complaint_id": complaint_id,
        }
    finally:
        db.close()
