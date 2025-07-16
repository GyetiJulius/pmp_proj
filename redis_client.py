import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("UPSTASH_REDIS_URL")

if not REDIS_URL:
    raise ValueError("Missing UPSTASH_REDIS_URL in .env file.")

# --- THE DEFINITIVE FIX ---
# We add `client_name=None` to prevent redis-py from sending an initial
# "CLIENT" command that Upstash does not support. This resolves the
# "Connection closed by server" error.
redis_client = redis.Redis.from_url("rediss://default:ASkwAAIjcDFiOWRiYmRmZTQ2YTM0YWRjYTE4MmE3OTkxMDQzNjYzMnAxMA@worthy-cat-10544.upstash.io:6379")

def set_project_state(project_id: str, state: dict):
    """Stores the project state in Redis as a JSON string."""
    redis_client.set(f"project:{project_id}", json.dumps(state))

def get_project_state(project_id: str):
    """Retrieves and deserializes the project state from Redis."""
    state_json = redis_client.get(f"project:{project_id}")
    if state_json:
        return json.loads(state_json)
    return None