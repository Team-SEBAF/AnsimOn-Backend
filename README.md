# Development Environment Setup Guide

This project is built with **FastAPI + Poetry** and clearly separates  
local development and AWS deployment environments (Dev / Prod).

---

## 1. Tech Stack

### Application

| Category | Technology |
| --- | --- |
| Framework | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| DB Migration | Alembic |

### Package / Environment

| Category | Technology |
| --- | --- |
| Virtual Environment / Package Manager | Poetry |

### Database

| Category | Technology |
| --- | --- |
| DB Engine | PostgreSQL |
| Local | Docker |
| Dev / Prod | AWS RDS |

### Infrastructure

| Category | Technology |
| --- | --- |
| Server | AWS Lambda |
| Authentication | AWS Cognito |
| Storage | AWS S3 |

### Testing

| Category | Technology |
| --- | --- |
| Framework | pytest |

---

## 2. Installing Poetry

This project **requires Poetry**.

### macOS / Linux

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

If the command is not found after installation, add Poetry to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows (PowerShell)

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Verify installation:

```bash
poetry --version
```

---

## 3. Installing Dependencies

Run the following command at the project root:

```bash
poetry install
```

- Dependencies are installed based on `pyproject.toml`
- Poetry automatically creates and manages the virtual environment

---

## 4. Running the Local Server

Start the FastAPI development server with:

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

- `--reload`: Automatically restarts the server on code changes  
- URL: http://localhost:8000

---

## 5. Docker (Local Database Setup)

For local development, PostgreSQL is provided via Docker.

### Prerequisites
- Docker Desktop must be installed

### Start

```bash
docker compose up -d
```

### Stop

```bash
docker compose down
```

### Reset

```bash
docker compose down -v
```

- The `-v` option removes volumes and resets the database
- `docker-compose.yml` is located at the project root

### Database Migration (Local Only)

Used for local development. Dev/Prod environments run migrations via CI/CD.

**Create a Migration**

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

- Generates a migration file based on SQLAlchemy model changes

**Apply Migrations**

```bash
poetry run alembic upgrade head
```

- Applies all migrations up to the latest revision

---

## 6. Test Commands

Run tests from the project root:

```bash
poetry run pytest --target local
```

Run with logs:

```bash
poetry run pytest --target local --log-cli-level=INFO
```

Run only a specific file:

```bash
poetry run pytest --target local tests/test_evidence_upload.py
```

Run against Dev/Prod resources:

```bash
AWS_PROFILE=ansimon-dev-local poetry run pytest --target dev
AWS_PROFILE=ansimon-dev-local poetry run pytest --target prod
```

---

## 7. CI / CD Workflows

GitHub Actions workflows:

### On push to `dev`

1. **DB Migrate** (`db-migrate.yml`)
   - Applies Alembic migrations
   - Use `workflow_dispatch` to target Dev or Prod

2. **Deploy Lambda** (`lambda-deploy.yml`)
   - Updates Lambda function code
   - Publishes version and updates alias (`dev` / `prod`)

### On pull request to `dev`

- **PR Check** (`pr-check.yml`)
  - Validates Lambda package (app directory) build
  - Builds zip without deploying

### Manual (workflow_dispatch)

- **Deploy Lambda Layer** (`lambda-layer-deploy.yml`)
  - Extracts requirements from `pyproject.toml` → builds Lambda Layer → uploads
  - Run manually when dependencies change, then run Lambda Deploy
