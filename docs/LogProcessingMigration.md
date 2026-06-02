# Log Processing System Migration

## Goal

Convert the current TXT file processing system into a log processing and observability-style system.

The final system should accept log files, process them in the background, and generate useful operational insights such as counts, severity summaries, error patterns, and other observability signals.

## Working Strategy

Each step should follow this rule:

1. Do one thing.
2. Keep the system working.
3. Make the change commit-worthy.
4. Teach one concept.

## How Each Step Will Be Documented

For every incremental step, this file will be updated with:

- Step name
- What the step is going to do
- What was already present in the system
- What needed to change
- Files changed
- How to test the step
- Concept learned

## Current System Baseline

The current project is a Dockerized background file processing system.

### Existing Capabilities

- Flask API accepts uploaded `.txt` files.
- Uploaded files are saved to a shared `uploads` directory.
- A `FileJob` database record is created for each upload.
- Redis Queue stores background jobs.
- A worker container processes queued jobs asynchronously.
- PostgreSQL stores job metadata, status, counts, retry count, and errors.
- Dashboard displays processed file results.
- Worker heartbeat can be checked through a debug route.
- Scheduler can mark stuck processing jobs as failed.

### Current Processing Output

The current worker extracts basic text-file statistics:

- Word count
- Line count
- Character count

### Target Direction

The system will move from generic text statistics toward log observability insights, such as:

- Total log lines
- Log level counts
- Error count
- Warning count
- Most common error messages
- Time range covered by the log file
- Failed or malformed line count
- Basic health/status summary

## Step Log

### Step 1 - Project Cleanup

#### Goal

Clean the project folders and structure before converting the system from generic file processing into log processing.

#### What Was Already Present

- Routes were already inside `app/routes`.
- Models were already inside `app/models`.
- Background processing already existed through Redis Queue and a worker.
- The active file-processing database model already existed as `FileJob`.

#### What Needed To Change

- Some files still had old names from previous versions of the project:
  - `app/routes/tasks.py` was no longer about tasks.
  - `app/routes/upload_routes.py` handled all file job APIs but had an upload-only name.
  - `app/jobs.py` mixed processing logic and reporting logic in one file.
  - `app/models/task.py` and `app/models/user.py` were legacy models not used by the current file-processing system.

#### Changes Made

- Replaced `app/routes/tasks.py` with `app/routes/system_routes.py`.
- Replaced `app/routes/upload_routes.py` with `app/routes/file_routes.py`.
- Converted `app/jobs.py` into an `app/jobs` package.
- Added `app/jobs/file_processing.py` for background file processing and retry handling.
- Added `app/jobs/reports.py` for report generation jobs.
- Added `app/jobs/__init__.py` to keep imports simple.
- Removed legacy `Task` and `User` model imports from `app/main.py`.
- Deleted legacy model files:
  - `app/models/task.py`
  - `app/models/user.py`

#### Files Changed

- `app/main.py`
- `app/routes/system_routes.py`
- `app/routes/file_routes.py`
- `app/jobs/__init__.py`
- `app/jobs/file_processing.py`
- `app/jobs/reports.py`
- `app/models/task.py`
- `app/models/user.py`
- `docs/LogProcessingMigration.md`

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Check the main routes:

```bash
curl http://localhost:5000/
curl http://localhost:5000/files
curl http://localhost:5000/debug/workers
```

Upload a text file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

#### Concept Learned

Project structure should follow responsibility, not history.

This step did not add new log-processing behavior. It made the code easier to extend by giving each part a clear place:

- Route files handle HTTP endpoints.
- Model files define database tables.
- Job files hold background work.
- Utility files hold shared helper logic.

This keeps future changes smaller, safer, and easier to explain.

### Step 2 - Add Environment Variables

#### Goal

Remove hardcoded configuration values from the application and Docker Compose setup.

#### What Was Already Present

- `DATABASE_URL` was already read with `os.getenv` in `app/main.py`.
- `REDIS_URL` was already read with `os.getenv` in `app/extensions.py`.
- `UPLOAD_FOLDER` was already read with `os.getenv` in `app/routes/file_routes.py`.
- `.env` was already listed in `.gitignore`, which is good because local environment files should not usually be committed.

#### What Needed To Change

- Environment variable access was scattered across multiple files.
- `docker-compose.yml` still had `DATABASE_URL` and `REDIS_URL` hardcoded inside service definitions.
- There was no `.env.example` file showing required environment variables.
- Local Python runs would not automatically load `.env` without dotenv support.

#### Changes Made

