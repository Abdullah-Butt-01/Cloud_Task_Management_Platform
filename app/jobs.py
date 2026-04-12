from .extensions import db
import time
from app.models.task import Task
import random

def process_report(task_id):

    """
    Example job: simulates processing a report for a task
    """
    task = Task.query.get(task_id)
    if not task:
        print(f"Task {task_id} not found!")
        return

    print(f"Processing report for Task {task_id}...")
    task.status = "processing"
    db.session.commit()

    # simulate work
    time.sleep(5)

    task.status = "done"
    db.session.commit()
    print(f"Task {task_id} completed!")


def background_job(task_id, n, delay):

    task = Task.query.get(task_id)

    #if task.status != "queued":
     #   return

    try:
        print(f"Starting task {task_id}")

        task.status = "started"
        db.session.commit()

        time.sleep(delay)

        # 🔥 failure simulation
        if n == 5:
            raise Exception("Simulated failure")

        result = n * n

        task.status = "finished"
        task.result = result
        db.session.commit()
        print(f"Task {n} completed")
        return result



    except Exception:
        task.status = "failed"
        db.session.commit()
        print(f"Task {n} failed!")
        return None
