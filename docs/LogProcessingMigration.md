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

### Step 9 - Extract Unique Client IPs

#### Goal

Identify all unique client IP addresses from nginx access logs and count how many distinct clients made requests.

#### Requested Metrics

- `unique_client_count` — total number of distinct IP addresses
- `unique_client_ips` — comma-separated list of all unique IP addresses

#### What Was Already Present

- The worker already parsed nginx log lines for status codes.
- The `NGINX_CLIENT_IP_PATTERN` regex already extracted the first token of each line as a client IP.
- `FileJob` already had `unique_client_count` and `unique_client_ips` fields.
- The dashboard already displayed a `Unique Clients` column.

#### What Needed To Change

The code already implemented the extraction logic but the migration document had not recorded it. This step completes the documentation gap.

#### How Client IP Extraction Works

Nginx access logs place the client IP as the first token of each line:

```text
192.168.1.10 - - [02/Jun/2026:08:15:01 +0000] "GET / HTTP/1.1" 200 612
```

The worker uses this pattern:

```python
NGINX_CLIENT_IP_PATTERN = re.compile(r"^(?P<client_ip>\S+)\s")
```

For each line, the worker:
1. Extracts the IP address.
2. Adds it to a `set()` to ensure uniqueness.
3. Sorts the final list alphabetically.
4. Stores the count and the comma-separated list.

#### Expected Results For Sample Log

Using `samples/nginx_access.log`, expected values are:

```text
unique_client_count: 10
unique_client_ips: ["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15", "192.168.1.16", "192.168.1.17", "192.168.1.18", "192.168.1.19"]
```

#### Files Changed

- `app/models/file_job.py` — fields already existed
- `app/jobs/file_processing.py` — extraction logic already existed
- `app/templates/dashboard.html` — column already existed
- `docs/LogProcessingMigration.md` — this documentation added

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

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
"unique_client_count": 10,
"unique_client_ips": ["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15", "192.168.1.16", "192.168.1.17", "192.168.1.18", "192.168.1.19"]
```

#### Concept Learned

Unique client identification is a fundamental observability signal.

Knowing how many distinct clients hit a service helps answer operational questions:
- Is the traffic coming from many sources or one aggressive client?
- Are there repeated failed requests from the same IP (potential attack or misconfigured client)?
- Can we correlate errors with specific client patterns?

This is the beginning of traffic-source analysis and security observability.




### Step 10 - Extract and Rank Requested Endpoints

#### Goal

Parse HTTP method and endpoint (URI path) from each nginx log line, count how often each endpoint is requested, and surface the most frequently hit endpoints.

#### Requested Metrics

- `total_endpoints` — number of unique endpoint + method combinations found
- `top_endpoints` — ranked list of the most frequently requested endpoints, including HTTP method, path, and hit count

#### What Was Already Present

- The worker already parsed nginx log lines for status codes and client IPs.
- `FileJob` already stored status counts, error categories, and client IP data.
- The dashboard already displayed all existing metrics in a tabular format.
- The API already returned structured JSON for every job.

#### What Needed To Change

The system could count status codes and identify clients, but it could not answer the question: *Which endpoints are being hit the most?* This is a core observability signal for traffic analysis, capacity planning, and identifying hot paths or potential abuse.

#### Changes Made

- Added endpoint ranking fields to `FileJob`:
  - `total_endpoints` — integer count of unique endpoints
  - `top_endpoints` — JSON text storing the ranked list
- Added endpoint extraction and ranking logic in the worker:
  - New regex `NGINX_ENDPOINT_PATTERN` to extract `METHOD` and `/path` from the request line
  - New `extract_and_rank_endpoints()` function that counts frequencies and returns top 5
- Updated `FileJob.to_dict()` to parse `top_endpoints` JSON back into a list of dicts for the API
- Added `total_endpoints` and `top_endpoints` to the API response
- Updated the dashboard:
  - Added `Total Endpoints` column
  - Added `Top Endpoints` column showing method, path, and count for each top endpoint
  - Added CSS styling for better readability
- Updated worker completion log to include `total_endpoints`

#### Parser Rule

Nginx access logs place the request line inside double quotes:

```text
"GET /api/users HTTP/1.1"
```

The worker uses this pattern:

```python
NGINX_ENDPOINT_PATTERN = re.compile(r'"(?P<method>\S+)\s+(?P<endpoint>\S+)\s+HTTP')
```

For each line, the worker:
1. Extracts the HTTP method (GET, POST, etc.) and the endpoint path.
2. Creates a composite key `METHOD /path` so the same path with different methods counts separately.
3. Counts occurrences in a dictionary.
4. Sorts by count descending, then by endpoint name ascending.
5. Returns the top 5 (configurable via `top_n` parameter).

#### Expected Results For Sample Log

Using `samples/nginx_access.log`, expected values are:

```text
total_endpoints: 10
top_endpoints:
  1. GET /                    (1)
  2. GET /api/orders          (1)
  3. GET /api/reports        (1)
  4. GET /api/users          (1)
  5. GET /checkout           (1)
