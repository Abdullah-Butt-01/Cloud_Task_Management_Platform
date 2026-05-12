from ..extensions import db  # import the SINGLE db instance
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)

    status = db.Column(db.String(50), default="todo")
    priority = db.Column(db.String(20), default="medium")
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Legacy job-engine fields kept temporarily while the project transitions.
    number = db.Column(db.Integer, nullable=True, default=0)
    result = db.Column(db.Integer, nullable=True)

    #Connecting Task to User, each task belongs to one user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    retry_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
      return{
	"task_id": self.id,
	"title": self.title,
	"description": self.description,
	"status": self.status,
	"priority": self.priority,
	"completed": self.completed,
	"due_date": self.due_date.isoformat() if self.due_date else None,
	"created_at": self.created_at.isoformat() if self.created_at else None,
	"updated_at": self.updated_at.isoformat() if self.updated_at else None,
	"user_id": self.user_id
    }

