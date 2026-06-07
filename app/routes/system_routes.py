from datetime import datetime

from flask import Blueprint
from redis import Redis

from ..extensions import queue, redis_conn
from app.jobs import generate_file_report
from app.utils.response import success_response

system_bp = Blueprint("system", __name__)
r = Redis(host="redis", port=6379, decode_responses=True)


@system_bp.route("/")
def home():
    count = redis_conn.incr("hits")
    return {
        "message": "Log Processing API running",
        "visit": count,
        "upload_endpoint": "POST /upload",
        "files_endpoint": "GET /files",
        "insights_endpoint": "GET /insights",
        "metrics_endpoint": "GET /metrics",
        "queue_endpoint": "GET /queue/status",
        "health_endpoint": "GET /health"
    }


@system_bp.route("/debug/workers", methods=["GET"])
def debug_workers():
    """
    Step 15: Improved worker heartbeat monitoring.

    Uses Redis TTL to detect stale workers automatically.
    Returns enriched worker state with uptime and stability info.
    """
    keys = r.keys("worker:*:heartbeat")
    workers = []
    now = datetime.utcnow().timestamp()

    for key in keys:
        worker_name = key.split(":")[1]

        # Step 15: Check TTL to detect stale workers
        ttl = r.ttl(key)
        last_seen_raw = r.get(key)

        if last_seen_raw is None:
            # Key expired — worker is dead or never started properly
            workers.append({
                "worker": worker_name,
                "status": "dead",
                "last_seen": None,
                "seconds_since_heartbeat": None,
                "ttl_remaining": 0,
                "uptime_seconds": None,
                "consecutive_beats": None,
                "reason": "Redis key expired — worker stopped sending heartbeats",
            })
            continue

        last_seen = float(last_seen_raw)
        seconds_since = round(now - last_seen, 1)

        # Step 15: Get enriched metadata from hash
        info = r.hgetall(f"worker:{worker_name}:info") or {}
        uptime = info.get("uptime_seconds")
        beats = info.get("consecutive_beats")
        started_at = info.get("started_at")

        # Step 15: Status logic using TTL, not just time comparison
        if ttl <= 0:
            status = "dead"
        elif seconds_since > 15:
            status = "stale"
        else:
            status = "active"

        workers.append({
            "worker": worker_name,
            "status": status,
            "last_seen": last_seen,
            "last_seen_iso": datetime.utcfromtimestamp(last_seen).isoformat(),
            "seconds_since_heartbeat": seconds_since,
            "ttl_remaining": ttl,
            "uptime_seconds": float(uptime) if uptime else None,
            "consecutive_beats": int(beats) if beats else None,
            "started_at": started_at,
        })

    # Step 15: Also check for workers that have info but no heartbeat (starting up)
    info_keys = r.keys("worker:*:info")
    for info_key in info_keys:
        worker_name = info_key.split(":")[1]
        heartbeat_key = f"worker:{worker_name}:heartbeat"
        if heartbeat_key not in keys:
            info = r.hgetall(info_key) or {}
            workers.append({
                "worker": worker_name,
                "status": "starting",
                "last_seen": None,
                "seconds_since_heartbeat": None,
                "ttl_remaining": r.ttl(info_key),
                "uptime_seconds": None,
                "consecutive_beats": None,
                "started_at": info.get("started_at"),
                "reason": "Worker registered but heartbeat not yet active",
            })

    return success_response(workers)


@system_bp.route("/reports/files", methods=["POST"])
def create_file_report():
    job = queue.enqueue(generate_file_report)

    return success_response(
        {
            "message": "File report job queued",
            "job_id": job.id,
        },
        202,
    )