```

All endpoints in the sample appear exactly once, so the ranking is alphabetical within the tied count.

#### Files Changed

- `app/models/file_job.py` — added `total_endpoints` and `top_endpoints` fields, added `_parse_top_endpoints()` helper
- `app/jobs/file_processing.py` — added `NGINX_ENDPOINT_PATTERN`, `extract_and_rank_endpoints()`, integrated into `process_text_file()`
- `app/templates/dashboard.html` — added `Total Endpoints` and `Top Endpoints` columns with CSS styling
- `docs/LogProcessingMigration.md` — this documentation added

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
"total_endpoints": 10,
"top_endpoints": [
  {"endpoint": "/", "method": "GET", "count": 1},
  {"endpoint": "/api/orders", "method": "GET", "count": 1},
  {"endpoint": "/api/reports", "method": "GET", "count": 1},
  {"endpoint": "/api/users", "method": "GET", "count": 1},
  {"endpoint": "/checkout", "method": "GET", "count": 1}
]
```

Open the dashboard:

```text
http://localhost:5000/dashboard
```

Expected dashboard now shows:
- A `Total Endpoints` column with the count
- A `Top Endpoints` column listing each top endpoint as `METHOD /path (count)`

#### Concept Learned

Endpoint ranking transforms raw traffic into actionable routing intelligence.

In observability systems, knowing which endpoints are most frequently hit helps answer critical operational questions:
- Which API routes consume the most resources?
- Are there unexpected spikes on specific endpoints (potential DDoS or scraping)?
- Should we cache certain paths or scale specific services?
- Are error-prone endpoints also the most trafficked ones?

By storing both the total count and the ranked top list, the system provides both summary and detail — a pattern that scales from small dashboards to large analytics pipelines.

## Stage 3 — Insights Engine

At this stage, the system transitions from a file processor into a monitoring system. The core change is separating computed insights from raw job metadata, enabling trend analysis, health scoring, and independent querying.

---

### Step 11 - Create LogInsight Model

#### Goal

Store computed analysis results in a separate table from raw job metadata. This decouples the processing pipeline from the observability layer, allowing insights to be queried, compared, and trended independently.

#### Requested Metrics

- `total_requests` — total HTTP requests counted
- `total_lines` — total log lines processed
- Expanded status code counts: `301`, `302`, `401`, `403`, `504` (in addition to existing `200`, `404`, `500`)
- `health_score` — calculated value from 0.0 to 1.0 based on error rate
- `health_status` — categorical label: `healthy`, `degraded`, `unhealthy`, or `unknown`

#### What Was Already Present

- `FileJob` already stored all computed metrics inline (status counts, errors, client IPs, endpoints).
- The worker already parsed and counted these values during processing.
- The dashboard already displayed all metrics from `FileJob`.
- The API already returned structured JSON for every job.

#### What Needed To Change

The problem: **FileJob mixed two responsibilities**:
1. **Job orchestration** — tracking upload, queue, processing, retry, and failure state
2. **Observability data** — storing computed counts, rankings, and health signals

This coupling made it impossible to:
- Query insights across multiple uploads without dragging job metadata
- Compare health trends between log files over time
- Add new insight types without bloating the job table
- Recompute or refresh insights without touching job state

#### Changes Made

**1. New Model: `app/models/log_insight.py`**

Created a dedicated `LogInsight` model with:
- Foreign key `file_job_id` linking back to `FileJob` (one-to-one relationship)
- Traffic volume fields: `total_requests`, `total_lines`
- Expanded status code counts: `200`, `301`, `302`, `401`, `403`, `404`, `500`, `504`
- Error categorization: `total_error_count`, `client_error_count`, `server_error_count`
- Client analysis: `unique_client_count`, `unique_client_ips`
- Endpoint analysis: `total_endpoints`, `top_endpoints` (JSON)
- Health summary: `health_score` (Float), `health_status` (String)
- Metadata: `created_at`, `updated_at`

Added methods:
- `calculate_health_score()` — computes score from error rate, sets status label
- `_parse_top_endpoints()` — deserializes stored JSON
- `_parse_client_ips()` — splits comma-separated IPs
- `to_dict()` — returns full insight as structured JSON

**2. Updated Worker: `app/jobs/file_processing.py`**

- Added `import LogInsight` from the new model
- Expanded `count_nginx_status_codes()` to count all 8 status codes (not just 200/404/500)
- Added new `save_log_insight()` function that:
  - Looks up existing insight by `file_job_id` or creates one
  - Populates all insight fields from computed data
  - Calls `calculate_health_score()` to auto-compute health
  - Commits and logs the result
