import os

from dotenv import load_dotenv

load_dotenv("settings.env")
API_URL = os.getenv("API_URL", "")
LICENSE_KEY = os.getenv("LICENSE_KEY", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PSWD = os.getenv("DB_PSWD", "")