- Added `app/config.py` as the central config module.
- Moved application config reads into `app/config.py`:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `UPLOAD_FOLDER`
- Updated `app/main.py` to use `DATABASE_URL` from config.
- Updated `app/extensions.py` to use `REDIS_URL` from config.
- Updated `app/routes/file_routes.py` to use `UPLOAD_FOLDER` from config.
- Updated `docker-compose.yml` so API and worker use `env_file: .env`.
- Made the shared uploads volume configurable:
  - `HOST_UPLOAD_FOLDER`
  - `UPLOAD_FOLDER`
- Added local `.env`.
- Added committed `.env.example`.
- Added `python-dotenv` to `requirements.txt`.

#### Files Changed

- `app/config.py`
- `app/main.py`
- `app/extensions.py`
- `app/routes/file_routes.py`
- `docker-compose.yml`
- `.env`
- `.env.example`
- `requirements.txt`
- `docs/LogProcessingMigration.md`

#### Environment Variables

```env
DATABASE_URL=postgresql://postgres:password@db:5432/tasks
REDIS_URL=redis://redis:6379/0
UPLOAD_FOLDER=/app/uploads
HOST_UPLOAD_FOLDER=./uploads
```

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the full system:

```bash
docker compose up -d --build
```

Check that the API can still reach Redis and Postgres:

```bash
curl http://localhost:5000/
curl http://localhost:5000/files
```

Upload a file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

#### Concept Learned

Configuration should live outside the code.

Hardcoding values like database URLs, Redis URLs, and filesystem paths makes deployment harder because every environment may need different values. A config module plus `.env` keeps code stable while allowing local, Docker, VM, and production environments to provide different settings.

### Step 3 - Add Proper Logging

#### Goal

Replace print-style debugging with Python logging and make the key runtime events visible.

#### What Was Already Present

- `app/utils/logger.py` already configured Python logging with `logging.basicConfig`.
- `log_message()` already existed as a small helper for consistent log messages.
- Worker processing already logged:
  - file processing started
  - file processing completed
  - retry queued
  - permanent failure
- Scheduler already used Python logging.

#### What Needed To Change

- `print()` was still used in `app/main.py` for startup and database connection messages.
- `print()` was still used in `app/worker.py` for heartbeat messages.
- Upload flow did not log when an upload started.
- Upload flow did not log when a background job was queued.
- Upload validation failures were returned to the client but not logged.
- All `log_message()` calls used info-level logging only, so failures could not be marked as warnings or errors.

#### Changes Made

- Updated `app/utils/logger.py`:
  - formatted the helper cleanly
  - added a `level` parameter
  - kept existing `task_id`, `user_id`, and `file_job_id` support
- Updated `app/routes/file_routes.py`:
  - logs upload started
  - logs job queued with RQ job ID and file job ID
  - logs missing file upload as warning
  - logs empty filename as warning
  - logs unsupported file type as warning
- Rewrote `app/main.py` startup messages to use `log_message()` instead of `print()`.
- Updated `app/worker.py`:
  - logs worker startup
  - logs heartbeat through Python logging instead of `print()`
- Updated `app/jobs/file_processing.py`:
  - logs processing failures as `ERROR`
  - logs retry queueing as `WARNING`
  - logs permanent failure as `ERROR`

#### Files Changed

- `app/utils/logger.py`
- `app/routes/file_routes.py`
- `app/jobs/file_processing.py`
- `app/main.py`
- `app/worker.py`
- `docs/LogProcessingMigration.md`

#### Events Now Logged

- API app startup
- Database connection success
- Database retry attempts
- Upload started
- Upload validation failures
- Background job queued
- Worker startup
- Worker heartbeat
- Worker processing started
- Worker processing completed
- Worker processing failure
- Retry queued
- Permanent failure

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Watch logs:

```bash
docker compose logs -f api
docker compose logs -f worker
```

Upload a valid file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

