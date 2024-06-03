from pyrogram.types import Message
from constants import TRIGGER_WORDS


def trigger_filter(flt, client, message: Message):
    return any(word in message.text.lower() for word in TRIGGER_WORDS)
