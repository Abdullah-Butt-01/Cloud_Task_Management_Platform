from flask import request, Blueprint
import os
from app.utils.response import success_response, error_response

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = "app/uploads"

@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
      return error_response("No file uploaded", 400)

    file = request.files["file"]

    if file.filename == "":
      return error_response("Empty filename", 400)

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file.save(filepath)

    return success_response({
      "message": "File uploaded successfully",
      "filename": file.filename
    })
