import os
from dotenv import load_dotenv

load_dotenv()

VENICE_API_KEY = os.getenv("VENICE_KEY")

if not VENICE_API_KEY:
    raise ValueError("VENICE_KEY environment variable is not set") 