- Integrated `save_log_insight()` call into `process_text_file()` after FileJob is updated
- Kept all existing FileJob fields for backward compatibility

**3. Updated App Factory: `app/main.py`**

- Added `from app.models.log_insight import LogInsight` import so SQLAlchemy registers the table during `db.create_all()`

**4. Database Relationship**

```python
# LogInsight -> FileJob (one-to-one)
file_job_id = db.Column(db.Integer, db.ForeignKey('file_job.id'), nullable=False, unique=True)
file_job = db.relationship('FileJob', backref=db.backref('insight', uselist=False))
```

This means:
- Every `FileJob` can have zero or one `LogInsight`
- Access via `file_job.insight` returns the insight object
- Access via `insight.file_job` returns the source job

#### Health Score Calculation

```python
def calculate_health_score(self):
    if not self.total_requests or self.total_requests == 0:
        self.health_score = None
        self.health_status = "unknown"
        return

    error_rate = self.total_error_count / self.total_requests
    self.health_score = round(max(0.0, 1.0 - error_rate), 3)

    if self.health_score >= 0.95:
        self.health_status = "healthy"
    elif self.health_score >= 0.80:
        self.health_status = "degraded"
    else:
        self.health_status = "unhealthy"
```

**Scoring thresholds:**
- `≥ 0.95` → `healthy` (≤ 5% errors)
- `≥ 0.80` → `degraded` (5–20% errors)
- `< 0.80` → `unhealthy` (> 20% errors)
- No requests → `unknown`

#### Expected Results For Sample Log

Using `samples/nginx_access.log` (10 lines):

```text
total_requests:        10
total_lines:           10
status_200_count:      4
status_301_count:      0
status_302_count:      1
status_401_count:      1
status_403_count:      1
status_404_count:      1
status_500_count:      1
status_504_count:      1
total_error_count:     5
client_error_count:    3
server_error_count:    2
unique_client_count:   10
total_endpoints:       10
health_score:          0.5
health_status:         unhealthy
```

With 5 errors out of 10 requests, the health score is `0.5` and status is `unhealthy`.

#### Files Changed

- `app/models/log_insight.py` — **new file**, the LogInsight model
- `app/jobs/file_processing.py` — added `save_log_insight()`, expanded status code counting, imported LogInsight
- `app/main.py` — imported LogInsight for SQLAlchemy table registration
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged (Backward Compatibility)

- `app/models/file_job.py` — kept all existing fields; FileJob still stores its own copy of metrics
- `app/templates/dashboard.html` — still reads from FileJob (insight data accessible via API expansion later)
- `app/routes/file_routes.py` — no changes needed for this step

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Reset the database (new table requires schema creation):

```bash
docker compose down -v
docker compose up -d --build
```

Upload the sample nginx log:

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
```

Check the FileJob result (backward compatible):

```bash
curl http://localhost:5000/files/1
```

Verify the LogInsight record was created by querying the database directly:

```bash
docker exec -it postgres-db psql -U postgres -d tasks -c "SELECT * FROM log_insight;"
```

Expected output:

```
 id | file_job_id | total_requests | total_lines | status_200_count | ... | health_score | health_status
----+-------------+----------------+-------------+------------------+-----+--------------+---------------
  1 |           1 |             10 |          10 |                4 | ... |          0.5 | unhealthy
