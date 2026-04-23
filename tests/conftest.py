import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
import httpx
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app._server_cost.db.service import server_cost_db_service
from app.domain.user import UserRepository

logger = logging.getLogger(__name__)

TEST_ENV_FILE = Path(__file__).resolve().parents[1] / ".env.test"
AWS_REGION = "ap-northeast-2"
INTEGRATION_DATASET_PREFIX = "integration_test_set/"
INTEGRATION_DATASET_DOWNLOAD_DIR = Path(__file__).resolve().parent / "integration_test_set"
DB_CONNECT_TIMEOUT_SECONDS = 5


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--target",
        action="store",
        default="local",
        choices=["local", "dev", "prod"],
        help="integration target environment",
    )


@dataclass
class TestEnvConfig:
    target: str
    values: dict[str, str]

    @classmethod
    def from_request(cls, request: pytest.FixtureRequest) -> "TestEnvConfig":
        target = str(request.config.getoption("--target")).lower()
        values = {k: v for k, v in dotenv_values(TEST_ENV_FILE).items() if k and v is not None}
        return cls(target=target, values=values)

    def database_url(self) -> str:
        return self.values[f"{self.target.upper()}_DATABASE_URL"]

    def s3_bucket_name(self) -> str:
        return self.values[f"{self.target.upper()}_S3_BUCKET_NAME"]

    def base_url(self) -> str | None:
        if self.target == "dev":
            return self.values["DEV_API_SERVER_URL"]
        if self.target == "prod":
            return self.values["PROD_API_SERVER_URL"]
        return None

    def url(self, path: str) -> str:
        base_url = self.base_url()
        if base_url is None:
            return path
        return f"{base_url}{path}"


class S3BucketClient:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com",
        )

    def delete_objects_by_prefix(self, prefix: str) -> None:
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            contents = page.get("Contents", [])
            if not contents:
                continue
            self.client.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in contents], "Quiet": True},
            )

    def paginate_objects(self, prefix: str):
        paginator = self.client.get_paginator("list_objects_v2")
        return paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

    def download_object(self, key: str, local_path: Path) -> None:
        self.client.download_file(self.bucket_name, key, str(local_path))


class IntegrationTestSetup:
    def __init__(self, db: Any, client: Any, config: TestEnvConfig, storage: S3BucketClient):
        self.db = db
        self.client = client
        self.config = config
        self.storage = storage

    def ensure_db_available(self) -> None:
        logger.info("(1) DB 연결 상태 확인")
        db_status = server_cost_db_service.get_db_connection_status(self.db).status
        if db_status != "available":
            logger.warning("DB를 먼저 켜주세요")
            pytest.skip("DB를 먼저 켜주세요")
        logger.info("(1) 완료")

    def fetch_auth_context(self) -> dict[str, str]:
        logger.info("(2) 로그인 후 access_token, user_sub, complaint_id 불러오기")

        login_payload = (
            {"email": "test_prod_9090@example.com", "password": "SecurePass123!"}
            if self.config.target == "prod"
            else {"email": "test_dev_9090@example.com", "password": "SecurePass123!"}
        )
        login_response = self.client.post(
            self.config.url("/api/v1/users/login/email"), json=login_payload
        )
        access_token = login_response.json()["access_token"]

        me_response = self.client.get(
            self.config.url("/api/v1/users/me"),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        me_data = me_response.json()
        user_sub = me_data["user_sub"]
        complaint_id = str(me_data["complaint_id"])

        logger.info("access_token=%s", access_token)
        logger.info("user_sub=%s", user_sub)
        logger.info("complaint_id=%s", complaint_id)
        logger.info("(2) 완료")

        return {
            "access_token": access_token,
            "user_sub": user_sub,
            "complaint_id": complaint_id,
        }

    def reset_existing_data(self, user_sub: str) -> None:
        logger.info("(3) 기존 데이터 초기화 시작")
        user_repo = UserRepository(self.db)
        user_repo.delete_by_user_sub(user_sub)
        self.db.commit()

        self.storage.delete_objects_by_prefix(f"{user_sub}/")
        logger.info("(3) 완료")

    def download_integration_dataset(self) -> None:
        logger.info("(4) 테스트 데이터셋 다운로드 시작")

        if INTEGRATION_DATASET_DOWNLOAD_DIR.exists():
            shutil.rmtree(INTEGRATION_DATASET_DOWNLOAD_DIR)
        INTEGRATION_DATASET_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

        downloaded_count = 0

        for page_index, page in enumerate(
            self.storage.paginate_objects(INTEGRATION_DATASET_PREFIX),
            start=1,
        ):
            page_files = page.get("Contents", [])
            logger.info("(4) 다운로드 진행중 - page=%s, page_files=%s", page_index, len(page_files))

            for obj in page_files:
                key = obj["Key"]
                if key.endswith("/"):
                    continue

                relative_key = key.removeprefix(INTEGRATION_DATASET_PREFIX)
                if not relative_key:
                    continue

                local_path = INTEGRATION_DATASET_DOWNLOAD_DIR / relative_key
                local_path.parent.mkdir(parents=True, exist_ok=True)
                self.storage.download_object(key, local_path)
                downloaded_count += 1

                if downloaded_count % 10 == 0:
                    logger.info("(4) 다운로드 진행중 - downloaded_files=%s", downloaded_count)

            logger.info(
                "(4) 페이지 완료 - page=%s, downloaded_files=%s",
                page_index,
                downloaded_count,
            )

        logger.info(
            "(4) 테스트 데이터셋 다운로드 완료 (files=%s, dir=%s)",
            downloaded_count,
            INTEGRATION_DATASET_DOWNLOAD_DIR,
        )

    def run(self) -> dict[str, str]:
        self.ensure_db_available()
        auth_context = self.fetch_auth_context()
        self.reset_existing_data(auth_context["user_sub"])
        self.download_integration_dataset()
        return auth_context


@pytest.fixture(scope="session")
def test_config(request: pytest.FixtureRequest) -> TestEnvConfig:
    config = TestEnvConfig.from_request(request)
    logger.info("target=%s", config.target)
    return config


@pytest.fixture(scope="session")
def client(test_config: TestEnvConfig) -> Any:
    if test_config.target == "local":
        from app.main import app

        with TestClient(app) as local_client:
            yield local_client
        return

    base_url = test_config.base_url()
    if base_url is None:
        raise ValueError("target must be one of: local, dev, prod")

    with httpx.Client(timeout=30.0) as remote_client:
        remote_client.base_url = httpx.URL(base_url)
        yield remote_client


@pytest.fixture(scope="session")
def integration_context(client: Any, test_config: TestEnvConfig) -> dict[str, str]:
    engine = create_engine(
        test_config.database_url(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": DB_CONNECT_TIMEOUT_SECONDS},
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    storage = S3BucketClient(test_config.s3_bucket_name())
    try:
        logger.info("integration_context 시작")
        test_setup = IntegrationTestSetup(db=db, client=client, config=test_config, storage=storage)
        return test_setup.run()
    finally:
        db.close()
        engine.dispose()
