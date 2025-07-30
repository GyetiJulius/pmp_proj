import redis
import json
import os
from dotenv import load_dotenv
import ssl
from upstash_redis import Redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("Missing UPSTASH_REDIS_URL in .env file.")


redis_client = Redis(url=os.getenv("UPSTASH_URL"), token=os.getenv("UPSTASH_TOKEN"))

def set_project_state(project_id: str, state: dict):
    """Stores the project state in Redis as a JSON string."""
    redis_client.set(f"project:{project_id}", json.dumps(state))

def get_project_state(project_id: str):
    """Retrieves and deserializes the project state from Redis."""
    state_json = redis_client.get(f"project:{project_id}")
    if state_json:
        return json.loads(state_json)
    return None