import logging
from os import getenv

import discord
from discord import Message, TextChannel, Thread, Embed
from discord.ext import tasks

from bot_functions import clear_reactions, get_thread_message
from classes import uacBot
from config import Config
from models import ActivePetitionStoreModel
from store import StoreManager
from setup_logger import setup_logging

logger = logging.getLogger(__name__)
setup_logging()

botInst = uacBot()

config = Config()
store_manager = StoreManager()


class Menu(discord.ui.View):
    def __init__(self, thread: discord.Thread) -> None:
        super().__init__(timeout=None)
        self.thread = thread
        self.add_item(
            discord.ui.Button(
                label=config.JUMP_BUTTON_LABEL,
                style=discord.ButtonStyle.success,
                url=self.thread.jump_url,
            )
        )

    @discord.ui.button(
        label=config.APPROVE_BUTTON_LABEL,
        style=discord.ButtonStyle.success,
        custom_id="approve_button",
    )
    async def approve(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            logger.info(f"Approve petition #{self.thread.id}")
            await self._handle_petition(interaction, button)
        except Exception as e:
            logger.error(f"Error in approve interaction: {e}")
            await interaction.response.send_message(
                "An error occurred.", ephemeral=True
            )

    @discord.ui.button(
        label=config.DECLINE_BUTTON_LABEL,
        style=discord.ButtonStyle.danger,
        custom_id="decline_button",
    )
    async def decline(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            logger.info(f"Decline petition #{self.thread.id}")
            await self._handle_petition(interaction, button)
        except Exception as e:
            logger.error(f"Error in decline interaction: {e}")
            await interaction.response.send_message(
                "An error occurred.", ephemeral=True
            )

    async def _handle_petition(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if (
            len(self.thread.applied_tags) == 1
            and self.thread.applied_tags[0] == config.PENDING_TAG
        ):
            logger.info(f"Creating menu for petition #{self.thread.id}")
            jumpTo = discord.ui.View()
            jumpTo.add_item(
                discord.ui.Button(
                    label=config.JUMP_BUTTON_LABEL,
                    style=discord.ButtonStyle.link,
                    url=self.thread.jump_url,
                )
            )
            threadStarter = [
                m async for m in self.thread.history(
                    limit=1, oldest_first=True
                )
            ][0]
            embed = discord.Embed(
                title=f"""
                Петиція #{len(self.thread.parent.threads)}: {self.thread.name}
                """,
                color=config.EMBED_COLOR,
            )
            embed.set_author(
                name=threadStarter.author.display_name,
                icon_url=threadStarter.author.avatar.url,
            )

            if button.label == config.APPROVE_BUTTON_LABEL:
                await interaction.response.send_message(
                    f"Петицію прийнято: {self.thread.name}", ephemeral=True
                )
                embed.description = "Вашу петицію було прийнято."
                logger.info(f"Petition approved: {self.thread.name}")
            elif button.label == config.DECLINE_BUTTON_LABEL:
                await interaction.response.send_message(
                    f"Петицію відхилено: {self.thread.name}", ephemeral=True
                )
                embed.description = "Вашу петицію було відхилено."
                logger.info(f"Petition declined: {self.thread.name}")

            logger.info("Sending message to petition author")
            await threadStarter.author.send(embed=embed, view=jumpTo)
            await interaction.message.edit(view=jumpTo)

            logger.info(f"Removing tag {config.PENDING_TAG}")
            await self.thread.remove_tags(config.PENDING_TAG)
            if button.label == config.APPROVE_BUTTON_LABEL:
                logger.info(f"Adding tag {config.APPROVE_TAG}")
                await self.thread.add_tags(config.APPROVE_TAG)
            elif button.label == config.DECLINE_BUTTON_LABEL:
                logger.info(f"Adding tag {config.DECLINE_TAG}")
                await self.thread.add_tags(config.DECLINE_TAG)

            logger.info(f"Locking thread #{self.thread.id}")
            await self.thread.edit(locked=True)
            store_manager.remove_active_petition(self.thread.id)


@botInst.event
async def on_ready():
    config.set_available_tags(
        forum_tags=botInst.get_channel(config.CHANNEL_ID).available_tags
    )
    await renew_messages()
    logger.info(f"Logged in as {botInst.user.name} ({botInst.user.id})")
    check_petition_emojies.start()


async def remove_message(message_id: int):
    logger.info(f"Removing message {message_id}")
    channel: TextChannel = botInst.get_channel(config.INFO_CHANNEL_ID)
    try:
        message = await channel.fetch_message(message_id)
        await message.delete()
    except discord.NotFound:
        logger.warning(
            f"""
            Message with id {message_id} not found! Skipping removing message
            """
        )
        pass


async def send_message(thread: Thread, message: Message):
    v = Menu(thread=thread)
    botInst.add_view(view=v)
    embed = Embed(
        title=f"Петиція #{thread.id}: {thread.name}",
        description="""
        Ця петиція набрала потрібну кількість голосів.
        Прийняти її або відхилити?
        """,
        color=config.EMBED_COLOR,
    )

    embed.set_author(
        name=message.author.display_name, icon_url=message.author.avatar.url
    )
    message = await botInst.get_channel(config.INFO_CHANNEL_ID).send(
        view=v, embed=embed
    )
    return message


async def renew_messages():
    logger.info("Renewing messages about petitions")
    active_petition: list[ActivePetitionStoreModel] = (
        store_manager.get_active_petitions_store()
    )
    for petition in active_petition:
        await remove_message(petition.message_id)
        store_manager.remove_active_petition(petition.thread_id)


@tasks.loop(seconds=config.CHECK_RATE)
async def check_petition_emojies():
    logging.info("Checking petitions emojies...")
    petitions_channel: Thread = botInst.get_channel(config.CHANNEL_ID)
    threads = list(filter(
    lambda thread: not thread.locked,
    petitions_channel.threads
        )
    )
    for thread in threads:
        starter_message: Message = await get_thread_message(thread=thread)
        emoji_dict = await clear_reactions(
            thread_message=starter_message,
            allowed_emojis=config.ALLOWED_EMOJIS
        )
        emoji_dict = {
            emoji_key.emoji: emoji_key.count for emoji_key in emoji_dict.keys()
        }
        await starter_message.add_reaction(config.APPROVAL_EMOJI)
        await thread.add_tags(config.PENDING_TAG)

        if (
            emoji_dict
            and emoji_dict[config.APPROVAL_EMOJI] >= config.APPROVE_THRESHOLD
            and not store_manager.is_petitio_exists(thread.id)
        ):

            message = await send_message(
                thread=thread,
                message=starter_message
            )
            store_manager.add_active_petitions_to_store(
                ActivePetitionStoreModel(
                    thread_id=thread.id,
                    message_id=message.id
                )
            )
            await message.create_thread(name=thread.name)
    logger.info("Checking petiotions emojies finished")


@botInst.event
async def on_thread_create(thread: discord.Thread):
    if thread.parent_id == config.CHANNEL_ID:
        logger.info("Petition created!")
        await thread.join()

        thread_start_message: discord.Message = await thread.fetch_message(
            thread.id
        )
        logger.info("Add reaction to new petition")
        await thread_start_message.add_reaction(config.APPROVAL_EMOJI)
        logger.info("Add pending tag to petition")
        await thread.add_tags(config.PENDING_TAG)


if __name__ == "__main__":
    botInst.run(token=getenv("TOKEN"))
