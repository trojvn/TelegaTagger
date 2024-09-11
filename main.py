from pathlib import Path
from time import sleep

import httpx
from rich.prompt import Prompt

from console import console
from envs import API_URL, LICENSE_KEY
from json_converter import JsonConverter
from stories_sender import StoriesSender


def restart_module():
    restart_ask = Prompt.ask("Перезагрузить модуль? (Y/n)", console=console).lower()
    if not restart_ask:
        restart_ask = "y"
    if restart_ask == "y":
        httpx.get(f"{API_URL}restart/")


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
        console.log("Файл с именами пользователей usernames.txt пуст!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    if not API_URL:
        console.log("Переменная окружения API_URL пуста! (.env)", style="red")
        return console.input("Нажмите Enter для продолжения...")
    if not LICENSE_KEY:
        console.log("Переменная окружения LICENSE_KEY пуста! (.env)", style="red")
        return console.input("Нажмите Enter для продолжения...")
    count_stories_ask = Prompt.ask("Сколько сторис с аккаунта?", console=console)
    if not count_stories_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    count_stories_ask = int(count_stories_ask)

    restart_module()

    ss = StoriesSender(usernames)
    count = JsonConverter(need_log=False).main()
    if not count:
        console.log("Нет аккаунтов в папке sessions!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")

    delay_ask = Prompt.ask("Задержка между сторис (сек.)", console=console)
    if not delay_ask.isdigit():
        delay_ask = 10
    else:
        delay_ask = int(delay_ask)

    for _ in range(count_stories_ask):
        r = ss.main()
        if not r:
            break
        sleep(delay_ask)

    return console.input("Нажмите Enter для продолжения...")


def main():
    while True:
        try:
            _main()
        except Exception:
            console.print_exception()


if __name__ == "__main__":
    main()
