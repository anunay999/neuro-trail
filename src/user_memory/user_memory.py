import redis
from dotenv import load_dotenv
import os

load_dotenv()

# Use Docker's service name instead of localhost
REDIS_HOST = os.getenv("REDIS_HOST", "redis_service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


class UserMemory:
    def __init__(self, host='localhost', port=REDIS_PORT, db=0):
        self.client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        try:
            self.client.ping()
            print("✅ Connected to Redis!")
        except redis.ConnectionError:
            print(f"❌ Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}")

    def update_progress(self, user_id, book_title):
        self.client.sadd(f"user:{user_id}:books", book_title)

    def get_history(self, user_id):
        history = self.client.smembers(f"user:{user_id}:books")
        return [item.decode('utf-8') for item in history]

    def update_learning_summary(self, user_id, summary):
        """
        Appends a summary of the user's learning (their reflection on the LLM answer) to Redis.
        """
        self.client.rpush(f"user:{user_id}:learned", summary)

    def get_learning_history(self, user_id):
        summaries = self.client.lrange(f"user:{user_id}:learned", 0, -1)
        return [s.decode('utf-8') for s in summaries]