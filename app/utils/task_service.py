from app.extensions import db
from app.models.task import Task
from datetime import datetime, timedelta
import logging

def mark_stale_tasks():
    logging.info("⌚Scheduler tick: Checking stale tasks")
    stale_time = datetime.utcnow() - timedelta(minutes=5)

    stuck_tasks = Task.query.filter(
       Task.status == "started",
       Task.started_at < stale_time
    ).all()

    for task in stuck_tasks:
      task.status = "failed"

    db.session.commit()

    logging.info(f"Found stale tasks: {len(stuck_tasks)}")
