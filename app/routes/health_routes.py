from datetime import datetime
from flask import Blueprint

from app.extensions import db, redis_conn, queue
from app.utils.logger import log_message
from app.utils.response import success_response, error_response

health_bp = Blueprint("health", __name__)


def check_database():
    """Check PostgreSQL connectivity by executing a simple query."""
    try:
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))
        return {
            "status": "up",
            "latency_ms": None,  # Could be measured with time.perf_counter
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
        }


def check_redis():
    """Check Redis connectivity by executing PING."""
    try:
        redis_conn.ping()
        return {
            "status": "up",
            "latency_ms": None,
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
        }


def check_workers():
    """Check worker health via heartbeat keys in Redis."""
    try:
        from redis import Redis
        r = Redis(host="redis", port=6379, decode_responses=True)

        keys = r.keys("worker:*:heartbeat")
        total_workers = len(keys)

        if total_workers == 0:
            return {
                "status": "down",
                "total_workers": 0,
                "active_workers": 0,
                "error": "No worker heartbeat keys found",
            }

        active_workers = 0
        stale_workers = 0
        now = datetime.utcnow().timestamp()

        for key in keys:
            ttl = r.ttl(key)
            last_seen_raw = r.get(key)

            if last_seen_raw is None or ttl <= 0:
                continue  # Dead worker, key expired

            last_seen = float(last_seen_raw)
            seconds_since = now - last_seen

            if seconds_since < 15:
                active_workers += 1
            else:
                stale_workers += 1

        if active_workers == 0:
            return {
                "status": "degraded",
                "total_workers": total_workers,
                "active_workers": 0,
                "stale_workers": stale_workers,
                "error": "All workers are stale or dead",
            }

        return {
            "status": "up",
            "total_workers": total_workers,
            "active_workers": active_workers,
            "stale_workers": stale_workers,
        }

    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
        }


def check_queue():
    """Check RQ queue is accessible."""
    try:
        pending = queue.count
        return {
            "status": "up",
            "pending_jobs": pending,
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
        }


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Step 17: Service health monitoring endpoint.

    Checks:
      - Database (PostgreSQL) — simple SELECT 1
      - Redis (cache + queue broker) — PING
      - Workers — heartbeat key presence and freshness
      - Queue — RQ queue accessibility

    Returns overall status:
      - "healthy" — all services up
      - "degraded" — one or more services down but system functional
      - "unhealthy" — critical services down (DB or Redis)
    """
    timestamp = datetime.utcnow().isoformat()

    db_check = check_database()
    redis_check = check_redis()
    worker_check = check_workers()
    queue_check = check_queue()

    # Determine overall status
    critical_services = [db_check["status"], redis_check["status"]]

    if "down" in critical_services:
        overall_status = "unhealthy"
    elif any(check["status"] != "up" for check in [db_check, redis_check, worker_check, queue_check]):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    health = {
        "timestamp": timestamp,
        "status": overall_status,
        "version": "1.0.0",
        "services": {
            "database": db_check,
            "redis": redis_check,
            "workers": worker_check,
            "queue": queue_check,
        },
    }

    log_message(
        "API",
        f"Health check: status={overall_status} db={db_check['status']} redis={redis_check['status']} workers={worker_check.get('active_workers', 0)}/{worker_check.get('total_workers', 0)}"
    )

    # Return 503 if unhealthy, 200 otherwise
    status_code = 503 if overall_status == "unhealthy" else 200

    return success_response(health), status_code