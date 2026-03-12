# Tee Time Watcher Backend

FastAPI backend for scanning golf course tee times, auto-booking when allowed, and managing user bookings and priorities.

## Quickstart

1. Create and activate a virtual environment, then install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # on Windows use .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Start a local Postgres and Redis instance, and update `app/config.py` with the correct connection URLs.

3. Run the API with:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with docs at `/docs`.

