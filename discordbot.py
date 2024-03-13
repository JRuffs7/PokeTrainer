import logging
import os

import discord
from discord.ext import commands

from services import serverservice

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

  @discordBot.event
  async def on_message_delete(message: discord.Message):
    if not message.guild or message.author.id != discordBot.user.id:
      return
    await serverservice.EndEvent(serverservice.GetServer(message.guild.id), message.id)

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
