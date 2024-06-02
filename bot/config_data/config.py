from dataclasses import dataclass

from environs import Env


@dataclass
class DatabaseConfig:
    postgres_db: str
    db_host: str
    postgres_user: str
    postgres_password: str
    db_port: int


@dataclass
class UserBot:
    app_name: str
    api_id: str
    api_hash: str


@dataclass
class Sentry:
    url: str


@dataclass
class Config:
    user_bot: UserBot
    db: DatabaseConfig
    sentry_url: Sentry


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        user_bot=UserBot(
            app_name=env("APP_NAME"),
            api_id=env("API_ID"),
            api_hash=env("API_HASH"),
        ),
        db=DatabaseConfig(
            postgres_db=env("POSTGRES_DB"),
            db_host=env("DB_HOST"),
            postgres_user=env("POSTGRES_USER"),
            postgres_password=env("POSTGRES_PASSWORD"),
            db_port=env.int("DB_PORT"),
        ),
        sentry_url=Sentry(url=env("SENTRY_URL")),
    )
