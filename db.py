from pathlib import Path

from montywrapper import MontyUser

users = MontyUser(Path("database"), "users").collection
