from uuid import uuid4
import os
import logging

from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename

from app.config import UPLOAD_FOLDER
from app.extensions import db, queue
from app.jobs import process_text_file
from app.models.file_job import FileJob
from app.utils.logger import log_message
from app.utils.response import error_response, success_response

file_bp = Blueprint("files", __name__)

ALLOWED_EXTENSIONS = {".txt", ".log"}


def is_supported_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@file_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        log_message("API", "Upload failed: no file field", level=logging.WARNING)
        return error_response("No file uploaded", 400)

    file = request.files["file"]

    log_message("API", f"Upload started filename={file.filename}")

    if file.filename == "":
        log_message("API", "Upload failed: empty filename", level=logging.WARNING)
        return error_response("Empty filename", 400)

    if not is_supported_file(file.filename):
        log_message(
            "API",
            f"Upload failed: unsupported file type filename={file.filename}",
            level=logging.WARNING,
        )
        return error_response("Only .txt and .log files are allowed", 400)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    original_filename = secure_filename(file.filename)
    stored_filename = f"{uuid4().hex}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, stored_filename)
    file.save(file_path)

    file_job = FileJob(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        status="queued",
    )

    db.session.add(file_job)
    db.session.commit()

    rq_job = queue.enqueue(process_text_file, file_job.id)
    file_job.rq_job_id = rq_job.id
    db.session.commit()

    log_message(
        "API",
        f"Job queued rq_job_id={rq_job.id} filename={original_filename}",
        file_job_id=file_job.id,
    )

    return success_response(
        {
            "message": "File uploaded and queued for processing",
            "file_job": file_job.to_dict(),
        },
        202,
    )


@file_bp.route("/files", methods=["GET"])
def list_file_jobs():
    status = request.args.get("status")

    query = FileJob.query

    if status:
        query = query.filter_by(status=status)

    file_jobs = query.order_by(FileJob.created_at.desc()).all()

    return success_response([file_job.to_dict() for file_job in file_jobs])


@file_bp.route("/files/<int:file_job_id>", methods=["GET"])
def get_file_job(file_job_id):
    file_job = FileJob.query.get(file_job_id)

    if not file_job:
        return error_response("File job not found", 404)

    return success_response(file_job.to_dict())


@file_bp.route("/dashboard")
def dashboard():
    file_jobs = FileJob.query.order_by(FileJob.id.desc()).all()

    return render_template("dashboard.html", file_jobs=file_jobs)
