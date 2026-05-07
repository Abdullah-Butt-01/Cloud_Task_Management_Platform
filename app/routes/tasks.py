from flask import Blueprint, request, jsonify, render_template
from ..extensions import db, redis_conn, queue
from redis import Redis
import time
import os

from rq.job import Job

from app.models.task import Task
from app.models.user import User

from app.jobs import background_job, process_report

from app.utils.response import success_response, error_response
from app.utils.task_service import mark_stale_tasks
from app.utils.logger import log_message
import logging

rapp = Blueprint("tasks", __name__)
r = Redis(host="redis", port=6379, decode_responses=True)

@rapp.route("/")
def home():
    count = redis_conn.incr("hits")
    return {"message": f"Task Platform API running - visit: {count}"}



@rapp.route("/task", methods=["POST"])
def create_task():

    data = request.json

    n = data.get("n")
    user_id = data.get("user_id")
    job_type = data.get("type", "square")
    delay = data.get("delay", 5)

    #logging.info(f"[API] Creating task n={n}, user={user_id}, type={job_type}")
    log_message(
      "API",
      "Task request received",
      user_id=user_id
    )

    task = Task(number=n, status="queued", user_id=user_id)
    db.session.add(task)
    db.session.commit()
    #logging.info(f"[API] Task {task.id} queued job-id={job.id}")
    log_message(
      "API",
      "Task queued",
      task_id=task.id,
      user_id=user_id
    )

    if job_type == "report":
        job = queue.enqueue(process_report, task.id)
        logging.info(f"[API] Task-id {task.id} Sent to Worker")
    else:
        job = queue.enqueue(background_job, task.id, n, delay)
        logging.info(f"[API] Task-id {task.id} Sent to Worker")

    return {
      "task_id": task.id,
      "job_id": job.id,
      "type": job_type
    }



@rapp.route("/tasks", methods=["GET"])
def list_tasks():
    tasks = Task.query.all()  # ✅ now works

    if not tasks:
      return success_response([])

    data = [t.to_dict() for t in tasks]

    return success_response(data)




@rapp.route("/task/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return error_response("Task not found", 404)

    return success_response(task.to_dict())


@rapp.route("/debug/tasks", methods=["GET"])
def debug_tasks():
    status = request.args.get("status")

    query = Task.query

    if status:
      query = query.filter_by(status=status)

    tasks = query.all()

    data = []

    total = len(tasks)
    finished = len([t for t in tasks if t.status == "finished"])
    failed = len([t for t in tasks if t.status == "failed"])

    for task in tasks:
      data.append({
        "id": task.id,
        "number": task.number,
        "status": task.status,
        "result": task.result,
        "user_id": task.user_id,
        "retry_count": task.retry_count
      })

    return success_response({
      "summary": {
	"total": total,
	"finished": finished,
	"failed": failed
      },
      "tasks": data
    })


@rapp.route("/debug/workers", methods=["GET"])
def debug_workers():
    keys = r.keys("worker:*:heartbeat")

    workers = []

    for key in keys:
      worker_name = key.split(":")[1]
      last_seen = float(r.get(key))

      alive = (time.time() - last_seen) < 10

      workers.append({
        "worker": worker_name,
        "last_seen": last_seen,
        "status":"alive" if alive else "dead"
      })
    return success_response(workers)


@rapp.route("/dashboard")
def dashboard():
    tasks = Task.query.order_by(Task.id.desc()).all()

    return render_template("dashboard.html", tasks=tasks)
