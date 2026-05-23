from datetime import datetime

from app.models.file_job import FileJob
from app.utils.logger import log_message


def generate_file_report():
    file_jobs = FileJob.query.all()

    report = {
        "total": len(file_jobs),
        "queued": len([job for job in file_jobs if job.status == "queued"]),
        "processing": len([job for job in file_jobs if job.status == "processing"]),
        "completed": len([job for job in file_jobs if job.status == "completed"]),
        "failed": len([job for job in file_jobs if job.status == "failed"]),
        "generated_at": datetime.utcnow().isoformat(),
    }

    log_message("WORKER", f"File report generated: {report}")

    return report
