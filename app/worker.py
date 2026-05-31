from app.main import create_app
from .extensions import queue
from rq import Worker

import redis
import time
import threading
import socket
from app.utils.logger import log_message

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def send_heartbeat(worker_name):
    while True:
      log_message("WORKER", f"Heartbeat from {worker_name}")
      r.set(f"worker:{worker_name}:heartbeat", time.time())
      time.sleep(5)

app = create_app(init_db=False, start_background_scheduler=False)

if __name__ == "__main__":
    with app.app_context():

        worker_name = socket.gethostname()

        thread = threading.Thread(
	  target=send_heartbeat,
	  args=(worker_name,),
	  daemon=True
        )
        thread.start()

        log_message("WORKER", f"Worker started name={worker_name}")
        worker = Worker([queue])
        worker.work()
