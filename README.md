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

### Planned

| Category | Technology |
| --- | --- |
| Caching | Redis |
| Testing | pytest |

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

### Stop & Reset

```bash
docker compose down -v
```

- The `-v` option removes volumes and resets the database
- `docker-compose.yml` is located at the project root

---

## 6. Database Migration (Alembic)

### Create a Migration

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

- Generates a migration file based on SQLAlchemy model changes

### Apply Migrations

```bash
poetry run alembic upgrade head
```

- Applies all migrations up to the latest revision

---

## 7. CI / CD Workflows

GitHub Actions is configured with the following workflows.

### On push to `main`

1. Database migration workflow
2. Lambda layer build & deploy
3. Application build & deploy (AWS Lambda)  
   - The application is deployed with the corresponding Lambda layer

### On pull request to `main`

- Application build verification  
  - Ensures the app builds successfully without deployment

---

## 8. Environment Separation Policy

| Environment | Database | Purpose |
| --- | --- | --- |
| Local | Docker (PostgreSQL) | Local development |
| Dev | AWS RDS | Shared development environment |
| Prod | AWS RDS | Production environment |
