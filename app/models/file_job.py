from datetime import datetime

from ..extensions import db


class FileJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)

    status = db.Column(db.String(50), default="queued")
    word_count = db.Column(db.Integer, nullable=True)
    line_count = db.Column(db.Integer, nullable=True)
    character_count = db.Column(db.Integer, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    status_200_count = db.Column(db.Integer, default=0)
    status_404_count = db.Column(db.Integer, default=0)
    status_500_count = db.Column(db.Integer, default=0)

    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    rq_job_id = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "file_job_id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "status": self.status,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "character_count": self.character_count,
            "processing_time": self.processing_time,
            "status_200_count": self.status_200_count,
            "status_404_count": self.status_404_count,
            "status_500_count": self.status_500_count,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "rq_job_id": self.rq_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
