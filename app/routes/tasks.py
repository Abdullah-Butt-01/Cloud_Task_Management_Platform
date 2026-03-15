from flask import Blueprint, request, jsonify
from app.models.task import Task
from app import db

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    data = request.json
    task = Task(title=data["title"])
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created"})

@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    tasks = Task.query.all()  # ✅ now works
    result = [{"id": t.id, "title": t.title, "completed": t.completed} for t in tasks]
    return jsonify(result)
