import asyncio
from pathlib import Path
from time import sleep

from rich.prompt import Prompt

from ask_from_history import ask_from_history
from auther import checker
from console import console
from json_converter import JsonConverter
from thon.starter import Starter
from users_db import UsersDB

u = UsersDB()


def _main():
    [Path(dir).mkdir(exist_ok=True) for dir in ["сессии"]]
    _prompt = "Выгрузить юзернеймы? (y/N)"
    unload_ask = Prompt.ask(_prompt, console=console, default="n").lower()
    if unload_ask == "y":
        success_users = u.get_success_users_from_db()
        fails_users = u.get_fails_users_from_db()
        u.write_success_users_to_file(success_users)
        u.write_fails_users_to_file(fails_users)
        console.log("Юзернеймы выгружены!", style="green")
        console.log("Успешных (шт.): ", len(success_users), style="green")
        console.log("Не успешных (шт.): ", len(fails_users), style="red")
    sessions_count = JsonConverter().main()
    if not sessions_count:
        console.log("Нет аккаунтов в папке с сессиями!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    console.log(f"Всего сессий: {sessions_count}", style="green")

    count, ok_count, error_count = UsersDB.load_users_from_file()
    console.log(f"Всего в файле юзернеймы.txt: {count} пользователей")
    console.log(f"Успешно добавлены в БД: {ok_count}", style="green")
    console.log(f"Ошибок (дубли): {error_count}", style="red")
    console.log(f"Всего юзеров в БД: {u.count_users_from_db}")
    console.log(f"Свободных юзеров: {u.count_free_users_from_db}", style="green")
    if not u.count_free_users_from_db:
        console.log("Нет свободных юзеров!", style="yellow")
        _prompt = "Хотите удалить БД и начать все сначала? (y/N)"
        delete_ask = Prompt.ask(_prompt, console=console, default="n").lower()
        if delete_ask == "y":
            u.drop()
            console.log("БД удалена!", style="green")
            return console.input("Нажмите Enter для продолжения...")
        return console.input("Нажмите Enter для продолжения...")

    _prompt = "Сколько сторис с аккаунта?"
    count_stories_ask = Prompt.ask(_prompt, console=console, default="1")
    if not count_stories_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    count_stories_ask = int(count_stories_ask)

    _prompt = "Введите донора у кого брать сторис (например @durov)"
    fwd_from_ask = ask_from_history(_prompt, console, Path("history_donors.json"))

    _prompt = "Какое сторис у донора забирать? (например 1)"
    fwd_index_ask = Prompt.ask(_prompt, console=console, default="1")
    if not fwd_index_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    fwd_index_ask = int(fwd_index_ask)

    _prompt = "Задержка между сторис (сек.)"
    delay_ask = Prompt.ask(_prompt, console=console, default="10")
    if not delay_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    delay_ask = int(delay_ask)

    _prompt = "Сколько юзеров упоминать в 1 сторис?"
    users_count_ask = Prompt.ask(_prompt, console=console, default="1")
    if not users_count_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    users_count_ask = int(users_count_ask)

    _prompt = "Сколько потоков нужно для работы?"
    threads_ask = Prompt.ask(_prompt, console=console, default=str(sessions_count))
    if not threads_ask.isdigit():
        console.log("Параметр должен быть числом!", style="yellow")
        return console.input("Нажмите Enter для продолжения...")
    threads_ask = int(threads_ask)
    if not checker():
        return console.input("Нажмите Enter для продолжения...")

    s = Starter(fwd_from_ask, fwd_index_ask, users_count_ask, threads_ask)

    for _ in range(count_stories_ask):
        if not asyncio.run(s.main()):
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
