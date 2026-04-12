from app.main import create_app
from .extensions import queue
from rq import Worker

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        worker = Worker([queue])
        worker.work()
