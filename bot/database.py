from dataclasses import dataclass


@dataclass
class Database:
    name: str
    user: str
    password: str
    host: str
    port: int
