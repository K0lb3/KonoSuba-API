import os
import json
from .paths import MASTER

class Database:
    data: dict
    def __init__(self) -> None:
        self.data = {}
        self.known_files = [
            f[:-5]
            for f in os.listdir(MASTER)
        ]
    
    def __getattr__(self, name: str):
        if name in self.known_files:
            if name not in self.data:
                with open(os.path.join(MASTER, f"{name}.json"), "rt", encoding="utf8") as f:
                    data = json.load(f)
                self.data[name] = {item["id"]:item for item in data}
            return self.data[name]

db = Database()