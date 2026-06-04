from datetime import datetime
import json
import os
import logging
import re

from app.extensions import db, queue
from app.models.file_job import FileJob
from app.models.log_insight import LogInsight
from app.utils.logger import log_message

MAX_RETRIES = 3
SUPPORTED_EXTENSIONS = {".txt", ".log"}
NGINX_STATUS_PATTERN = re.compile(r'"\s(?P<status_code>\d{3})\s')
NGINX_CLIENT_IP_PATTERN = re.compile(r"^(?P<client_ip>\S+)\s")
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
    """
    Count all HTTP status codes from nginx log content.
    Step 11: Expanded to count all common status codes, not just 200/404/500.
    """
    counts = {
        "status_200_count": 0,
        "status_404_count": 0,
        "status_500_count": 0,
        "status_301_count": 0,
        "status_302_count": 0,
        "status_401_count": 0,
        "status_403_count": 0,
        "status_504_count": 0,
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

        # Count specific status codes
        if status_code == "200":
            counts["status_200_count"] += 1
        elif status_code == "301":
            counts["status_301_count"] += 1
        elif status_code == "302":
            counts["status_302_count"] += 1
        elif status_code == "401":
            counts["status_401_count"] += 1
        elif status_code == "403":
            counts["status_403_count"] += 1
        elif status_code == "404":
            counts["status_404_count"] += 1
        elif status_code == "500":
            counts["status_500_count"] += 1
        elif status_code == "504":
            counts["status_504_count"] += 1

        # Categorize errors
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


def extract_and_rank_endpoints(content, top_n=5):
    endpoint_counts = {}
    for line in content.splitlines():
        match = NGINX_ENDPOINT_PATTERN.search(line)
        if not match:
            continue
        method = match.group("method")
        endpoint = match.group("endpoint")
        key = f"{method} {endpoint}"
        if key not in endpoint_counts:
            endpoint_counts[key] = {"endpoint": endpoint, "method": method, "count": 0}
        endpoint_counts[key]["count"] += 1

    sorted_endpoints = sorted(
        endpoint_counts.values(),
        key=lambda x: (-x["count"], x["endpoint"])
    )
    return {
        "total_endpoints": len(endpoint_counts),
        "top_endpoints": sorted_endpoints[:top_n],
    }


# Step 11: New function to create or update LogInsight record
def save_log_insight(file_job, status_counts, unique_client_ips, endpoint_data, line_count):
    """
    Create or update a LogInsight record linked to the given FileJob.

    This separates computed insights from raw job metadata, enabling:
    - Independent querying of insights across time
    - Trend analysis and comparison between uploads
    - Health scoring based on error rates
    """
    insight = LogInsight.query.filter_by(file_job_id=file_job.id).first()

    if not insight:
        insight = LogInsight(file_job_id=file_job.id)
        db.session.add(insight)

    # Traffic volume
    insight.total_requests = status_counts["status_200_count"] + status_counts["status_301_count"] + status_counts["status_302_count"] + status_counts["status_401_count"] + status_counts["status_403_count"] + status_counts["status_404_count"] + status_counts["status_500_count"] + status_counts["status_504_count"]
    insight.total_lines = line_count

    # Status codes
    insight.status_200_count = status_counts["status_200_count"]
    insight.status_301_count = status_counts["status_301_count"]
    insight.status_302_count = status_counts["status_302_count"]
    insight.status_401_count = status_counts["status_401_count"]
    insight.status_403_count = status_counts["status_403_count"]
    insight.status_404_count = status_counts["status_404_count"]
    insight.status_500_count = status_counts["status_500_count"]
    insight.status_504_count = status_counts["status_504_count"]

    # Errors
    insight.total_error_count = status_counts["total_error_count"]
    insight.client_error_count = status_counts["client_error_count"]
    insight.server_error_count = status_counts["server_error_count"]

    # Clients
    insight.unique_client_count = len(unique_client_ips)
    insight.unique_client_ips = ",".join(unique_client_ips)

    # Endpoints
    insight.total_endpoints = endpoint_data["total_endpoints"]
    insight.top_endpoints = json.dumps(endpoint_data["top_endpoints"])

    # Health score (calculated automatically)
    insight.calculate_health_score()

    db.session.commit()

    log_message(
        "WORKER",
        f"LogInsight saved health_score={insight.health_score} status={insight.health_status}",
        file_job_id=file_job.id,
    )

    return insight


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
        endpoint_data = extract_and_rank_endpoints(content)

        # Update FileJob (keep existing fields for backward compatibility)
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
        file_job.total_endpoints = endpoint_data["total_endpoints"]
        file_job.top_endpoints = json.dumps(endpoint_data["top_endpoints"])
        file_job.status = "completed"
        file_job.completed_at = datetime.utcnow()
        file_job.processing_time = calculate_processing_time(
            file_job.started_at,
            file_job.completed_at,
        )
        db.session.commit()

        # Step 11: Create LogInsight record with all computed insights
        save_log_insight(
            file_job=file_job,
            status_counts=status_counts,
            unique_client_ips=unique_client_ips,
            endpoint_data=endpoint_data,
            line_count=stats["line_count"],
        )

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