from flask import Flask
from .extensions import db
import os # For reading Environment variables (env)

from sqlalchemy.exc import OperationalError
import time
#time.sleep(10)

def create_app(): # Instead creatting globally, create inside function to avoid circular imports
    app = Flask(__name__)

    print("Create_app is running")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@db:5432/tasks"
    ) # If env exists, use it otherwise use default value
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # SQLAlchemy tracking (changes in memory)

    db.init_app(app)  # before this, Flask and DB exists but not connected

    # import models AFTER db.init_app (database instance should exist first)
    from app.models.task import Task
    from app.models.user import User

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
    from app.routes.tasks import rapp
    app.register_blueprint(rapp) # add routes to the application

    ''' create tables (for development)
    with app.app_context():
        db.create_all()
'''
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)






