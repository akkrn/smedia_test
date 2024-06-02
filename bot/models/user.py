import datetime

from sqlalchemy import TIMESTAMP, BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
import enum


class UserStatus(enum.Enum):
    ALIVE = "alive"
    DEAD = "dead"
    FINISHED = "finished"


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str | None]
    tg_first_name: Mapped[str | None]
    tg_last_name: Mapped[str | None]
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP, default=datetime.datetime.now()
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ALIVE
    )
    status_updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP, default=datetime.datetime.now()
    )
