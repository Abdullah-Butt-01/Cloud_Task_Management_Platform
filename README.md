# TXT File Processing System

## Overview
The system takes a text file 

## Features
- Upload .txt files
- Background processing with Redis Queue
- Word, line, and character counting
- PostgreSQL persistence
- Retry and failure handling
- Worker health check
- Dockerized deployment

## Architecture
Add a simple diagram.

## Tech Stack
- Python Flask
- PostgreSQL
- Redis
- RQ
- SQLAlchemy
- Docker Compose

## Project Structure
Explain important folders and files.

## API Routes
Document every route with request/response examples.

## Processing Flow
Explain upload -> queue -> worker -> database -> result.

## Failure Handling
Explain retry_count, failed status, scheduler timeout.

## Running Locally
docker compose up -d --build

## Testing
curl commands for upload, list, dashboard, worker debug.

## Deployment Notes
How to run on VM.

## Future Improvements
Authentication, migrations, file size limits, better UI, tests.
