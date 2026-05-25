from flask import Flask
from .extensions import db

from sqlalchemy.exc import OperationalError
import time

from app.config import DATABASE_URL
from app.utils.logger import setup_logger

def create_app(): # Instead creating globally, create inside function to avoid circular imports
    app = Flask(__name__)
    print("create_app() is running")

    setup_logger()

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # SQLAlchemy tracking (changes in memory)

    db.init_app(app)  # before this, Flask and DB exists but not connected

    # import models AFTER db.init_app (database instance should exist first)
    from app.models.file_job import FileJob

    from app.scheduler import start_scheduler
    start_scheduler(app)

    # --- Wait for DB to be ready ---
    for i in range(10):  # try 10 times
        try:
            with app.app_context():
                db.create_all()  # creates tables if not exist
            print("✅ DB connected")
            break
        except OperationalError:
            print("⏳ DB not ready, retrying in 2 seconds...")
            time.sleep(2)
    # -------------------------------


    # import and register blueprints
    from app.routes.system_routes import system_bp
    app.register_blueprint(system_bp) # add system routes to the application

    from app.routes.file_routes import file_bp
    app.register_blueprint(file_bp)

    ''' create tables (for development)
    with app.app_context():
        db.create_all()
'''
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)






