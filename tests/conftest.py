import logging

import pytest
from fastapi.testclient import TestClient

from app._server_cost.db.service import server_cost_db_service
from app.core.aws import delete_s3_objects_by_prefix
from app.core.database import SessionLocal
from app.core.settings import settings
from app.domain.user import UserRepository
from app.main import app

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def integration_context(client: TestClient) -> dict[str, str]:
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
            if settings.env == "prod"
            else {"email": "test_dev_9090@example.com", "password": "SecurePass123!"}
        )
        login_response = client.post("/api/v1/users/login/email", json=login_payload)
        access_token = login_response.json()["access_token"]

        me_response = client.get(
            "/api/v1/users/me",
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

        return {
            "access_token": access_token,
            "user_sub": user_sub,
            "complaint_id": complaint_id,
        }
    finally:
        db.close()
