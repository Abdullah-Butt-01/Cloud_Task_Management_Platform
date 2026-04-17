from .extensions import db
import time
from app.models.task import Task
import random

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

MAX_RETRIES = 3

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
    logging.info(f"[WORKER] [TASK {task_id}] with n={n} START")

    task = Task.query.get(task_id)

    if not task:
      logging.error(f"[WORKER] [TASK {task_id}] Task not found")
      return

    try:
        task.status = "started"
        db.session.commit()
        logging.info(f"[WORKER] [TASK {task_id}] status: started")

        time.sleep(delay)

        # 🔥 failure simulation
        if n == 5:
            raise Exception("Simulated failure")

        result = n * n

        task.status = "finished"
        task.result = result
        db.session.commit()
        logging.info(f"[WORKER] [TASK {task_id}] status: finished")

        logging.info(f"[WORKER] [TASK {task_id}] SUCCESS")

        return result



    except Exception as e:
        task.status = "failed"
        db.session.commit()
        logging.error(f"[WORKER] [Task {task_id}] FAILED : {e}")

        task.retry_count += 1

        if task.retry_count < MAX_RETRIES:
          logging.info(f"[WORKER] [TASK {task_id}] RETRY {task.retry_count}")

          db.session.commit()
          # Retry
          background_job(task_id, n, delay)

        else:
          task.status = "failed"
          db.session.commit()

          logging.error(f"[WORKER] [TASK {task_id}] PERMANENT FAILURE")
        return None
