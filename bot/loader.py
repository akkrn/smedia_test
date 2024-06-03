from pyrogram import Client
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config_data.config import load_config
from database import Database

config = load_config(path=None)

db = Database(
    name=config.db.postgres_db,
    user=config.db.postgres_user,
    password=config.db.postgres_password,
    host=config.db.db_host,
    port=config.db.db_port,
)
database_url = f"postgresql+asyncpg://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"
engine = create_async_engine(database_url, echo=False)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

sentry_url = config.sentry_url.url

app = Client(
    config.user_bot.app_name,
    api_id=config.user_bot.api_id,
    api_hash=config.user_bot.api_hash,
)
