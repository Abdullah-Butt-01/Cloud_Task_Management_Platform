from app.main import create_app
from .extensions import queue
from rq import Worker

import redis
import time
import threading
import socket

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def send_heartbeat(worker_name):
    while True:
      print(f"heartbeat from {worker_name}")
      r.set(f"worker:{worker_name}:heartbeat", time.time())
      time.sleep(5)

app = create_app()

if __name__ == "__main__":
    with app.app_context():

        worker_name = socket.gethostname()

        thread = threading.Thread(
	  target=send_heartbeat,
	  args=(worker_name,),
	  daemon=True
        )
        thread.start()

        worker = Worker([queue])
        worker.work()
