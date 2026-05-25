import time

from flask import Flask
from sqlalchemy.exc import OperationalError

from app.config import DATABASE_URL
from app.extensions import db
from app.utils.logger import log_message, setup_logger


def create_app():
    app = Flask(__name__)

    setup_logger()
    log_message("API", "create_app() started")

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Import models after db.init_app so SQLAlchemy knows every table.
    from app.models.file_job import FileJob

    from app.scheduler import start_scheduler
    start_scheduler(app)

    for _ in range(10):
        try:
            with app.app_context():
                db.create_all()
            log_message("API", "Database connected")
            break
        except OperationalError:
            log_message("API", "Database not ready, retrying in 2 seconds")
            time.sleep(2)

    from app.routes.system_routes import system_bp
    app.register_blueprint(system_bp)

    from app.routes.file_routes import file_bp
    app.register_blueprint(file_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
