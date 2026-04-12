from flask import Blueprint, request, jsonify
from ..extensions import db, redis_conn, queue
from redis import Redis
import os

from rq.job import Job

from app.models.task import Task
from app.models.user import User

from app.jobs import background_job, process_report

import logging
logging.basicConfig(level=logging.INFO)

rapp = Blueprint("tasks", __name__)

@rapp.route("/tasks", methods=["POST"])
def create_task():
    data = request.json
    task = Task(title=data["title"])
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created"})

@rapp.route("/tasks", methods=["GET"])
def list_tasks():
    tasks = Task.query.all()  # ✅ now works
    result = [{"id": t.id, "title": t.title, "completed": t.completed, "result": t.result} for t in tasks]
    return jsonify(result)


@rapp.route("/")
def home():
    count = redis_conn.incr("hits")
    return {"message": f"Task Platform API running - visit: {count}"}


''' First route /<task/<int:n>
@tasks_bp.route("/task/<int:n>")
def add_task(n):
    print(f"Received task {n}")
    job = queue.enqueue(background_job, n)
    return {"message": f"Task {n} added to queue", "job_id": job.id}
'''

''' Second route /task/<int:n> for dynamic delay
@tasks_bp.route("/task/<int:n>")
def run_task(n):
    delay = request.args.get("delay", default=5, type=int)

    job = queue.enqueue(background_job, n, delay)

    return {
        "message": f"Task {n} added with delay {delay}",
        "job_id": job.id
    }
'''

''' Third route /task/<int:n> for adding task to database
@rapp.route("/task/<int:n>")
def run_task(n):
    delay = request.args.get("delay", default=5, type=int)

    # 1. Create DB record
    task = Task(number=n, status="queued")
    db.session.add(task)
    db.session.commit()

    # 2. Send to worker (IMPORTANT: pass task.id)
    job = queue.enqueue(background_job, task.id, n, delay)

    return {
        "task_id": task.id,
        "job_id": job.id
    }
'''

''' Fourth route /task/<int:n> for connecting task and user
@rapp.route("/task/<int:n>")
def run_task(n):
    delay = request.args.get("delay", default=5, type=int)
    user_id = request.args.get("user_id", type=int)

    print("DEBUG user_id: ", user_id)

    # 🔥 check if user exists
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    # create task linked to user
    task = Task(number=n, status="queued", user_id=user_id)
    db.session.add(task)
    db.session.commit()

    # send to worker
    job = queue.enqueue(background_job, task.id, n, delay)

    return {
        "task_id": task.id,
        "user_id": user_id,
        "job_id": job.id
    }
'''

# Fifth route /task/n For new worker job >jobs.py
@rapp.route("/task/<int:n>")
def run_task(n):
    logging.info(f"[API] Received task request: n={n}")

    user_id = request.args.get("user_id", type=int)
    logging.info(f"[API] User ID: {user_id}")

    job_type = request.args.get("type", default="square")

    task = Task(number=n, status="queued", user_id=user_id)
    db.session.add(task)
    db.session.commit()

    if job_type == "report":
        job = queue.enqueue(process_report, task.id)
    else:
        job = queue.enqueue(background_job, task.id, n, 5)

    logging.info(f"[API] Task {task.id} queued with job-id {job.id}")

    return {"task_id": task.id, "job_id": job.id, "type": job_type}


@rapp.route("/task/status/<job_id>")
def task_status(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "result": job.result
        }
    except Exception as e:
        return {"error": str(e)}, 404


