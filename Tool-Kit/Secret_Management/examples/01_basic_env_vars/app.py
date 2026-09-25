import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("API_KEY")
db_password = os.getenv("DB_PASSWORD")

if api_key:
    print("API Key loaded successfully (masking for security).")
else:
    print("API Key not found!")
