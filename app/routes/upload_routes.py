import os
from uuid import uuid4

from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename

from app.extensions import db, queue
from app.jobs import process_text_file
from app.models.file_job import FileJob
from app.utils.response import error_response, success_response

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSION = ".txt"


def is_txt_file(filename):
    return os.path.splitext(filename)[1].lower() == ALLOWED_EXTENSION


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return error_response("No file uploaded", 400)

    file = request.files["file"]

    if file.filename == "":
        return error_response("Empty filename", 400)

    if not is_txt_file(file.filename):
        return error_response("Only .txt files are allowed", 400)

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

    return success_response(
        {
            "message": "File uploaded and queued for processing",
            "file_job": file_job.to_dict(),
        },
        202,
    )


@upload_bp.route("/files", methods=["GET"])
def list_file_jobs():
    status = request.args.get("status")

    query = FileJob.query

    if status:
        query = query.filter_by(status=status)

    file_jobs = query.order_by(FileJob.created_at.desc()).all()

    return success_response([file_job.to_dict() for file_job in file_jobs])


@upload_bp.route("/files/<int:file_job_id>", methods=["GET"])
def get_file_job(file_job_id):
    file_job = FileJob.query.get(file_job_id)

    if not file_job:
        return error_response("File job not found", 404)

    return success_response(file_job.to_dict())


@upload_bp.route("/dashboard")
def dashboard():
    file_jobs = FileJob.query.order_by(FileJob.id.desc()).all()

    return render_template("dashboard.html", file_jobs=file_jobs)
