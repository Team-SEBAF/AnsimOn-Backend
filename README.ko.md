# 개발 환경 설정 가이드

이 프로젝트는 **FastAPI + Poetry** 기반으로 구성되어 있으며,  
로컬 개발 환경과 AWS 배포 환경(Dev / Prod)을 명확히 분리하여 운영합니다.

---

## 1. 기술 스택

### Application

| 구분 | 기술 |
| --- | --- |
| Framework | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| DB Migration | Alembic |

### Package / Environment

| 구분 | 기술 |
| --- | --- |
| Virtual Environment / Package Manager | Poetry |

### Database

| 구분 | 기술 |
| --- | --- |
| DB Engine | PostgreSQL |
| Local | Docker |
| Dev / Prod | AWS RDS |

### Infrastructure

| 구분 | 기술 |
| --- | --- |
| Server | AWS Lambda |
| Authentication | AWS Cognito |
| Storage | AWS S3 |

### Testing

| 구분 | 기술 |
| --- | --- |
| Framework | pytest |

---

## 2. Poetry 설치

이 프로젝트는 **Poetry 사용을 전제로 합니다.**

### macOS / Linux

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

설치 후 경로가 적용되지 않았다면 아래를 실행합니다.

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows (PowerShell)

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

설치 확인:

```bash
poetry --version
```

---

## 3. 의존성 설치 및 가상환경 설정

프로젝트 루트에서 아래 명령어를 실행합니다.

```bash
poetry install
```

- `pyproject.toml` 기준으로 의존성이 설치됩니다.
- Poetry가 자동으로 가상환경을 생성합니다.

---

## 4. 로컬 서버 실행

FastAPI 개발 서버는 아래 명령어로 실행합니다.

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

- `--reload`: 코드 변경 시 서버 자동 재시작
- 접속 주소: http://localhost:8000

---

## 5. Docker (Local DB) 설정

로컬 개발 환경에서는 **Docker 기반 PostgreSQL**을 사용합니다.

### 사전 준비
- Docker Desktop 설치 필요

### 실행

```bash
docker compose up -d
```

### 종료

```bash
docker compose down
```

### 초기화

```bash
docker compose down -v
```

- `-v` 옵션은 볼륨까지 제거하여 DB를 초기화합니다.
- `docker-compose.yml`은 프로젝트 루트에 위치합니다.

### DB Migration (로컬용)

로컬에서만 사용합니다. Dev/Prod 환경은 CI/CD에서 자동 적용됩니다.

**Migration 생성**

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

- SQLAlchemy 모델 변경 사항을 기반으로 migration 파일을 생성합니다.

**Migration 적용**

```bash
poetry run alembic upgrade head
```

- 최신 migration까지 DB에 반영합니다.

---

## 6. 테스트 명령어

프로젝트 루트에서 아래 명령어로 테스트를 실행합니다.

```bash
poetry run pytest --target local
```

로그까지 확인하려면:

```bash
poetry run pytest --target local --log-cli-level=INFO
```

특정 파일만 실행하려면:

```bash
poetry run pytest --target local tests/test_integration_setup.py
```

Dev/Prod 리소스를 대상으로 실행하려면:

```bash
AWS_PROFILE=ansimon-dev-local poetry run pytest --target dev
AWS_PROFILE=ansimon-dev-local poetry run pytest --target prod
```

---

## 7. CI / CD 워크플로

GitHub Actions로 다음 워크플로가 구성되어 있습니다.

### dev 브랜치 push 시

1. **DB Migrate** (`db-migrate.yml`)
   - Alembic migration 자동 적용 (Dev/Prod는 `workflow_dispatch`로 대상 선택)

2. **Deploy Lambda** (`lambda-deploy.yml`)
   - Lambda 함수 코드 업데이트
   - 버전 퍼블리시 및 alias 업데이트 (`dev` / `prod`)

### dev 브랜치 PR 시

- **PR Check** (`pr-check.yml`)
  - Lambda 패키지(app 디렉터리) 빌드 검증
  - 실제 배포 없이 zip 생성 여부만 확인

### 수동 실행 (workflow_dispatch)

- **Deploy Lambda Layer** (`lambda-layer-deploy.yml`)
  - `pyproject.toml` 기준 requirements 추출 → Lambda Layer 빌드 → 업로드
  - 의존성 변경 시 수동 실행 후 Lambda Deploy 수행