```

Check the relationship from the job side:

```bash
docker exec -it postgres-db psql -U postgres -d tasks -c "SELECT f.id, f.status, i.health_score, i.health_status FROM file_job f LEFT JOIN log_insight i ON f.id = i.file_job_id;"
```

#### Concept Learned

**Separate concerns between orchestration and analysis.**

`FileJob` answers: *Did the processing succeed? When? How long did it take? How many retries?*

`LogInsight` answers: *What did the log tell us? How healthy is the service? Which endpoints are hot? Are errors rising?*

This separation is the foundation of a monitoring system:
- **Job metadata** is ephemeral and operational (needed for the pipeline)
- **Insight data** is analytical and persistent (needed for dashboards, alerts, and trend analysis)

By storing insights in their own table, the system can now:
- Run queries like `SELECT AVG(health_score) FROM log_insight WHERE created_at > NOW() - INTERVAL '7 days'`
- Compare today's traffic patterns against last week's
- Build alerting rules on health score thresholds
- Export insight data to external analytics tools without job noise

This is the architectural shift from **file processing** to **log observability**.

### Step 13 - Add Insights API

#### Goal

Expose stored analytics through dedicated REST endpoints so clients can query insights independently from job metadata.

#### Requested Routes

- `GET /insights` — list all insights with optional filtering
- `GET /insights/<id>` — single insight by ID with linked file job summary
- `GET /insights/health-summary` — aggregated health statistics across all uploads

#### What Was Already Present

- `LogInsight` model already stored all computed metrics in the database.
- `save_log_insight()` already created records after file processing.
- `FileJob` already had API routes (`/files`, `/files/<id>`) returning job metadata.
- The existing response helper (`success_response`, `error_response`) provided consistent JSON formatting.

#### What Needed To Change

The insights existed in the database but were **inaccessible from the API**. Clients could only see raw job data through `/files/<id>`, which mixed orchestration metadata with analysis results. There was no way to:
- Query only insights (without job noise)
- Filter by health status
- Get system-wide health aggregates
- Retrieve a single insight with its source job context

#### Changes Made

**1. New Route File: `app/routes/insight_routes.py`**

Created a dedicated blueprint with three endpoints:

- **`GET /insights`** — lists all LogInsight records, supports:
  - `?health_status=` filter (healthy, degraded, unhealthy, unknown)
  - `?limit=` pagination (default 50)
  - Ordered by `created_at` descending (newest first)

- **`GET /insights/<id>`** — returns single insight including:
  - Full insight data via `to_dict()`
  - Linked file job summary (id, filename, status, processing time)
  - 404 if insight not found

- **`GET /insights/health-summary`** — aggregated statistics:
  - Total insight count
  - Breakdown by health status (healthy, degraded, unhealthy, unknown)
  - Average health score across all insights
  - Healthy percentage

**2. Updated App Factory: `app/main.py`**

Registered the new `insight_bp` blueprint alongside existing `system_bp` and `file_bp`.

**3. Consistent Patterns**

All routes follow the same patterns as existing routes:
- Use `success_response()` / `error_response()` for consistent JSON structure
- Use `log_message()` for API-level logging
- Use SQLAlchemy query interface for database access

#### Files Changed

- `app/routes/insight_routes.py` — **new file**, insight API endpoints
- `app/main.py` — registered `insight_bp` blueprint
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged

- `app/models/log_insight.py` — no model changes needed
- `app/jobs/file_processing.py` — no worker changes needed
- `app/routes/file_routes.py` — no file route changes needed

#### API Response Examples

**GET /insights**

```json
{
  "success": true,
  "data": [
    {
      "insight_id": 1,
      "file_job_id": 1,
      "total_requests": 10,
      "total_lines": 10,
      "status_200_count": 4,
      "status_404_count": 1,
      "status_500_count": 1,
      "total_error_count": 5,
      "client_error_count": 3,
      "server_error_count": 2,
      "unique_client_count": 10,
      "total_endpoints": 10,
      "health_score": 0.5,
      "health_status": "unhealthy",
      "created_at": "2026-06-05T12:00:00",
      "updated_at": "2026-06-05T12:00:00"
    }
  ],
  "error": null
}
```

**GET /insights/1**

```json
{
  "success": true,
  "data": {
    "insight_id": 1,
    "file_job_id": 1,
    "total_requests": 10,
    ...,
    "health_score": 0.5,
    "health_status": "unhealthy",
    "file_job": {
      "id": 1,
      "original_filename": "nginx_access.log",
      "status": "completed",
      "processing_time": 0.123,
      "created_at": "2026-06-05T12:00:00"
    }
  },
  "error": null
}
```

**GET /insights/health-summary**

```json
{
  "success": true,
  "data": {
    "total_insights": 5,
    "breakdown": {
      "healthy": 2,
      "degraded": 1,
      "unhealthy": 1,
      "unknown": 1
    },
    "average_health_score": 0.73,
    "healthy_percentage": 40.0
  },
  "error": null
}
```

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose down -v
docker compose up -d --build
```

Upload a log file first (to create an insight):

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
```

Test the new endpoints:

```bash
# List all insights
curl http://localhost:5000/insights

# Filter by health status
curl "http://localhost:5000/insights?health_status=unhealthy"

# Get single insight
curl http://localhost:5000/insights/1

