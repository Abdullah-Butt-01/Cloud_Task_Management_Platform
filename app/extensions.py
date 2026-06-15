from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue
from app.config import REDIS_URL

"""
# Host + Port Method
redis_url = os.getenv("REDIS_URL", "redis") #use env value if available otherwise use 'redis' as backup
redis_conn = Redis(host=redis_url, port=6379)
"""

# URL Method
redis_conn = Redis.from_url(REDIS_URL)

queue = Queue(connection=redis_conn)


db = SQLAlchemy()
