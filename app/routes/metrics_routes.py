from datetime import datetime
from flask import Blueprint
from sqlalchemy import func

from app.extensions import db, queue, redis_conn
from app.models.file_job import FileJob
from app.models.log_insight import LogInsight
from app.utils.logger import log_message
from app.utils.response import success_response

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def system_metrics():
    """
    System-wide processing pipeline metrics.

    Returns:
      - Job counts by status (queued, processing, completed, failed)
      - Total files processed
      - Average processing time
      - Total errors across all jobs
      - Insight health distribution
      - Queue size (Redis)
      - Worker count (from heartbeat keys)
      - System uptime signal (Redis hit counter)
    """
    now = datetime.utcnow()

    # --- Job Pipeline Metrics ---
    total_jobs = FileJob.query.count()
    queued_jobs = FileJob.query.filter_by(status="queued").count()
    processing_jobs = FileJob.query.filter_by(status="processing").count()
    completed_jobs = FileJob.query.filter_by(status="completed").count()
    failed_jobs = FileJob.query.filter_by(status="failed").count()

    avg_processing_time = db.session.query(
        func.avg(FileJob.processing_time)
    ).filter(FileJob.status == "completed").scalar()

    total_retries = db.session.query(func.sum(FileJob.retry_count)).scalar() or 0

    # --- Error Metrics ---
    total_errors = db.session.query(func.sum(FileJob.total_error_count)).scalar() or 0
    total_client_errors = db.session.query(func.sum(FileJob.client_error_count)).scalar() or 0
    total_server_errors = db.session.query(func.sum(FileJob.server_error_count)).scalar() or 0

    # --- Insight Health Metrics ---
    total_insights = LogInsight.query.count()
    healthy_insights = LogInsight.query.filter_by(health_status="healthy").count()
    degraded_insights = LogInsight.query.filter_by(health_status="degraded").count()
    unhealthy_insights = LogInsight.query.filter_by(health_status="unhealthy").count()

    avg_health_score = db.session.query(func.avg(LogInsight.health_score)).scalar()

    # --- Queue Metrics ---
    queue_size = queue.count

    # --- Worker Metrics ---
    from redis import Redis
    r = Redis(host="redis", port=6379, decode_responses=True)
    worker_keys = r.keys("worker:*:heartbeat")
    worker_count = len(worker_keys)

    alive_workers = 0
    dead_workers = 0
    for key in worker_keys:
        last_seen = float(r.get(key))
        if (now.timestamp() - last_seen) < 10:
            alive_workers += 1
        else:
            dead_workers += 1

    # --- System Signal ---
    api_hits = redis_conn.get("hits") or 0

    metrics = {
        "timestamp": now.isoformat(),
        "jobs": {
            "total": total_jobs,
            "queued": queued_jobs,
            "processing": processing_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "success_rate": round(
                (completed_jobs / total_jobs) * 100, 1
            ) if total_jobs else 0,
            "average_processing_time": round(float(avg_processing_time), 3) if avg_processing_time else None,
            "total_retries": int(total_retries),
        },
        "errors": {
            "total": int(total_errors),
            "client_errors": int(total_client_errors),
            "server_errors": int(total_server_errors),
        },
        "insights": {
            "total": total_insights,
            "healthy": healthy_insights,
            "degraded": degraded_insights,
            "unhealthy": unhealthy_insights,
            "average_health_score": round(float(avg_health_score), 3) if avg_health_score else None,
        },
        "queue": {
            "pending_jobs": queue_size,
        },
        "workers": {
            "total": worker_count,
            "alive": alive_workers,
            "dead": dead_workers,
        },
        "system": {
            "api_hits": int(api_hits),
        },
    }

    log_message("API", f"Metrics generated: jobs={total_jobs} insights={total_insights} workers={alive_workers}/{worker_count}")

    return success_response(metrics)