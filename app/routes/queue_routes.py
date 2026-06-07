from flask import Blueprint
from sqlalchemy import func

from app.extensions import db, queue
from app.models.file_job import FileJob
from app.utils.logger import log_message
from app.utils.response import success_response

queue_bp = Blueprint("queue", __name__)


@queue_bp.route("/queue/status", methods=["GET"])
def queue_status():
    """
    Step 16: Queue monitoring endpoint.

    Shows:
      - RQ queue size (pending jobs in Redis)
      - Job counts by status in database
      - Estimated throughput (completed jobs per hour)
      - Queue health signal
    """
    # RQ queue metrics
    pending_rq_jobs = queue.count

    # Database job breakdown
    total_jobs = FileJob.query.count()
    queued_db = FileJob.query.filter_by(status="queued").count()
    processing_db = FileJob.query.filter_by(status="processing").count()
    completed_db = FileJob.query.filter_by(status="completed").count()
    failed_db = FileJob.query.filter_by(status="failed").count()

    # Throughput estimate: completed jobs in last hour
    from datetime import datetime, timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_completed = FileJob.query.filter(
        FileJob.status == "completed",
        FileJob.completed_at >= one_hour_ago
    ).count()

    # Health signal
    if pending_rq_jobs == 0 and queued_db == 0:
        health = "idle"
    elif pending_rq_jobs > 0 and processing_db == 0:
        health = "backlogged"  # Jobs waiting but no workers processing
    elif pending_rq_jobs > 10:
        health = "overloaded"
    else:
        health = "healthy"

    # Worker capacity estimate (rough: if 1 worker ~ 1 job/minute)
    estimated_clear_time = None
    if pending_rq_jobs > 0:
        # Assume 1 job per minute per worker (conservative)
        # This is a rough estimate; real throughput varies by file size
        estimated_clear_time = f"{pending_rq_jobs} minutes (1 worker)"

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "rq_queue": {
            "pending_jobs": pending_rq_jobs,
        },
        "database": {
            "total_jobs": total_jobs,
            "queued": queued_db,
            "processing": processing_db,
            "completed": completed_db,
            "failed": failed_db,
        },
        "throughput": {
            "completed_last_hour": recent_completed,
            "estimated_clear_time": estimated_clear_time,
        },
        "health": health,
    }

    log_message(
        "API",
        f"Queue status: pending={pending_rq_jobs} health={health} throughput={recent_completed}/hour"
    )

    return success_response(metrics)