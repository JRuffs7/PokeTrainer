import asyncio
import logging
import os
from random import choice

import discord
from discord.ext import commands, tasks
from commands.views.Events.UserEntryEventView import UserEntryEventView
from globals import eventtimes
from models.Server import Server
from models.enums import EventType

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
    event_loop.start()

  @tasks.loop(time=eventtimes)
  async def event_loop():
    allServers = serverservice.GetAllServers()
    for server in allServers:
      asyncio.run_coroutine_threadsafe(EventThread(choice(list(EventType)), server), discordBot.loop)

  async def EventThread(eventType: EventType, server: Server):
    guild = discordBot.get_guild(server.ServerId)
    if not guild:
      return 
    channel = guild.get_channel(server.ChannelId)
    if not channel or not isinstance(channel, discord.TextChannel):
      return
    
    match eventType:
      case EventType.StatCompare:
        serverservice.StatCompareEvent(server)
        await UserEntryEventView(server, channel, discordBot.user.display_avatar.url).send()
      case EventType.PokemonCount:
        serverservice.PokemonCountEvent(server)
        await UserEntryEventView(server, channel, discordBot.user.display_avatar.url).send()
        return
      case _:
        return
        #spawnPkmn = serverservice.SpecialSpawnEvent(server)
        #await SpecialSpawnEventView(server, channel, spawnPkmn, 'Special Spawn Event').send()

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
