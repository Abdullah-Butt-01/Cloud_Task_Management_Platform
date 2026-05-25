import logging


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def log_message(
    component,
    message,
    task_id=None,
    user_id=None,
    file_job_id=None,
    level=logging.INFO,
):

    base = f"[{component}]"

    if task_id:
        base += f" [TASK_ID={task_id}]"

    if file_job_id:
        base += f" [FILE_JOB_ID={file_job_id}]"

    if user_id:
        base += f" [USER={user_id}]"

    base += f" {message}"

    logging.log(level, base)
