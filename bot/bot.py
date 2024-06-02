import asyncio
import logging
import datetime
import sentry_sdk

from pyrogram import filters
from pyrogram.errors import UserIsBlocked, UserDeactivated, UserDeactivatedBan
from sqlalchemy import select, update

from models import User, UserStatus
from loader import client, async_session, sentry_url
from constants import (
    FIRST_MSG,
    SECOND_MSG,
    THIRD_MSG,
    FIRST_DELAY,
    SECOND_DELAY,
    THIRD_DELAY,
    TRIGGER_WORDS
)

logger = logging.getLogger(__name__)


async def update_user_status(user_id, status):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == user_id)
            .values(status=status, status_updated_at=datetime.datetime.now())
        )
        await session.commit()


@client.on_message(filters.private)
async def handle_message(client, message):
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


async def start_funnel(user_id):
    logger.info(f"Starting funnel for user with tg_id:{user_id}")
    messages = [
        (FIRST_DELAY, FIRST_MSG),
        (SECOND_DELAY, SECOND_MSG),
        (THIRD_DELAY, THIRD_MSG),
    ]
    for delay, text in messages:
        await asyncio.sleep(delay)

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.tg_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user is None or user.status != UserStatus.ALIVE:
                return

            try:
                await client.send_message(user_id, text)
            except (UserIsBlocked, UserDeactivated, UserDeactivatedBan) as e:
                logger.info(
                    f"User with tg_id: {user_id} is blocked or deactivated: {e}"
                )
                await update_user_status(user_id, UserStatus.DEAD)
                return


@client.on_message(filters.text & filters.private)
async def trigger_handler(client, message):
    if any(word in message.text.lower() for word in TRIGGER_WORDS):
        await update_user_status(message.from_user.id, UserStatus.FINISHED)
        logger.info(
            f"User with tg_id:{message.from_user.id} finished the funnel"
        )


if __name__ == "__main__":
    sentry_sdk.init(sentry_url)
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )
    client.run()
