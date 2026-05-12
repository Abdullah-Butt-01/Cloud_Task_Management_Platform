from datetime import datetime

from flask import Blueprint
from redis import Redis

from ..extensions import queue, redis_conn
from app.jobs import generate_file_report
from app.utils.response import success_response

rapp = Blueprint("system", __name__)
r = Redis(host="redis", port=6379, decode_responses=True)


@rapp.route("/")
def home():
    count = redis_conn.incr("hits")
    return {
        "message": "TXT File Processing API running",
        "visit": count,
        "upload_endpoint": "POST /upload",
        "files_endpoint": "GET /files",
    }


@rapp.route("/debug/workers", methods=["GET"])
def debug_workers():
    keys = r.keys("worker:*:heartbeat")
    workers = []

    for key in keys:
        worker_name = key.split(":")[1]
        last_seen = float(r.get(key))
        alive = (datetime.utcnow().timestamp() - last_seen) < 10

        workers.append(
            {
                "worker": worker_name,
                "last_seen": last_seen,
                "status": "alive" if alive else "dead",
            }
        )

    return success_response(workers)


@rapp.route("/reports/files", methods=["POST"])
def create_file_report():
    job = queue.enqueue(generate_file_report)

    return success_response(
        {
            "message": "File report job queued",
            "job_id": job.id,
        },
        202,
    )
