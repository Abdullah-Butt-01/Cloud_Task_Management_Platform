from datetime import datetime
import json
import os
import logging
import re

from app.extensions import db, queue
from app.models.file_job import FileJob
from app.utils.logger import log_message

MAX_RETRIES = 3
SUPPORTED_EXTENSIONS = {".txt", ".log"}
NGINX_STATUS_PATTERN = re.compile(r'"\s(?P<status_code>\d{3})\s')
NGINX_CLIENT_IP_PATTERN = re.compile(r"^(?P<client_ip>\S+)\s")
# Step 10: New regex to extract HTTP method and endpoint from nginx log lines
# Example: "GET /api/users HTTP/1.1" -> method=GET, endpoint=/api/users
NGINX_ENDPOINT_PATTERN = re.compile(
    r'"(?P<method>\S+)\s+(?P<endpoint>\S+)\s+HTTP'
)


def calculate_processing_time(started_at, completed_at):
    if not started_at or not completed_at:
        return None

    return round((completed_at - started_at).total_seconds(), 3)


def count_text_stats(content):
    return {
        "word_count": len(content.split()),
        "line_count": len(content.splitlines()),
        "character_count": len(content),
    }


def count_nginx_status_codes(content):
    counts = {
        "status_200_count": 0,
        "status_404_count": 0,
        "status_500_count": 0,
        "total_error_count": 0,
        "client_error_count": 0,
        "server_error_count": 0,
    }

    for line in content.splitlines():
        match = NGINX_STATUS_PATTERN.search(line)

        if not match:
            continue

        status_code = match.group("status_code")
        status_number = int(status_code)

        if status_code == "200":
            counts["status_200_count"] += 1
        elif status_code == "404":
            counts["status_404_count"] += 1
        elif status_code == "500":
            counts["status_500_count"] += 1

        if 400 <= status_number <= 499:
            counts["client_error_count"] += 1
            counts["total_error_count"] += 1
        elif 500 <= status_number <= 599:
            counts["server_error_count"] += 1
            counts["total_error_count"] += 1

    return counts


def extract_unique_client_ips(content):
    client_ips = set()

    for line in content.splitlines():
        match = NGINX_CLIENT_IP_PATTERN.search(line)

        if match:
            client_ips.add(match.group("client_ip"))

    return sorted(client_ips)


# Step 10: New function to extract and rank endpoints
def extract_and_rank_endpoints(content, top_n=5):
    """
    Extract all HTTP endpoints from nginx log content and rank by frequency.

    Returns:
        dict with:
        - total_endpoints: number of unique endpoints found
        - top_endpoints: list of {endpoint, method, count} dicts, sorted by count desc
    """
    endpoint_counts = {}

    for line in content.splitlines():
        match = NGINX_ENDPOINT_PATTERN.search(line)

        if not match:
            continue

        method = match.group("method")
        endpoint = match.group("endpoint")
        # Create a composite key: "METHOD /path" so GET /api/users and POST /api/users are separate
        key = f"{method} {endpoint}"

        if key not in endpoint_counts:
            endpoint_counts[key] = {"endpoint": endpoint, "method": method, "count": 0}

        endpoint_counts[key]["count"] += 1

    # Sort by count descending, then by endpoint name ascending
    sorted_endpoints = sorted(
        endpoint_counts.values(),
        key=lambda x: (-x["count"], x["endpoint"])
    )

    # Take top N (default 5)
    top_endpoints = sorted_endpoints[:top_n]

    return {
        "total_endpoints": len(endpoint_counts),
        "top_endpoints": top_endpoints,
    }


def process_text_file(file_job_id):
    file_job = FileJob.query.get(file_job_id)

    if not file_job:
        log_message("WORKER", "File job not found", file_job_id=file_job_id)
        return None

    try:
        file_job.status = "processing"
        file_job.started_at = datetime.utcnow()
        file_job.error_message = None
        db.session.commit()

        log_message("WORKER", "File processing started", file_job_id=file_job.id)

        if not os.path.exists(file_job.file_path):
            raise FileNotFoundError("Uploaded file was not found")

        file_extension = os.path.splitext(file_job.original_filename)[1].lower()

        if file_extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Only .txt and .log files can be processed")

        with open(file_job.file_path, "r", encoding="utf-8") as text_file:
            content = text_file.read()

        stats = count_text_stats(content)
        status_counts = count_nginx_status_codes(content)
        unique_client_ips = extract_unique_client_ips(content)
        # Step 10: Extract and rank endpoints
        endpoint_data = extract_and_rank_endpoints(content)

        file_job.word_count = stats["word_count"]
        file_job.line_count = stats["line_count"]
        file_job.character_count = stats["character_count"]
        file_job.status_200_count = status_counts["status_200_count"]
        file_job.status_404_count = status_counts["status_404_count"]
        file_job.status_500_count = status_counts["status_500_count"]
        file_job.total_error_count = status_counts["total_error_count"]
        file_job.client_error_count = status_counts["client_error_count"]
        file_job.server_error_count = status_counts["server_error_count"]
        file_job.unique_client_count = len(unique_client_ips)
        file_job.unique_client_ips = ",".join(unique_client_ips)
        # Step 10: Store endpoint ranking data
        file_job.total_endpoints = endpoint_data["total_endpoints"]
        file_job.top_endpoints = json.dumps(endpoint_data["top_endpoints"])
        file_job.status = "completed"
        file_job.completed_at = datetime.utcnow()
        file_job.processing_time = calculate_processing_time(
            file_job.started_at,
            file_job.completed_at,
        )
        db.session.commit()

        log_message(
            "WORKER",
            f"File processing completed processing_time={file_job.processing_time}s "
            f"total_endpoints={file_job.total_endpoints}",
            file_job_id=file_job.id,
        )

        return file_job.to_dict()

    except Exception as error:
        file_job.retry_count += 1
        file_job.error_message = str(error)

        log_message(
            "WORKER",
            f"File processing failed error={error} attempt={file_job.retry_count}",
            file_job_id=file_job.id,
            level=logging.ERROR,
        )

        if file_job.retry_count < MAX_RETRIES:
            file_job.status = "queued"
            db.session.commit()

            retry_job = queue.enqueue(process_text_file, file_job.id)
            file_job.rq_job_id = retry_job.id
            db.session.commit()

            log_message(
                "WORKER",
                f"File processing retry queued: attempt={file_job.retry_count}",
                file_job_id=file_job.id,
                level=logging.WARNING,
            )
        else:
            file_job.status = "failed"
            file_job.completed_at = datetime.utcnow()
            file_job.processing_time = calculate_processing_time(
                file_job.started_at,
                file_job.completed_at,
            )
            db.session.commit()

            log_message(
                "WORKER",
                f"File processing failed permanently: {error}",
                file_job_id=file_job.id,
                level=logging.ERROR,
            )

        return None