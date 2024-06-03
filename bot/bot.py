import asyncio
import logging
import datetime
import sentry_sdk
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.errors import UserIsBlocked, UserDeactivated, UserDeactivatedBan
from sqlalchemy import select, update

from models import User, UserStatus
from loader import app, async_session, sentry_url
from constants import (
    FIRST_MSG,
    SECOND_MSG,
    THIRD_MSG,
    FIRST_DELAY,
    SECOND_DELAY,
    THIRD_DELAY,
    TRIGGER_WORDS,
)
from filters import trigger_filter

logger = logging.getLogger(__name__)


async def update_user_status(user_id: int, status: UserStatus) -> None:
    """
    Обновляет статус пользователя в базе данных
    """
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == user_id)
            .values(status=status, status_updated_at=datetime.datetime.now())
        )
        await session.commit()


trigger_filter = filters.create(trigger_filter)


@app.on_message(trigger_filter)
async def trigger_handler(client: Client, message: Message) -> None:
    """
    Обработчик сообщений, которые содержат триггерные слова
    """
    await update_user_status(message.from_user.id, UserStatus.FINISHED)
    logger.info(f"User with tg_id:{message.from_user.id} finished the funnel")


@app.on_message(filters.private)
async def handle_message(client: Client, message: Message) -> None:
    """
    Обработчик всех сообщений от пользователя, при первом обращении
    создает запись в базе данных и запускает воронку сообщений
    """
    async with async_session() as session:
        user_id = message.from_user.id
        result = await session.execute(
            select(User).where(User.tg_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                tg_id=user_id,
                tg_username=message.from_user.username,
                tg_first_name=message.from_user.first_name,
                tg_last_name=message.from_user.last_name,
            )
            session.add(user)
            await session.commit()
            await asyncio.create_task(start_funnel(user_id))


async def start_funnel(user_id: int) -> None:
    """
    Запускает воронку сообщений для пользователя
    """
    logger.info(f"Starting funnel for user with tg_id:{user_id}")
    messages = [
        (FIRST_DELAY, FIRST_MSG),
        (SECOND_DELAY, SECOND_MSG),
        (THIRD_DELAY, THIRD_MSG),
    ]
    second_msg_time = None

    for idx, (delay, text) in enumerate(messages):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.tg_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user is None or user.status == UserStatus.DEAD:
                return
            if user and user.status == UserStatus.FINISHED and second_msg_time:
                delay = (
                    THIRD_DELAY
                    - (
                        datetime.datetime.now()
                        - min(user.status_updated_at, second_msg_time)
                    ).seconds
                )
            await asyncio.sleep(delay)
            try:
                await app.send_message(user_id, text)
                if idx == 1:
                    second_msg_time = datetime.datetime.now()
            except (UserIsBlocked, UserDeactivated, UserDeactivatedBan) as e:
                logger.info(
                    f"User with tg_id: {user_id} is blocked or deactivated: {e}"
                )
                await update_user_status(user_id, UserStatus.DEAD)
                return


if __name__ == "__main__":
    sentry_sdk.init(sentry_url)
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )
    app.run()
