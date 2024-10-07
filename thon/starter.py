import asyncio
from asyncio import Semaphore
from pathlib import Path
from typing import Generator

from tooler import move_item

from base_session import BaseSession
from console import console
from thon.tagger import Tagger
from users_db import UsersDB

u = UsersDB()


class Starter(BaseSession):
    def __init__(
        self,
        fwd_from: str,
        fwd_index: int,
        users_count: int,
        threads: int,
        period: int | None,
    ):
        self.fwd_from, self.fwd_index = fwd_from, fwd_index - 1
        self.period = None if period == 0 else period
        self.semaphore = Semaphore(threads)
        self.users_count = users_count
        Tagger.is_donor_good = True
        super().__init__()

    async def _main(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        users: set[str],
    ):
        t = Tagger(
            item,
            json_file,
            json_data,
            self.fwd_from,
            users,
            self.fwd_index,
            self.period,
        )
        async with self.semaphore:
            if not Tagger.is_donor_good:
                return u.restore_users_from_db(users)
            r = await t.main()
        if "OK" not in r:
            u.restore_users_from_db(users)
            console.log(item.name, r, style="red")
        if "ERROR_AUTH" in r:
            move_item(item, self.banned_dir, True, True)
            move_item(json_file, self.banned_dir, True, True)
        if "ERROR_STORY" in r:
            move_item(item, self.errors_dir, True, True)
            move_item(json_file, self.errors_dir, True, True)
        if "OK" in r:
            if not (_users := set(filter(None, r.replace("OK:", "").split("|")))):
                _message = f"Опубликовано, но никого не упомянул {users}"
                return console.log(item.name, _message, style="yellow")
            u.write_success_users_to_db(_users)
            console.log(item.name, r, style="green")

    def __get_sessions_and_users(self) -> Generator:
        for item, json_file, json_data in self.find_sessions():
            if not u.count_free_users_from_db:
                return console.log("Нет юзернеймов для обработки!", style="yellow")
            if not (users := u.get_users_from_db(self.users_count)):
                return console.log("Нет юзернеймов для обработки!", style="yellow")
            yield item, json_file, json_data, users

    async def main(self) -> bool:
        if not Tagger.is_donor_good:
            return False
        tasks = set()
        for item, json_file, json_data, users in self.__get_sessions_and_users():
            tasks.add(self._main(item, json_file, json_data, users))
        if not tasks:
            return False
        await asyncio.gather(*tasks, return_exceptions=True)
        return True
