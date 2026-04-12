from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue
import os

'''
# Host + Port Method
redis_url = os.getenv("REDIS_URL", "redis") #use env value if available otherwise use 'redis' as backup
redis_conn = Redis(host=redis_url, port=6379)
'''

# URL Method
redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)

queue = Queue(connection=redis_conn)


db = SQLAlchemy()