Upload an invalid file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@bad.csv"
```

#### Concept Learned

Logging is not just printing text. Good application logging records important system events with severity levels:

- `INFO` for normal events
- `WARNING` for recoverable or invalid situations
- `ERROR` for failed operations

This makes the system easier to debug locally and easier to operate later as an observability-style log processing system.

### Step 4 - Add Timestamps

#### Goal

Track the lifecycle of each background job.

#### Requested Fields

- `started_at`
- `completed_at`

#### What Was Already Present

The requested database fields already existed in `app/models/file_job.py`:

```python
started_at = db.Column(db.DateTime, nullable=True)
completed_at = db.Column(db.DateTime, nullable=True)
```

The API response already exposed both fields through `FileJob.to_dict()`.

The worker already set `started_at` when processing began:

```python
file_job.started_at = datetime.utcnow()
```

The worker already set `completed_at` when processing completed successfully:

```python
file_job.completed_at = datetime.utcnow()
```

The worker and scheduler also already set `completed_at` for terminal failure states.

#### What Needed To Change

The timestamp fields existed, but the dashboard did not show them. That made the lifecycle harder to inspect during local testing and demos.

#### Changes Made

- Updated `app/templates/dashboard.html`.
- Added `Started At` column.
- Added `Completed At` column.

#### Files Changed

- `app/templates/dashboard.html`
- `docs/LogProcessingMigration.md`

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Upload a file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

Check the API result:

```bash
curl http://localhost:5000/files/1
```

Open the dashboard:

```text
http://localhost:5000/dashboard
```

Expected lifecycle:

- `created_at` is set when the job row is created.
- `started_at` is set when the worker starts processing.
- `completed_at` is set when the job reaches a terminal state such as `completed` or `failed`.

#### Concept Learned

Timestamps turn a background job into an observable lifecycle.

Without timestamps, a status only tells what state the job is in. With timestamps, we can answer better operational questions:

- When was the job created?
- When did processing actually start?
- How long did it wait in the queue?
- How long did processing take?
- When did it finish or fail?

### Step 5 - Add Processing Duration

#### Goal

Measure worker performance by storing how long each job spent inside worker processing.

#### Requested Field

- `processing_time`

#### What Was Already Present

- `started_at` already existed.
- `completed_at` already existed.
- The worker already set both timestamps during the job lifecycle.
- The dashboard already showed `Started At` and `Completed At` after Step 4.

#### What Needed To Change

The system could show when processing started and ended, but it did not store the calculated duration. Anyone reading the API or dashboard had to calculate the duration manually.

#### Changes Made

- Added `processing_time` to `FileJob`.
- Added `processing_time` to `FileJob.to_dict()` so API responses include it.
- Added duration calculation in the worker:
  - successful completion
  - permanent failure
- Added duration calculation in the scheduler when stale jobs time out.
- Added `Processing Time` column to the dashboard.
- Updated worker completion logs to include processing time.

#### Files Changed

- `app/models/file_job.py`
- `app/jobs/file_processing.py`
- `app/utils/task_service.py`
- `app/templates/dashboard.html`
- `docs/LogProcessingMigration.md`

#### How Processing Time Is Calculated

```python
processing_time = (completed_at - started_at).total_seconds()
```

The value is rounded to 3 decimal places and stored in seconds.

This measures worker execution time, not queue wait time.

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Upload a file:

```bash
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

Check the result:

```bash
curl http://localhost:5000/files/1
```

Expected response includes:

```json
"processing_time": 0.123
```

Open the dashboard:

```text
http://localhost:5000/dashboard
```

Expected dashboard includes a `Processing Time` column.

#### Concept Learned

Processing duration is a basic performance metric.

Timestamps tell when lifecycle events happened. Duration turns those timestamps into a measurable performance signal. In an observability-style system, this is the beginning of metrics such as latency, throughput, slow jobs, and worker performance trends.

## Stage 2 - Real Log Processing

At this stage, the system identity changes from generic text-file processing toward real log processing.

### Step 6 - Add Sample Nginx Log Support

#### Goal

Upload real logs into the system.

#### What Was Already Present

- The upload route already accepted text-like files.
- Uploaded files were already saved to the configured upload folder.
- A `FileJob` row was already created for every upload.
- Redis Queue already handled background processing.
- The worker already processed uploaded file contents asynchronously.

#### What Needed To Change

- The system only accepted `.txt` files.
- There was no committed real-world log sample for testing or demos.
- The root API response still identified the app as a TXT file processing API.

#### Changes Made

- Added a committed sample nginx access log:
  - `samples/nginx_access.log`
- Updated upload validation to accept:
  - `.txt`
  - `.log`
- Updated unsupported upload error message to mention `.txt` and `.log`.
- Updated the root route message to identify the service as a Log Processing API.

#### Files Changed

- `samples/nginx_access.log`
- `app/routes/file_routes.py`
- `app/routes/system_routes.py`
- `docs/LogProcessingMigration.md`

#### Sample Log Details

The sample nginx log includes realistic access-log lines with several HTTP outcomes:

- `200` successful requests
- `302` redirect
- `401` unauthorized
- `403` forbidden
- `404` not found
- `500` server error
- `504` gateway timeout

This gives the next steps useful data for observability insights.

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Check system identity:

```bash
curl http://localhost:5000/
```

