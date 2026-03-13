# Tee Time Watcher — Install & setup

This document records **every install and setup command** needed so others can run the project from a clean machine. Add new steps here as you run them.

---

## Prerequisites

- **Python** 3.10+ (backend)
- **PostgreSQL** (database)
- **Redis** (job queue; used by backend)
- **macOS:** Xcode Command Line Tools (for Homebrew builds); Homebrew optional but used below for Redis/Postgres

---

## 1. System / CLI tools (macOS)

If Homebrew or other build tools fail with “active developer path does not exist” or compiler errors, point the system at the Command Line Tools (not full Xcode):

```bash
sudo xcode-select --switch /Library/Developer/CommandLineTools
```

To (re)install Command Line Tools:

```bash
xcode-select --install
```

*(If you see “command line tools are already installed”, use **Software Update** in System Settings to get the latest, or follow the message to remove and reinstall.)*

---

## 2. PostgreSQL

Install and run Postgres. Example on macOS with Homebrew:

```bash
brew install postgresql@16
brew services start postgresql@16
```

Create the database and user (adjust user/password/db name to match `backend/app/config.py` or your `.env`):

```bash
createuser -s postgres  # if needed
createdb tee_time_db
# If you use a specific user (e.g. mike):
# createuser -P mike
# psql -c "CREATE DATABASE tee_time_db OWNER mike;"
```

---

## 3. Redis

Install and start Redis. On macOS with Homebrew:

```bash
brew install redis
brew services start redis
```

Run these as **separate** commands. Do not chain with `&&` if your shell or script expects one command per step.

Verify Redis is listening:

```bash
redis-cli ping
# PONG
```

---

## 4. Backend (Python)

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional: if you use a `.env` in `backend/`, create it and set at least:

- `database_url` (e.g. `postgresql+psycopg://user:password@127.0.0.1:5432/tee_time_db`; encode `@` in password as `%40`)
- `redis_url` (e.g. `redis://localhost:6379/0`)
- `jwt_secret_key`, `credential_encryption_key` for production

---

## 5. Database schema

The FastAPI app creates tables on startup (`Base.metadata.create_all`). If you use Alembic instead, from `backend/` with the venv activated:

```bash
alembic upgrade head
```

*(Add the exact `alembic` commands here when you run them.)*

---

## 6. Run the backend

With Postgres and Redis running, from `backend/` with the venv activated:

```bash
uvicorn app.main:app --reload
```

API: `http://localhost:8000` — docs at `/docs`.

For scheduler, worker, and other services see `backend/README.md` and `backend/docs/MANUAL_SERVICES_WALKTHROUGH.md`.

---

## Summary of install commands (copy‑paste)

```bash
# macOS: fix CLI tools if needed
sudo xcode-select --switch /Library/Developer/CommandLineTools

# Postgres
brew install postgresql@16
brew services start postgresql@16
createdb tee_time_db

# Redis
brew install redis
brew services start redis

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Then configure .env and run:
# uvicorn app.main:app --reload
```

---

*Last updated from project setup and terminal history. When you run new install or setup commands, add them here so others can run the project.*
