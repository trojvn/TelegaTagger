import logging
from pathlib import Path

from console import console
from envs import API_URL, LICENSE_KEY
from json_converter import JsonConverter
from stories_sender import StoriesSender


def get_usernames() -> set[str]:
    usernames_file = Path("usernames.txt")
    if not usernames_file.is_file():
        usernames_file.touch()
        return set()
    with usernames_file.open("r", encoding="utf-8") as f:
        usernames = set(filter(None, [line.strip() for line in f.readlines()]))
    return usernames


def _main():
    [Path(dir).mkdir(exist_ok=True) for dir in ["sessions"]]
    if not (usernames := get_usernames()):
        console.log("Файл с именами пользователей usernames.txt пуст!")
        return input("Нажмите Enter для продолжения...")
    if not API_URL:
        console.log("Переменная окружения API_URL пуста! (.env)")
        return input("Нажмите Enter для продолжения...")
    if not LICENSE_KEY:
        console.log("Переменная окружения LICENSE_KEY пуста! (.env)")
        return input("Нажмите Enter для продолжения...")

    ss = StoriesSender(usernames)
    count = JsonConverter(need_log=False).main()
    if not count:
        console.log("Нет аккаунтов в папке sessions!")
        return input("Нажмите Enter для продолжения...")
    for _ in range(3):
        r = ss.main()
        if not r:
            break

    return input("Нажмите Enter для продолжения...")


def main():
    while True:
        try:
            _main()
        except Exception as e:
            logging.exception(e)


if __name__ == "__main__":
    main()
