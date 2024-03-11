import logging
import os

import discord
from discord.ext import commands

intents = discord.Intents.all()
discordBot = commands.Bot(command_prefix='~',
                          case_insensitive=True,
                          help_command=None,
                          intents=intents)
logger = logging.getLogger('discord')

async def StartBot():

  @discordBot.event
  async def on_ready():
    logger.info(f"{discordBot.user} up and running")

  async def on_message_delete(message):
    async for entry in message.guild.audit_logs(limit=1,action=discord.AuditLogAction.message_delete):
        deleter = entry.user
    print(f"{deleter.name} deleted message by {message.author.name}")

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
