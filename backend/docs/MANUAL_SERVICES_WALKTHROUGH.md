# Manual walkthrough: backend sub-services

This doc explains what each sub-service does and how to run it **manually** so you can see the flow and verify things work.

---

## Prerequisites

Before running any of this:

1. **Postgres** – running and reachable (e.g. `psql -h 127.0.0.1 -p 5432 -U mike -d tee_time_db`).
2. **Redis** – running on `localhost:6379` (config in `app/config.py`: `redis_url`).
3. **Backend venv** – use the project venv for all commands:
   ```bash
   cd ~/Documents/tee-time-watcher/backend
   source .venv/bin/activate
   ```
   Or run the venv’s Python explicitly: `./.venv/bin/python -m app.scheduler` (no need to `source`).

---

## 1. API server (optional for this walkthrough)

**What it does:** Serves HTTP: auth, courses, watch-rules, bookings, notifications. Also creates DB tables on startup (`Base.metadata.create_all`).

**Run:**
```bash
cd ~/Documents/tee-time-watcher/backend
./run
# or: ./.venv/bin/uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'
```

**Verify:** Open http://127.0.0.1:8000/health → `{"status":"ok"}`.  
Tables exist after at least one successful API startup.

---

## 2. Scheduler (one-shot)

**What it does:**  
Reads all **watch rules** from the DB. For each rule that is **due** (active and past its `scan_interval_seconds` since last run), it **enqueues one scan job** into Redis (priority queue) and creates a **ScanJob** row in Postgres with status `PENDING`.  
It does **not** perform any scanning or booking itself; it only enqueues work.

**Run once:**
```bash
cd ~/Documents/tee-time-watcher/backend
source .venv/bin/activate
python -m app.scheduler
```

**What you should see:**  
No output if everything is OK (no errors). If you have no watch rules, it simply does nothing. If you have due rules, it enqueues jobs and inserts rows into `scan_jobs`.

**How to verify:**

- **Postgres:** After running with at least one due watch rule, check that new rows appeared:
  ```bash
  psql -h 127.0.0.1 -p 5432 -U mike -d tee_time_db -c "SELECT id, watch_rule_id, status FROM scan_jobs ORDER BY id DESC LIMIT 5;"
  ```
  You should see rows with `status = 'PENDING'` (or later `IN_PROGRESS` / `DONE` / `FAILED` after the worker runs).

- **Redis:** The queue key is `scan_jobs` (sorted set). Check that items were added:
  ```bash
  redis-cli ZCARD scan_jobs
  ```
  After a scheduler run with due rules, this should be &gt; 0 (until the worker consumes them).

**Typical flow:** You need at least one **user**, one **course**, and one **watch_rule** (e.g. created via API or seed script). Then run the scheduler; it will enqueue one job per due rule.

---

## 3. Worker (consumes scan jobs)

**What it does:**  
Polls Redis for the next scan job (by priority), dequeues it, loads the corresponding **ScanJob** from Postgres, and **processes** it: loads the WatchRule and Course, uses the **DemoCourseAdapter** to “search” tee times (demo implementation), optionally auto-books if the user has credentials and the slot is free. Updates the **ScanJob** to `IN_PROGRESS` then `DONE` or `FAILED`, and writes **TeeTimeCandidate** and possibly **Booking** rows.

**Run once (process a single job and exit):**
```bash
cd ~/Documents/tee-time-watcher/backend
source .venv/bin/activate
python -m app.worker
```

**Current behavior:** The worker module is written so that `python -m app.worker` runs **one** job and exits. If the queue is empty, it exits silently. If a job was processed, you’ll see log output from the app.

**What you should see:**  
- If queue empty: process exits with no output (or a single log line).  
- If a job was dequeued: logs about processing the job; the corresponding `scan_jobs` row moves to `DONE` or `FAILED`, and you may see new rows in `tee_time_candidates` or `bookings`.

**How to verify:**

- **Postgres:** After running the worker with a job in the queue:
  ```bash
  psql -h 127.0.0.1 -p 5432 -U mike -d tee_time_db -c "SELECT id, watch_rule_id, status, started_at, finished_at FROM scan_jobs ORDER BY id DESC LIMIT 5;"
  ```
  Processed jobs should have `status = 'DONE'` or `'FAILED'` and `started_at` / `finished_at` set.

- **Redis:** One job was removed from the queue:
  ```bash
  redis-cli ZCARD scan_jobs
  ```
  Count decreases by one per job processed.

**End-to-end manual test:**

1. Start Postgres and Redis.
2. Start the API once so tables exist (then you can stop it): `./run` then Ctrl+C.
3. Create a user, a course, and a watch rule (via API or SQL).
4. Run the scheduler once: `python -m app.scheduler`.
5. Check the `scan_jobs` table in Postgres and the `scan_jobs` key in Redis (see above).
6. Run the worker once: `python -m app.worker`.
7. Check `scan_jobs` again (status DONE/FAILED) and optionally `tee_time_candidates` / `bookings`.

---

## Summary

| Service   | Command                    | Role |
|----------|----------------------------|------|
| API      | `./run`                     | HTTP API + create tables |
| Scheduler| `python -m app.scheduler`   | One-shot: enqueue due watch rules into Redis + create ScanJob rows |
| Worker   | `python -m app.worker`      | One-shot: dequeue one job, run DemoCourseAdapter, update ScanJob and DB |

Dependencies: **Queue** = Redis (`scan_jobs` sorted set). **State** = Postgres (users, courses, watch_rules, scan_jobs, tee_time_candidates, bookings).
