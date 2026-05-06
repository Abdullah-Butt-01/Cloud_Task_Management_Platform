import logging

def setup_logger():
    logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s | %(levelname)s | %(message)s",
    )

def log_message(component, message, task_id=None, user_id=None):

    base = f"[{component}]"

    if task_id:
      base += f" [TASK_ID={task_id}]"

    if user_id:
      base += f"USER={user_id}"

    base += f" {message}"

    logging.info(base)
