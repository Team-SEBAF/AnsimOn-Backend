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

### Planned

| 구분 | 기술 |
| --- | --- |
| Caching | Redis |
| Test | pytest |

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

### 종료 및 초기화

```bash
docker compose down -v
```

- `-v` 옵션은 볼륨까지 제거하여 DB를 초기화합니다.
- `docker-compose.yml`은 프로젝트 루트에 위치합니다.

---

## 6. DB Migration (Alembic)

### Migration 생성

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

- SQLAlchemy 모델 변경 사항을 기반으로 migration 파일을 생성합니다.

### Migration 적용

```bash
poetry run alembic upgrade head
```

- 최신 migration까지 DB에 반영합니다.

---

## 7. CI / CD 워크플로

GitHub Actions를 통해 다음과 같은 워크플로가 구성되어 있습니다.

### main 브랜치 push 시

1. DB Migration Workflow 실행
2. Lambda Layer Build & Deploy
3. Application Build & Deploy (AWS Lambda)
   - Layer와 Application이 연결되어 배포됩니다.

### main 브랜치 PR 시

- Application Build 검증
  - 실제 배포 없이 빌드 단계만 확인합니다.

---

## 8. 환경 분리 정책

| 환경 | DB | 실행 목적 |
| --- | --- | --- |
| Local | Docker (PostgreSQL) | 로컬 개발 |
| Dev | AWS RDS | 개발 공용 환경 |
| Prod | AWS RDS | 운영 환경 |
