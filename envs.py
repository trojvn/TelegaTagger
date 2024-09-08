import os

from dotenv import load_dotenv

load_dotenv()
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PSWD = os.getenv("DB_PSWD", "")
