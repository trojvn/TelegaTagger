import contextlib
from pathlib import Path
from random import shuffle
from shutil import move
from threading import Lock, Thread
from time import sleep

import httpx
from rich.prompt import Prompt

from ask_from_history import ask_from_history
from base_session import BaseSession
from console import console
from envs import API_URL, LICENSE_KEY

LOCKER = Lock()


class StoriesSender(BaseSession):
    def __init__(self, usernames: set[str]):
        BaseSession.__init__(self)

        self.__errors_path = Path("errors")
        self.__errors_path.mkdir(exist_ok=True)
        self.__banned_path = Path("banned")
        self.__banned_path.mkdir(exist_ok=True)
        self.__is_donor_good = True
        self.__is_license_good = True

        prompt = "Введите донора у кого брать сторис (например @durov)"
        self.__donor = ask_from_history(prompt, console, Path("history_donors.json"))

        prompt = "Какое сторис у донора забирать? (например 1)"
        self.__fwd_index_ask = Prompt.ask(prompt, console=console)
        if self.__fwd_index_ask.isdigit():
            self.__fwd_index = int(self.__fwd_index_ask) - 1
        else:
            self.__fwd_index = 0

        self.__black_list_path = Path("black_list.txt")
        self.__black_list = self.__check_black_list_usernames()
        prompt = "Применить блэклист? (Y/n)"
        black_list_ask = Prompt.ask(prompt, console=console).lower()
        if not black_list_ask:
            black_list_ask = "y"
        if black_list_ask == "y":
            self.__usernames = list(usernames - self.__black_list)
        else:
            self.__usernames = list(usernames)
        shuffle(self.__usernames)

    def __check_black_list_usernames(self) -> set[str]:
        if not self.__black_list_path.is_file():
            return set()
        with self.__black_list_path.open("r", encoding="utf-8") as f:
            r = list(set(filter(None, [line.strip() for line in f.readlines()])))
        return set(r)

    def __pop_usernames(self, *, count: int) -> list[str]:
        usernames = []
        for _ in range(count):
            with contextlib.suppress(Exception):
                usernames.append(self.__usernames.pop())
        return usernames

    def __write_usernames_to_black_list(self, usernames: list[str]):
        with self.__black_list_path.open("a", encoding="utf-8") as f:
            f.writelines([f"{line}\n" for line in usernames])

    def __post_request(self, item: Path, params: dict, json_data: dict) -> str:
        while True:
            try:
                r = httpx.post(API_URL, params=params, json=json_data, timeout=30)
                if r.status_code == 200:
                    return r.text
            except Exception as e:
                console.log(f"[{item.name}] {e}, перезапуск...")
                sleep(1.5)

    def _main(
        self,
        item: Path,
        json_file: Path,
        json_data: dict,
        usernames: list[str],
    ):
        params: dict = {
            "license_key": LICENSE_KEY,
            "fwd_from": self.__donor,
            "fwd_index": self.__fwd_index,
        }
        data: dict = {
            "json_data": json_data,
            "usernames": usernames,
        }
        r = self.__post_request(item, params, data)
        if "ERROR_LICENSE" in r:
            console.log(r, style="red")
            self.__is_license_good = False
        elif "ERROR_AUTH" in r:
            with contextlib.suppress(Exception):
                move(item, self.__banned_path)
            with contextlib.suppress(Exception):
                move(json_file, self.__banned_path)
            console.log(f"[{item.name}] Ошибка авторизации!", style="red")
        elif "ERROR_DONOR" in r:
            console.log(r, style="red")
            self.__is_donor_good = False
        elif "ERROR_STORY" in r:
            with contextlib.suppress(Exception):
                move(item, self.__errors_path)
            with contextlib.suppress(Exception):
                move(json_file, self.__errors_path)
            console.log(f"[{item.name}] Ошибка добавления сторис!", style="red")
        elif "OK" in r:
            console.log(f"[{item.name}] Сторис успешно добавлен!", style="green")
            with LOCKER:
                self.__write_usernames_to_black_list(usernames)
        else:
            console.log(f"[{item.name}] {r}", style="red")

    def main(self) -> bool:
        if not self.__usernames:
            console.log("Нет юзернеймов для обработки!")
            return False
        threads: list = []
        for item, json_file, json_data in self._find_sessions():
            while len(threads) >= 5:
                with contextlib.suppress(Exception):
                    threads[0].join()
            usernames = self.__pop_usernames(count=5)
            if not usernames:
                break
            console.log(f"[{item.name}] -> {usernames}")
            args = (item, json_file, json_data, usernames)
            thr = Thread(target=self._main, args=args)
            thr.start()
            threads.append(thr)
            if not self.__is_donor_good or not self.__is_license_good:
                break
            sleep(1.5)
        [t.join() for t in threads]
        return True
