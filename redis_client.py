import json
import os
from dotenv import load_dotenv
from upstash_redis import Redis

load_dotenv()

UPSTASH_URL = os.getenv("UPSTASH_URL") # Use the correct variable from your .env
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") # Use the correct variable from your .env

if not UPSTASH_URL or not UPSTASH_TOKEN:
    raise ValueError("Missing UPSTASH_REDIS_URL or UPSTASH_REDIS_TOKEN in .env file.")

redis_client = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)

def set_project_state(project_id: str, state: dict):
    """Stores the project state in Redis as a JSON string."""
    redis_client.set(f"project:{project_id}", json.dumps(state))

def get_project_state(project_id: str):
    """Retrieves and deserializes the project state from Redis."""
    state_json = redis_client.get(f"project:{project_id}")
    if state_json:
        return json.loads(state_json)
    return None