# Get health summary
curl http://localhost:5000/insights/health-summary
```

#### Concept Learned

**Expose analytics through dedicated endpoints, not just embedded in job responses.**

Before this step, insights were only accessible as nested data inside FileJob responses. Now they are first-class resources with their own query interface. This enables:

- **Independent querying** — dashboards can poll `/insights` without pulling job metadata
- **Filtering** — operations teams can focus on `unhealthy` insights only
- **Aggregation** — `/health-summary` provides executive-level health dashboards
- **Scalability** — as insight types grow, the `/insights` namespace can expand without affecting job routes

This is the pattern that separates **data pipelines** (FileJob) from **analytics platforms** (LogInsight API).  

### Step 14 - Add Metrics Endpoint

#### Goal

Expose system-wide statistics about the entire processing pipeline through a single endpoint. This provides an operational dashboard view of the system's health, throughput, and performance.

#### Requested Route

- `GET /metrics` — system-wide statistics

#### What Was Already Present

- `FileJob` stored individual job status, processing time, retry counts, and error counts.
- `LogInsight` stored health scores and status distributions.
- The worker sent heartbeat keys to Redis.
- The RQ queue exposed `queue.count` for pending jobs.
- `/debug/workers` already checked worker heartbeats.
- `/` already tracked API hits via Redis `incr("hits")`.

#### What Needed To Change

All these metrics existed in separate places (database, Redis, scattered endpoints). There was no single endpoint that aggregated them into an operational snapshot. An operator monitoring the system would need to call `/files`, `/insights/health-summary`, `/debug/workers`, and check Redis manually.

#### Changes Made

**1. New Route File: `app/routes/metrics_routes.py`**

Created a dedicated `metrics_bp` blueprint with one endpoint:

- **`GET /metrics`** — returns a structured snapshot with 5 metric categories:

| Category | Metrics |
|----------|---------|
| `jobs` | total, queued, processing, completed, failed, success_rate %, avg_processing_time, total_retries |
| `errors` | total_errors, client_errors, server_errors (summed across all jobs) |
| `insights` | total_insights, healthy/degraded/unhealthy counts, average_health_score |
| `queue` | pending_jobs (from RQ queue count) |
| `workers` | total, alive, dead (from Redis heartbeat keys) |
| `system` | api_hits (Redis counter) |

All values are computed at request time using SQL `COUNT`, `SUM`, `AVG` queries and Redis lookups. No caching — this is a real-time operational endpoint.

**2. Updated App Factory: `app/main.py`**

Registered the new `metrics_bp` blueprint.

#### Response Structure

```json
{
  "success": true,
  "data": {
    "timestamp": "2026-06-06T11:51:00",
    "jobs": {
      "total": 15,
      "queued": 2,
      "processing": 1,
      "completed": 10,
      "failed": 2,
      "success_rate": 66.7,
      "average_processing_time": 0.234,
      "total_retries": 3
    },
    "errors": {
      "total": 45,
      "client_errors": 30,
      "server_errors": 15
    },
    "insights": {
      "total": 10,
      "healthy": 6,
      "degraded": 2,
      "unhealthy": 2,
      "average_health_score": 0.82
    },
    "queue": {
      "pending_jobs": 2
    },
    "workers": {
      "total": 2,
      "alive": 2,
      "dead": 0
    },
    "system": {
      "api_hits": 147
    }
  },
  "error": null
}
```

#### Files Changed

- `app/routes/metrics_routes.py` — **new file**, system metrics endpoint
- `app/main.py` — registered `metrics_bp` blueprint
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged

- `app/models/file_job.py` — no model changes needed
- `app/models/log_insight.py` — no model changes needed
- `app/jobs/file_processing.py` — no worker changes needed
- `app/routes/insight_routes.py` — no insight route changes needed

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Upload a few files first (to generate metrics):

```bash
curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
curl -X POST http://localhost:5000/upload -F "file=@sample.txt"
```

Test the metrics endpoint:

```bash
curl http://localhost:5000/metrics
```

Verify the response contains all 6 categories with real values.

#### Concept Learned

**Aggregate operational signals into a single operational endpoint.**

Before this step, metrics were scattered across multiple endpoints and data stores. Now `/metrics` provides a unified operational snapshot that answers the key monitoring questions:

- Is the pipeline keeping up? (`jobs.queued` vs `workers.alive`)
- Are jobs failing? (`jobs.success_rate`, `jobs.failed`)
- Are errors client-side or server-side? (`errors.client_errors` vs `errors.server_errors`)
- Is the system healthy overall? (`insights.average_health_score`)
- Do we need to scale workers? (`queue.pending_jobs` vs `workers.alive`)

This is the endpoint that monitoring tools (Prometheus, Grafana, Datadog) would scrape. It follows the pattern of exposing a `/metrics` or `/health` endpoint that consolidates internal state into an external signal.

### Step 15 - Worker Heartbeat Improvement

#### Goal

Track stale workers reliably using Redis TTL and enriched heartbeat metadata, so the system can distinguish between active, stale, dead, and starting workers.

#### What Was Already Present

- The worker already sent heartbeats to Redis every 5 seconds.
- The heartbeat stored a raw timestamp: `r.set(f"worker:{name}:heartbeat", time.time())`.
- `/debug/workers` checked if `(now - last_seen) < 10` to label workers as "alive" or "dead".
- The heartbeat thread ran as a daemon thread alongside the RQ worker.

#### Problems with the Old Approach

1. **No auto-expiry**: If a worker process crashed, the heartbeat key remained in Redis forever. The debug endpoint would show it as "alive" if the timestamp happened to be recent, or "dead" based on a hardcoded 10-second threshold — but the key itself never disappeared.
2. **No enrichment**: The heartbeat only stored a timestamp. There was no uptime tracking, no stability scoring, no start time recording.
3. **Binary status**: Workers were only "alive" or "dead". There was no "stale" (slow heartbeats) or "starting" (registered but not yet beating) state.
4. **Race condition**: A worker starting up might be queried before its first heartbeat, showing as "dead" even though it was healthy.

#### Changes Made

**1. Updated Worker: `app/worker.py`**

- Added `HEARTBEAT_TTL = 30` — Redis key auto-expires if worker stops sending heartbeats.
- Added `HEARTBEAT_INTERVAL = 5` — explicit constant for clarity.
- Heartbeat now uses `r.set(key, timestamp, ex=HEARTBEAT_TTL)` — the `ex` parameter sets TTL.
- Added a second Redis hash (`worker:{name}:info`) storing enriched metadata:
  - `status`: active/starting
  - `started_at`: ISO timestamp of worker start
  - `uptime_seconds`: cumulative uptime
  - `consecutive_beats`: stability counter (resets on heartbeat failure)
- Added exception handling in heartbeat loop — if Redis fails, beats reset and loop continues.
- Added startup registration — worker writes initial "starting" state before heartbeat thread begins.
- Heartbeat log now includes beat number and uptime for traceability.

**2. Updated Debug Endpoint: `app/routes/system_routes.py`**

- `/debug/workers` now uses **Redis TTL** as the primary stale-detection signal, not just time arithmetic.
- Status logic:
  - `ttl <= 0` → `dead` (key expired, worker stopped)
  - `seconds_since > 15` → `stale` (beating slowly, may be overloaded)
  - otherwise → `active` (healthy)
- Also detects `starting` workers — those with `info` hash but no heartbeat key yet.
- Returns enriched response fields:
  - `last_seen_iso` — human-readable timestamp
  - `seconds_since_heartbeat` — how long since last beat
  - `ttl_remaining` — seconds until Redis auto-deletes the key
  - `uptime_seconds` — cumulative worker uptime
  - `consecutive_beats` — stability score
  - `started_at` — when worker began
  - `reason` — explanation for dead/starting status

**3. Updated Home Route**

Added `insights_endpoint` and `metrics_endpoint` to the root response so API discovery is complete.

#### Files Changed

- `app/worker.py` — enriched heartbeat with TTL, metadata hash, exception handling
- `app/routes/system_routes.py` — improved `/debug/workers` with TTL-based detection, 4 status states, enriched response
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged

- `app/models/*` — no model changes needed
- `app/jobs/file_processing.py` — no processing logic changes needed
- `app/routes/file_routes.py` — no file route changes needed
- `app/routes/insight_routes.py` — no insight route changes needed
- `app/routes/metrics_routes.py` — no metrics route changes needed

#### Worker Status States

| Status | Meaning | Trigger |
|--------|---------|---------|
| `active` | Healthy and beating normally | TTL > 0 and last beat < 15s ago |
| `stale` | Beating but slowly (overloaded?) | TTL > 0 but last beat > 15s ago |
| `dead` | Stopped sending heartbeats | Redis key expired (TTL = 0) |
| `starting` | Registered but not yet beating | Has `info` hash but no heartbeat key |

#### Response Example

```json
{
  "success": true,
  "data": [
    {
      "worker": "task-worker-7f8a9b",
      "status": "active",
      "last_seen": 1754515860.123,
      "last_seen_iso": "2026-06-06T11:51:00",
      "seconds_since_heartbeat": 2.3,
      "ttl_remaining": 28,
      "uptime_seconds": 3600.5,
      "consecutive_beats": 720,
      "started_at": "2026-06-06T10:51:00"
    },
    {
      "worker": "task-worker-old-3c4d5e",
      "status": "dead",
      "last_seen": null,
      "seconds_since_heartbeat": null,
      "ttl_remaining": 0,
      "uptime_seconds": null,
      "consecutive_beats": null,
      "reason": "Redis key expired — worker stopped sending heartbeats"
    }
  ],
  "error": null
}
```

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Check worker status:

```bash
curl http://localhost:5000/debug/workers
```

Simulate a dead worker by stopping the worker container:

```bash
docker stop task-worker
# Wait 30 seconds for TTL to expire
curl http://localhost:5000/debug/workers
```

The stopped worker should show `status: "dead"` with `ttl_remaining: 0`.

Restart the worker:

```bash
docker compose up -d worker
curl http://localhost:5000/debug/workers
```

The new worker should show `status: "active"` with `consecutive_beats` climbing.

#### Concept Learned

**Use TTL-based expiry, not time arithmetic, for heartbeat stale detection.**

Before this step, the system relied on `(now - last_seen) < 10` — a client-side calculation that could be wrong if clocks drifted, API was slow, or Redis had stale data. By using Redis `SET ... EX`, the server itself enforces expiry: if the worker dies, the key disappears automatically. This is the same pattern used by distributed systems (etcd leases, ZooKeeper ephemeral nodes, Consul TTL checks) for reliable failure detection.

The enriched metadata (uptime, consecutive beats, start time) transforms heartbeat from a binary alive/dead signal into a **health gradient** that operators can use to detect degrading workers before they fail completely.

### Step 16 - Queue Monitoring

#### Goal

Show pending jobs and queue size, plus database job breakdown and throughput estimates, so operators can detect backlog, idle, or overloaded states.

#### Requested Metrics

- Pending jobs in RQ queue
- Queue size
- Job counts by status (queued, processing, completed, failed)

#### What Was Already Present

- `queue.count` from RQ already exposed the Redis queue size.
- `FileJob` already stored status fields (`queued`, `processing`, `completed`, `failed`).
- `/metrics` from Step 14 already included `queue.pending_jobs` as one field in a large snapshot.
- The scheduler already checked for stale processing jobs.

#### What Needed To Change

The queue metrics were buried inside `/metrics` as a single number. There was no dedicated endpoint for queue-specific monitoring, no throughput estimation, and no health signal that could alert operators to backlog conditions (jobs waiting but no workers processing).

#### Changes Made

**1. New Route File: `app/routes/queue_routes.py`**

Created a dedicated `queue_bp` blueprint with one endpoint:

- **`GET /queue/status`** — returns structured queue metrics with 4 categories:

| Category | Metrics |
|----------|---------|
| `rq_queue` | `pending_jobs` — jobs waiting in Redis RQ queue |
| `database` | `total`, `queued`, `processing`, `completed`, `failed` — job counts by status |
| `throughput` | `completed_last_hour` — jobs finished in last 60 minutes; `estimated_clear_time` — rough ETA to clear backlog |
| `health` | Categorical signal: `idle`, `healthy`, `backlogged`, `overloaded` |

**Health signal logic:**

| State | Condition | Meaning |
|-------|-----------|---------|
| `idle` | No pending jobs, no queued DB jobs | System has no work |
| `backlogged` | Pending jobs exist but nothing in `processing` | Workers may be dead or not picking up jobs |
| `overloaded` | > 10 pending jobs in queue | Queue depth suggests need for more workers |
| `healthy` | Some pending jobs, some processing | Normal operating state |

**2. Updated App Factory: `app/main.py`**

Registered the new `queue_bp` blueprint.

**3. Updated Home Route (in `system_routes.py`)**

Added `queue_endpoint` to root response for API discovery completeness.

#### Response Structure

```json
{
  "success": true,
  "data": {
    "timestamp": "2026-06-07T10:04:00",
    "rq_queue": {
      "pending_jobs": 3
    },
    "database": {
      "total": 25,
      "queued": 3,
      "processing": 1,
      "completed": 20,
      "failed": 1
    },
    "throughput": {
      "completed_last_hour": 12,
      "estimated_clear_time": "3 minutes (1 worker)"
    },
    "health": "healthy"
  },
  "error": null
}
```

#### Files Changed

- `app/routes/queue_routes.py` — **new file**, queue monitoring endpoint
- `app/main.py` — registered `queue_bp` blueprint
- `app/routes/system_routes.py` — added `queue_endpoint` to home route
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged

- `app/models/*` — no model changes needed
- `app/jobs/file_processing.py` — no worker changes needed
- `app/worker.py` — no heartbeat changes needed
- `app/routes/insight_routes.py` — no insight route changes needed
- `app/routes/metrics_routes.py` — no metrics route changes needed

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Check queue status with no jobs:

```bash
curl http://localhost:5000/queue/status
```

Expected: `health: "idle"`, `pending_jobs: 0`.

Upload several files rapidly to create backlog:

```bash
for i in {1..5}; do
  curl -X POST http://localhost:5000/upload -F "file=@samples/nginx_access.log"
done
```

Check queue status during processing:

```bash
curl http://localhost:5000/queue/status
```

Expected: `health: "healthy"` or `"overloaded"`, `pending_jobs` > 0, `throughput.completed_last_hour` climbing.

Stop the worker container and check again:

```bash
docker stop task-worker
curl http://localhost:5000/queue/status
```

Expected: `health: "backlogged"` — jobs in queue but nothing processing.

#### Concept Learned

**Queue depth is an early warning signal, not just a number.**

Before this step, `pending_jobs` was a single integer inside `/metrics`. Now `/queue/status` provides a **health gradient** that operators can act on:

- `idle` → scale workers down (save resources)
- `healthy` → normal operation
- `backlogged` → workers may be dead (check `/debug/workers`)
- `overloaded` → scale workers up (add capacity)

The throughput estimate (`completed_last_hour`) turns queue depth into a **capacity planning signal**: if the queue is growing faster than workers can clear it, the system needs more capacity. This is the same pattern used by Kubernetes HPA (Horizontal Pod Autoscaler), AWS Auto Scaling, and Celery monitoring dashboards.

### Step 17 - Health Endpoint

#### Goal

Check DB, Redis, and worker connectivity in a single endpoint, returning a structured health report with per-service status and an overall system status.

#### Requested Checks

- Database (PostgreSQL)
- Redis (cache + queue broker)
- Workers (heartbeat freshness)

#### What Was Already Present

- `db.session` from SQLAlchemy was already used throughout the app.
- `redis_conn` from `app/extensions.py` already connected to Redis.
- `queue` from RQ was already used for job enqueueing.
- Worker heartbeat keys were already written to Redis (Step 15).
- `/debug/workers` already checked worker status but was a debug endpoint, not a health check.
- `/metrics` from Step 14 included some operational data but no service connectivity checks.

#### What Needed To Change

There was no single endpoint that **proactively checked** whether each service was actually reachable and functional. The existing endpoints assumed connectivity — they would fail with 500 errors if DB or Redis were down, but they didn't provide a structured health report that load balancers, Kubernetes, or monitoring tools could use.

A proper health endpoint needs:
- **Per-service checks** with isolated try/except blocks (one failure doesn't break others)
- **Overall status** aggregation (healthy / degraded / unhealthy)
- **HTTP status codes** that match the health state (200 for healthy, 503 for unhealthy)
- **Structured response** that monitoring tools can parse automatically

#### Changes Made

**1. New Route File: `app/routes/health_routes.py`**

Created a dedicated `health_bp` blueprint with one endpoint and four check functions:

| Check Function | What It Tests | Pass Criteria |
|----------------|-------------|---------------|
| `check_database()` | `SELECT 1` on PostgreSQL | Query executes without exception |
| `check_redis()` | `PING` on Redis | Redis responds to PING |
| `check_workers()` | Heartbeat keys in Redis | At least one active worker (TTL > 0, beat < 15s) |
| `check_queue()` | RQ queue access | `queue.count` returns without exception |

**Overall status logic:**

| Status | Condition | HTTP Code |
|--------|-----------|-----------|
| `healthy` | All services up | 200 |
| `degraded` | Workers or queue down, but DB + Redis up | 200 |
| `unhealthy` | DB or Redis down (critical services) | 503 |

**Response structure:**

```json
{
  "success": true,
  "data": {
    "timestamp": "2026-06-07T10:38:00",
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": { "status": "up" },
      "redis": { "status": "up" },
      "workers": { "status": "up", "total_workers": 2, "active_workers": 2, "stale_workers": 0 },
      "queue": { "status": "up", "pending_jobs": 0 }
    }
  },
  "error": null
}
```

**2. Updated App Factory: `app/main.py`**

Registered the new `health_bp` blueprint.

**3. Updated Home Route (in `system_routes.py`)**

Added `health_endpoint` to root response for API discovery.

#### Files Changed

- `app/routes/health_routes.py` — **new file**, health check endpoint
- `app/main.py` — registered `health_bp` blueprint
- `app/routes/system_routes.py` — added `health_endpoint` to home route
- `docs/LogProcessingMigration.md` — this documentation added

#### Files Unchanged

- `app/models/*` — no model changes needed
- `app/jobs/file_processing.py` — no processing logic changes needed
- `app/worker.py` — no heartbeat changes needed
- `app/routes/insight_routes.py` — no insight route changes needed
- `app/routes/metrics_routes.py` — no metrics route changes needed
- `app/routes/queue_routes.py` — no queue route changes needed

#### How To Test

Run a syntax check:

```bash
python -m compileall app
```

Run the system:

```bash
docker compose up -d --build
```

Test healthy state:

```bash
curl http://localhost:5000/health
```

Expected: `status: "healthy"`, HTTP 200, all services `up`.

Test degraded state (stop worker):

```bash
docker stop task-worker
sleep 35  # Wait for TTL expiry
curl http://localhost:5000/health
```

Expected: `status: "degraded"`, HTTP 200, workers `status: "down"` or `degraded`.

Test unhealthy state (stop DB):

```bash
docker stop postgres-db
curl http://localhost:5000/health
```

Expected: `status: "unhealthy"`, HTTP 503, database `status: "down"` with error message.

Restart all services:

```bash
docker compose up -d
```

#### Concept Learned

**Health checks must be proactive, isolated, and machine-readable.**

Before this step, service failures would only be detected when an API request actually failed. Now `/health` proactively tests each dependency and returns a structured report that:

- **Load balancers** can use to route traffic away from unhealthy instances (HTTP 503)
- **Kubernetes** can use for liveness and readiness probes (`/health` with 5-second timeout)
- **Monitoring tools** (PagerDuty, Datadog, Grafana) can parse the JSON and alert on specific service failures
- **Operators** can see which service is down without reading stack traces

The isolated try/except pattern is critical: if Redis is down, the database check still runs and reports its own status. This prevents a single failure from masking the health of other services. The status hierarchy (critical vs non-critical) ensures that a worker outage doesn't make the whole system appear dead to a load balancer, while a database outage does trigger a 503.