Upload the sample nginx log:

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
```

Check the job:

```bash
curl http://localhost:5000/files
```

#### Concept Learned

Representative sample data makes a system easier to evolve.

Before adding parsing logic, the project needs a stable real log file that can be used repeatedly for testing. This keeps future parser and insight changes grounded in realistic input instead of imaginary strings.

### Step 7 - Parse Status Codes

#### Goal

Extract HTTP status code counts from nginx access logs.

#### Requested Status Codes

- `200`
- `404`
- `500`

#### What Was Already Present

- The worker already opened and read uploaded file content.
- The sample nginx log already contained `200`, `404`, and `500` responses.
- The system already stored job results in `FileJob`.
- The dashboard already displayed processing results.

#### What Needed To Change

The system processed logs as plain text only. It did not understand nginx access log structure, so it could not extract HTTP status codes.

#### Changes Made

- Added status-code fields to `FileJob`:
  - `status_200_count`
  - `status_404_count`
  - `status_500_count`
- Added those fields to `FileJob.to_dict()` so API responses include them.
- Added nginx status-code parsing in the worker.
- Added dashboard columns for:
  - `200`
  - `404`
  - `500`

#### Files Changed

- `app/models/file_job.py`
- `app/jobs/file_processing.py`
- `app/templates/dashboard.html`
- `docs/LogProcessingMigration.md`

#### Parser Rule

Nginx access logs commonly place the status code immediately after the quoted request:

```text
"GET /api/orders HTTP/1.1" 500 128
```

The worker uses this pattern:

```python
r'"\s(?P<status_code>\d{3})\s'
```

For this step, the parser only counts `200`, `404`, and `500`.

#### Expected Counts For Sample Log

Using `samples/nginx_access.log`, expected values are:

```text
200: 4
404: 1
500: 1
```

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Because this step adds database columns, reset the local dev database volume if you are not using migrations:

```bash
docker compose down -v
docker compose up -d --build
```

Upload the sample nginx log:

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
```

Check the result:

```bash
curl http://localhost:5000/files/1
```

Expected response includes:

```json
"status_200_count": 4,
"status_404_count": 1,
"status_500_count": 1
```

#### Concept Learned

Parsing turns raw logs into structured signals.

Before this step, the worker only produced generic text statistics. Now it extracts operational meaning from the log format. This is the beginning of observability: turning raw events into queryable metrics.

### Step 8 - Count Errors

#### Goal

Calculate error totals from parsed HTTP status codes.

#### Requested Metrics

- Total errors
- 4xx errors
- 5xx errors

#### Step Separation

Steps 8, 9, and 10 are separate steps:

- Step 8 counts error categories.
- Step 9 extracts unique client IP addresses.
- Step 10 extracts and ranks requested endpoints.

They should be implemented separately because each one teaches a different observability concept.

#### What Was Already Present

- Step 7 already parsed HTTP status codes from nginx access logs.
- The worker already counted specific status codes:
  - `200`
  - `404`
  - `500`
- `FileJob` already stored parsed status-code metrics.
- The dashboard already displayed status-code counts.

#### What Needed To Change

The system could count specific codes, but it did not summarize error categories. Observability systems usually group status codes because categories are easier to reason about:

- `4xx` means client-side or request problems.
- `5xx` means server-side or upstream problems.

#### Changes Made

- Added error fields to `FileJob`:
  - `total_error_count`
  - `client_error_count`
  - `server_error_count`
- Added those fields to `FileJob.to_dict()`.
- Updated the worker parser to count:
  - all `400-499` responses as client errors
  - all `500-599` responses as server errors
  - both categories together as total errors
- Added dashboard columns:
  - `Total Errors`
  - `4xx`
  - `5xx`

#### Files Changed

- `app/models/file_job.py`
- `app/jobs/file_processing.py`
- `app/templates/dashboard.html`
- `docs/LogProcessingMigration.md`

#### Expected Counts For Sample Log

Using `samples/nginx_access.log`, expected values are:

```text
total errors: 5
4xx: 3
5xx: 2
```

The sample has:

- `401`
- `403`
- `404`
- `500`
- `504`

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Because this step adds database columns, reset the local dev database volume if you are not using migrations:

```bash
docker compose down -v
docker compose up -d --build
```

Upload the sample nginx log:

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
```

Check the result:

```bash
curl http://localhost:5000/files/1
```

Expected response includes:

```json
"total_error_count": 5,
"client_error_count": 3,
"server_error_count": 2
```

#### Concept Learned

Error categories are higher-level signals than individual status codes.

Specific codes are useful for detail, but categories make operational health easier to understand quickly. A rising `5xx` count usually means the system or upstream service is unhealthy, while a rising `4xx` count often points to invalid requests, authentication problems, missing resources, or client misuse.
