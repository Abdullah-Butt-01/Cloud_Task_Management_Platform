from datetime import datetime
import os
import logging

from app.extensions import db, queue
from app.models.file_job import FileJob
from app.utils.logger import log_message

MAX_RETRIES = 3


def count_text_stats(content):
    return {
        "word_count": len(content.split()),
        "line_count": len(content.splitlines()),
        "character_count": len(content),
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

        if not file_job.original_filename.lower().endswith(".txt"):
            raise ValueError("Only .txt files can be processed")

        with open(file_job.file_path, "r", encoding="utf-8") as text_file:
            content = text_file.read()

        stats = count_text_stats(content)

        file_job.word_count = stats["word_count"]
        file_job.line_count = stats["line_count"]
        file_job.character_count = stats["character_count"]
        file_job.status = "completed"
        file_job.completed_at = datetime.utcnow()
        db.session.commit()

        log_message("WORKER", "File processing completed", file_job_id=file_job.id)

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
            db.session.commit()

            log_message(
                "WORKER",
                f"File processing failed permanently: {error}",
                file_job_id=file_job.id,
                level=logging.ERROR,
            )

        return None
