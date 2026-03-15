from flask import Flask
from app import db
import os

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/tasks"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)  # initialize db here

    # import models AFTER db.init_app
    from app.models.task import Task

    # import and register blueprints
    from app.routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp)

    # create tables (for development)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {"message": "Task Platform API running"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
