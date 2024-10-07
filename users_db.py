import contextlib
from pathlib import Path

from db import users


class UsersDB:
    @property
    def count_users_from_db(self) -> int:
        return users.count_documents({})

    @property
    def count_free_users_from_db(self) -> int:
        return users.count_documents({"is_free": True})

    @staticmethod
    def load_users_from_file() -> tuple[int, int, int]:
        count, ok_count, error_count = 0, 0, 0
        for _user in UsersDB.__get_users_from_file():
            count += 1
            with contextlib.suppress(Exception):
                users.insert_one({"_id": _user, "is_free": True})
                ok_count += 1
                continue
            error_count += 1
        return count, ok_count, error_count

    @staticmethod
    def get_users_from_db(count: int) -> set[str]:
        _users = set()
        for options in users.find({"is_free": True}).limit(count):
            _users.add(options["_id"])
        if not _users:
            return set()
        users.update_many({"_id": {"$in": list(_users)}}, {"$set": {"is_free": False}})
        return _users

    @staticmethod
    def restore_users_from_db(_users: set[str]):
        users.update_many({"_id": {"$in": list(_users)}}, {"$set": {"is_free": True}})

    @staticmethod
    def write_success_users_to_db(_users: set[str]):
        users.update_many({"_id": {"$in": list(_users)}}, {"$set": {"is_good": True}})

    @staticmethod
    def __get_users_from_file() -> set[str]:
        users_file = Path("юзернеймы.txt")
        if not users_file.is_file():
            users_file.touch()
            return set()
        with users_file.open("r", encoding="utf-8") as f:
            _users = set(filter(None, [line.strip() for line in f.readlines()]))
        return _users

    @staticmethod
    def get_success_users_from_db() -> set[str]:
        _users = set()
        for options in users.find({"is_good": True}):
            _users.add(options["_id"])
        return _users

    @staticmethod
    def get_fails_users_from_db() -> set[str]:
        _users = set()
        for options in users.find({"is_free": False, "is_good": None}):
            _users.add(options["_id"])
        return _users

    @staticmethod
    def drop():
        users.drop()

    @staticmethod
    def write_fails_users_to_file(_users: set[str]):
        with Path("юзернеймы_неудачные.txt").open("w", encoding="utf-8") as f:
            {f.write(f"{user}\n") for user in _users}

    @staticmethod
    def write_success_users_to_file(_users: set[str]):
        with Path("юзернеймы_успешные.txt").open("w", encoding="utf-8") as f:
            {f.write(f"{user}\n") for user in _users}
