import logging
import discord
from asyncio import sleep
from discord.ext import tasks
from dotenv import load_dotenv
from os import getenv, path
from classes import uacBot
import json


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

if path.exists('.env'):
    load_dotenv('.env')
botInst = uacBot()

with open('config.json', 'r') as f:
    config = json.load(f)

f.close()


CHANNEL_ID = config["channel_id"]
INFO_CHANNEL_ID = config["info_channel_id"]
ALLOWED_EMOJIS = config["allowed_emojis"]
APPROVE_THRESHOLD = config["approve_threshold"]
CHECK_RATE = config["check_rate"]
APPROVAL_EMOJI = config["approval_emoji"]
EMBED_COLOR = config["embed_color"]

APPROVE_BUTTON_LABEL = config["btn_labels"]["approve"]
DECLINE_BUTTON_LABEL = config["btn_labels"]["decline"]
JUMP_BUTTON_LABEL = config["btn_labels"]["jump"]


class Menu(discord.ui.View):
    def __init__(self, thread: discord.Thread) -> None:
        super().__init__()
        self.thread = thread
        self.add_item(discord.ui.Button(label=JUMP_BUTTON_LABEL, style=discord.ButtonStyle.success, url=self.thread.jump_url))


    @discord.ui.button(label=APPROVE_BUTTON_LABEL, style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_petition(interaction, button)


    @discord.ui.button(label=DECLINE_BUTTON_LABEL, style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_petition(interaction, button)


    async def _handle_petition(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.thread.locked:
            await self.thread.edit(locked=True)
        
        if len(self.thread.applied_tags) == 1 and self.thread.applied_tags[0] == PENDING_TAG:
            jumpTo = discord.ui.View()
            jumpTo.add_item(discord.ui.Button(label=JUMP_BUTTON_LABEL, style=discord.ButtonStyle.link, url=self.thread.jump_url))
            threadStarter = [m async for m in self.thread.history(limit=1, oldest_first=True)][0]
            embed = discord.Embed(
                    title=f'Петиція #{len(self.thread.parent.threads)}: {self.thread.name}',  
                    color=EMBED_COLOR
                    )
            embed.set_author(name=threadStarter.author.display_name, icon_url=threadStarter.author.avatar.url)

            if button.label == APPROVE_BUTTON_LABEL:
                await interaction.response.send_message(f'Петицію прийнято: {self.thread.name}', ephemeral=True)
                embed.description = f'Вашу петицію було прийнято.'
                logger.info(f'Petition approved: {self.thread.name}')
            elif button.label == DECLINE_BUTTON_LABEL:
                await interaction.response.send_message(f'Петицію відхилено: {self.thread.name}', ephemeral=True)
                embed.description = f'Вашу петицію було відхилено.'
                logger.info(f'Petition declined: {self.thread.name}')    

            await threadStarter.author.send(embed=embed, view=jumpTo)
            await interaction.message.edit(view=jumpTo)

            await self.thread.remove_tags(PENDING_TAG)
            await sleep(1)
            if button.label == APPROVE_BUTTON_LABEL:
                await self.thread.add_tags(APPROVE_TAG)
            elif button.label == DECLINE_BUTTON_LABEL:
                await self.thread.add_tags(DECLINE_TAG)


@botInst.event
async def on_ready():
    global APPROVE_TAG, DECLINE_TAG, PENDING_TAG

    APPROVE_TAG_NAME = config["tags"]["approve_tag"]
    DECLINE_TAG_NAME = config["tags"]["decline_tag"]
    PENDING_TAG_NAME = config["tags"]["pending_tag"]
    
    petitioChannelTags = botInst.get_channel(CHANNEL_ID).available_tags

    for t in petitioChannelTags:
        if t.name == APPROVE_TAG_NAME:
            APPROVE_TAG = t
        elif t.name == DECLINE_TAG_NAME:
            DECLINE_TAG = t
        elif t.name == PENDING_TAG_NAME:
            PENDING_TAG = t
        else:
            logger.error('Misconfigured tags in config.json')
            await botInst.close()
            exit(1)

    logger.info(f'Loaded tags: {APPROVE_TAG}, {DECLINE_TAG}, {PENDING_TAG}')
    check_petitio_reactions.start()
    logger.info(f'Logged in as {botInst.user.name} ({botInst.user.id})')
    

@botInst.event
async def on_thread_create(thread: discord.Thread):
    if thread.parent.id == CHANNEL_ID:
        threadStarter = [m async for m in thread.history(limit=1, oldest_first=True)][0]
        for e in ALLOWED_EMOJIS:
            await threadStarter.add_reaction(e)

        await thread.add_tags(PENDING_TAG)


@tasks.loop(seconds=CHECK_RATE)
async def check_petitio_reactions():
    petitioChannel = botInst.get_channel(CHANNEL_ID)
    for thread in petitioChannel.threads:
        threadStarter = [m async for m in thread.history(limit=1, oldest_first=True)][0]
        for r in threadStarter.reactions:
            if r.emoji not in ALLOWED_EMOJIS:
                await r.clear()
            elif r.emoji == APPROVAL_EMOJI and r.count == APPROVE_THRESHOLD:
                if thread.locked:
                    continue
                
                await thread.edit(locked=True)

                logger.info(f'Locked thread {thread.name} ({thread.id})')
                v = Menu(thread)
                embed = discord.Embed(
                    title=f'Петиція #{len(thread.parent.threads)}: {thread.name}', 
                    description='Ця петиція набрала потрібну кількість голосів. Прийняти її або відхилити?', 
                    color=EMBED_COLOR
                    )
                embed.set_author(name=threadStarter.author.display_name, icon_url=threadStarter.author.avatar.url)
                message: discord.Message = await botInst.get_channel(INFO_CHANNEL_ID).send(view=v, embed=embed)
                await message.create_thread(name=thread.name)

    del petitioChannel


if __name__ == '__main__':
    botInst.run(token=getenv('TOKEN'))