from pathlib import Path
from typing import Generator

from jsoner import json_read_sync

from console import console


class BaseSession:
    def __init__(self):
        self.base_dir = Path("sessions")
        self.base_dir.mkdir(exist_ok=True)

    def _find_sessions(self) -> Generator:
        for item in self.base_dir.glob("*.session"):
            json_file = item.with_suffix(".json")
            if not json_file.is_file():
                console.log(f"{item.name} | Не найден json файл!", style="red")
                continue
            if not (json_data := json_read_sync(json_file)):
                console.log(f"{item.name} | Ошибка чтения json")
                continue
            yield item, json_file, json_data
