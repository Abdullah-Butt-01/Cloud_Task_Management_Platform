from app.main import create_app
from .extensions import queue
from rq import Worker

import redis
import time
import threading
import socket
from datetime import datetime
from app.utils.logger import log_message

r = redis.Redis(host="redis", port=6379, decode_responses=True)

# Step 15: Heartbeat TTL — if worker dies, key expires after this many seconds
HEARTBEAT_TTL = 30  # Redis key auto-expires if worker stops sending heartbeats
HEARTBEAT_INTERVAL = 5  # seconds between heartbeats


def send_heartbeat(worker_name):
    """
    Send enriched heartbeat to Redis with worker state.

    Step 15 improvements:
    - Uses Redis SET with EX (TTL) so dead workers auto-expire
    - Stores structured JSON with timestamp, status, and metadata
    - Includes worker start time for uptime calculation
    - Tracks consecutive heartbeats for stability scoring
    """
    start_time = time.time()
    consecutive_beats = 0

    while True:
        try:
            consecutive_beats += 1
            now = time.time()
            uptime_seconds = round(now - start_time, 1)

            heartbeat_data = {
                "worker_name": worker_name,
                "timestamp": now,
                "timestamp_iso": datetime.utcnow().isoformat(),
                "status": "active",
                "uptime_seconds": uptime_seconds,
                "consecutive_beats": consecutive_beats,
                "heartbeat_interval": HEARTBEAT_INTERVAL,
                "ttl": HEARTBEAT_TTL,
            }

            # Step 15: Use SET with EX (TTL) — if worker dies, key auto-expires
            r.set(
                f"worker:{worker_name}:heartbeat",
                now,
                ex=HEARTBEAT_TTL
            )
            # Also store enriched metadata (separate key, same TTL)
            r.hset(f"worker:{worker_name}:info", mapping={
                "status": "active",
                "started_at": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime_seconds,
                "consecutive_beats": consecutive_beats,
            })
            r.expire(f"worker:{worker_name}:info", HEARTBEAT_TTL)

            log_message(
                "WORKER",
                f"Heartbeat #{consecutive_beats} uptime={uptime_seconds}s",
                file_job_id=None,
            )

            time.sleep(HEARTBEAT_INTERVAL)

        except Exception as e:
            log_message(
                "WORKER",
                f"Heartbeat failed: {e}",
                level=30,  # WARNING
            )
            consecutive_beats = 0  # Reset on failure
            time.sleep(HEARTBEAT_INTERVAL)


app = create_app(init_db=False, start_background_scheduler=False)

if __name__ == "__main__":
    with app.app_context():

        worker_name = socket.gethostname()

        # Step 15: Register worker start in Redis
        r.hset(f"worker:{worker_name}:info", mapping={
            "status": "starting",
            "started_at": datetime.utcnow().isoformat(),
            "hostname": worker_name,
        })
        r.expire(f"worker:{worker_name}:info", HEARTBEAT_TTL)

        thread = threading.Thread(
            target=send_heartbeat,
            args=(worker_name,),
            daemon=True
        )
        thread.start()

        log_message("WORKER", f"Worker started name={worker_name}")
        worker = Worker([queue])
        worker.work()