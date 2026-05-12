from datetime import datetime, timedelta
import logging

from app.extensions import db
from app.models.file_job import FileJob


def mark_stale_file_jobs():
    logging.info("Scheduler tick: checking stale file jobs")

    stale_time = datetime.utcnow() - timedelta(minutes=5)
    stale_jobs = FileJob.query.filter(
        FileJob.status == "processing",
        FileJob.started_at.isnot(None),
        FileJob.started_at < stale_time,
    ).all()

    for file_job in stale_jobs:
        file_job.status = "failed"
        file_job.error_message = "Processing timed out"
        file_job.completed_at = datetime.utcnow()

    db.session.commit()

    logging.info(f"Found stale file jobs: {len(stale_jobs)}")
