from ..extensions import db  # import the SINGLE db instance
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)

    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="queued")
    result = db.Column(db.Integer, nullable=True)
    #Connecting Task to User, each task belongs to one user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    retry_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
      return{
	"task_id": self.id,
	"number": self.number,
	"status": self.status,
	"result": self.result,
	"user_id": self.user_id
    }


