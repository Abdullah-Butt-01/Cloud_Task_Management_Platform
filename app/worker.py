import time # pause execution
from redis import Redis
from rq import Worker, Queue # rq: RedisQueue
import os

redis_url = os.getenv("REDIS_HOST", "redis")
redis_conn = Redis(host=redis_url, port=6379)

queue = Queue(connection=redis_conn)

def background_job(n):
    print(f"Processing task: {n}")
    time.sleep(5)
    print(f"Task {n} done")
    return n * n

if __name__ == "__main__":
    worker = Worker([queue])
    worker.work()
