from ..extensions import db  # import the SINGLE db instance

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)

    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="queued")
    result = db.Column(db.Integer, nullable=True)

    #Connecting Task to User, each task belongs to one user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
