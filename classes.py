import discord
from discord.ext import commands


class uacBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.typing = False
        intents.presences = False
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
