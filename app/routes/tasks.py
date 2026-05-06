from flask import Blueprint, request, jsonify
from ..extensions import db, redis_conn, queue
from redis import Redis
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
