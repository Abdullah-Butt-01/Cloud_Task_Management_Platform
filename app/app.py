from flask import Flask
from app import db
import os # For reading Environment variables (env)

import redis

redis_host = os.getenv("REDIS_HOST", "redis")
r = redis.Redis(host=redis_host, port=6379)

def create_app(): # Instead creatting globally, create inside function to avoid circular imports
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@db:5432/tasks"
    ) # If env exists, use it otherwise use default value
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # SQLAlchemy tracking (changes in memory)

    db.init_app(app)  # before this, Flask and DB exists but not connected

    # import models AFTER db.init_app (database instance should exist first)
    from app.models.task import Task 

    # import and register blueprints
    from app.routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp) # add routes to the application

    # create tables (for development)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        count = r.incr("hits")
        return {"message": f"Task Platform API running - visit: {count}"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
