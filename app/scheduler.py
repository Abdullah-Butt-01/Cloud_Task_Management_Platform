from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.task_service import mark_stale_tasks
import os
import logging

#logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_scheduler_job(app):
    with app.app_context():
      mark_stale_tasks()

def start_scheduler(app):

    #if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    #  return

    scheduler.add_job(lambda: run_scheduler_job(app), trigger="interval", minutes=1)

    scheduler.start()
    logging.info("🚀scheduler_started")

