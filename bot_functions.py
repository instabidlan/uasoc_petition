import logging
from typing import Counter
from discord import Message, Thread
from setup_logger import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


async def get_thread_message(thread: Thread) -> Message:
    logger.info("Get thread message")
    return await thread.fetch_message(thread.id)


async def clear_reactions(thread_message: Message, allowed_emojis: list[str]):
    logger.info(f"Clear reactions for petition {thread_message.id}")
    counted_reactions = get_thread_reactions(thread_message=thread_message)
    counted_reactions_dict = dict(counted_reactions)
    for emoji in counted_reactions:
        if str(emoji) not in allowed_emojis:
            await emoji.clear()
            del counted_reactions_dict[emoji]
    return counted_reactions_dict


def get_thread_reactions(thread_message: Message) -> Counter:
    return Counter(thread_message.reactions)
