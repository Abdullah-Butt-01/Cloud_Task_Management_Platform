from datetime import datetime

from ..extensions import db


class LogInsight(db.Model):
    """
    Stores computed observability insights from processed log files.

    This model separates raw job metadata (FileJob) from computed analysis results,
    allowing insights to be queried, compared, and trended independently.
    """

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key linking back to the source file job
    file_job_id = db.Column(db.Integer, db.ForeignKey('file_job.id'), nullable=False, unique=True)
    file_job = db.relationship('FileJob', backref=db.backref('insight', uselist=False))

    # --- Traffic Volume ---
    total_requests = db.Column(db.Integer, default=0)
    total_lines = db.Column(db.Integer, default=0)

    # --- Status Code Breakdown ---
    status_200_count = db.Column(db.Integer, default=0)
    status_404_count = db.Column(db.Integer, default=0)
    status_500_count = db.Column(db.Integer, default=0)
    status_301_count = db.Column(db.Integer, default=0)
    status_302_count = db.Column(db.Integer, default=0)
    status_401_count = db.Column(db.Integer, default=0)
    status_403_count = db.Column(db.Integer, default=0)
    status_504_count = db.Column(db.Integer, default=0)

    # --- Error Categorization ---
    total_error_count = db.Column(db.Integer, default=0)
    client_error_count = db.Column(db.Integer, default=0)
    server_error_count = db.Column(db.Integer, default=0)

    # --- Client Analysis ---
    unique_client_count = db.Column(db.Integer, default=0)
    unique_client_ips = db.Column(db.Text, nullable=True)

    # --- Endpoint Analysis ---
    total_endpoints = db.Column(db.Integer, default=0)
    top_endpoints = db.Column(db.Text, nullable=True)

    # --- Health Summary ---
    health_score = db.Column(db.Float, nullable=True)
    health_status = db.Column(db.String(20), default="unknown")

    # --- Metadata ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def calculate_health_score(self):
        """
        Calculate a health score from 0.0 to 1.0 based on error rates.

        Formula: 1.0 - (total_errors / total_requests)
        If no requests, score is None.
        """
        if not self.total_requests or self.total_requests == 0:
            self.health_score = None
            self.health_status = "unknown"
            return

        error_rate = self.total_error_count / self.total_requests
        self.health_score = round(max(0.0, 1.0 - error_rate), 3)

        if self.health_score >= 0.95:
            self.health_status = "healthy"
        elif self.health_score >= 0.80:
            self.health_status = "degraded"
        else:
            self.health_status = "unhealthy"

    def _parse_top_endpoints(self):
        """Parse stored JSON back into list of dicts."""
        if not self.top_endpoints:
            return []
        import json
        try:
            return json.loads(self.top_endpoints)
        except json.JSONDecodeError:
            return []

    def _parse_client_ips(self):
        """Parse comma-separated IPs back into list."""
        if not self.unique_client_ips:
            return []
        return self.unique_client_ips.split(",")

    def to_dict(self):
        return {
            "insight_id": self.id,
            "file_job_id": self.file_job_id,

            # Traffic
            "total_requests": self.total_requests,
            "total_lines": self.total_lines,

            # Status codes
            "status_200_count": self.status_200_count,
            "status_404_count": self.status_404_count,
            "status_500_count": self.status_500_count,
            "status_301_count": self.status_301_count,
            "status_302_count": self.status_302_count,
            "status_401_count": self.status_401_count,
            "status_403_count": self.status_403_count,
            "status_504_count": self.status_504_count,

            # Errors
            "total_error_count": self.total_error_count,
            "client_error_count": self.client_error_count,
            "server_error_count": self.server_error_count,

            # Clients
            "unique_client_count": self.unique_client_count,
            "unique_client_ips": self._parse_client_ips(),

            # Endpoints
            "total_endpoints": self.total_endpoints,
            "top_endpoints": self._parse_top_endpoints(),

            # Health
            "health_score": self.health_score,
            "health_status": self.health_status,

            # Metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }