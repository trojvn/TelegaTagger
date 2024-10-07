import os
from pathlib import Path

from dotenv import load_dotenv

_env_file = Path(".env")
if not _env_file.is_file():
    _env_file = Path("settings.env")
    if not _env_file.is_file():
        _env_file = Path("env.txt")

load_dotenv(_env_file)
LICENSE_KEY = os.getenv("LICENSE_KEY", "")
DEBUG = os.getenv("DEBUG", "")
