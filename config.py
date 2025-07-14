import os
from dotenv import load_dotenv

load_dotenv()

def get_cohere_api_key():
    key = os.getenv("COHERE_API_KEY")
    if not key:
        raise ValueError("COHERE_API_KEY not found in environment variables.")
    return key

def get_cerebras_api_key():
    key = os.getenv("CEREBRAS_API_KEY")
    if not key:
        raise ValueError("CEREBRAS_API_KEY not found in environment variables.")
    return key

def get_tavily_api_key():
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")
    return key

def get_google_api_key():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")
    return key
