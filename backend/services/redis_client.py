import redis
import json

class RedisClient:
    def __init__(self, host="localhost", port=6379):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def set_intent(self, intent: dict):
        self.r.set("intent", json.dumps(intent))

    def get_intent(self):
        data = self.r.get("intent")
        return json.loads(data) if data else None

redis_client = RedisClient()
