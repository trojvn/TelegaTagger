import asyncio
from pathlib import Path

from jsoner import json_write_sync
from telethon import TelegramClient
from telethon.sessions import StringSession
from tooler import ProxyParser

from ask_from_history import ask_from_history
from base_session import BaseSession
from console import console


class JsonConverter(BaseSession):
    def __init__(self, need_proxy: bool = True, need_log: bool = True):
        super().__init__()
        self.__need_proxy, self.__need_log = need_proxy, need_log
        self.__api_id, self.__api_hash = 2040, "b18441a1ff607e10a989891a5462e627"
        if not need_proxy:
            return
        prompt = "Введите прокси (формат http:ipaddr:port:user:pswd)"
        proxy = ask_from_history(prompt, console, Path("history_proxies.json"))
        try:
            self.__proxy = ProxyParser(proxy).asdict_thon
        except Exception as e:
            console.log(e, style="red")
            raise SystemExit from e

    def _main(self, item: Path, json_file: Path, json_data: dict):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = TelegramClient(str(item), self.__api_id, self.__api_hash)
        ss = StringSession()
        ss._server_address = client.session.server_address  # type: ignore
        ss._takeout_id = client.session.takeout_id  # type: ignore
        ss._auth_key = client.session.auth_key  # type: ignore
        ss._dc_id = client.session.dc_id  # type: ignore
        ss._port = client.session.port  # type: ignore
        del client
        string_session = ss.save()
        if self.__need_proxy:
            json_data["proxy"] = self.__proxy
        json_data["string_session"] = string_session
        json_write_sync(json_file, json_data)
        if self.__need_log:
            console.log(f"{item.name} | Успешно обработан!", style="green")

    def main(self) -> int:
        count = 0
        for item, json_file, json_data in self._find_sessions():
            self._main(item, json_file, json_data)
            count += 1
        if self.__need_log:
            console.log(f"Обработано всего: {count}")
        return count
