import asyncio
import logging
import os
from random import choice

import discord
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from commands.views.Events.SpecialBattleEventView import SpecialBattleEventView
from commands.views.Events.SpecialSpawnEventView import SpecialSpawnEventView
from commands.views.Events.UserEntryEventView import UserEntryEventView
from globals import HelpColor, eventtimes
from models.Server import Server
from models.enums import EventType

from services import serverservice
from services.utility import discordservice

intents = discord.Intents.all()
discordBot = commands.Bot(command_prefix='~',
                          case_insensitive=True,
                          help_command=None,
                          intents=intents)
logger = logging.getLogger('discord')
syncLogger = logging.getLogger('command')
errorLogger = logging.getLogger('error')


async def StartBot():
  
  @discordBot.event
  async def on_ready():
    logger.info(f"{discordBot.user} up and running - {os.environ['BUILD']}")

    syncLogger.info(f'Global Sync Command Startup')
    await discordBot.tree.sync()
    syncLogger.info(f'Syncing complete.')

    try:
      os.remove('dataaccess/utility/cache.sqlite3')
    except Exception as e:
      pass

    try:
      updateStr = ''
      with open('updatefile.txt', 'r') as file:
          updateStr = file.read()
      os.remove('updatefile.txt')
      if updateStr:
        updateStr += "\n\nCheck out recent updates in more detail by using **/help update**\n\nFeel free to report any issues to the [Discord Server](https://discord.com/invite/W9T4K7fyYu)\n\nDon't forget to upvote at https://top.gg/bot/1151657435073875988"
        allServers = serverservice.GetAllServers()
        for server in allServers:
          asyncio.run_coroutine_threadsafe(MessageThread(discordservice.CreateEmbed('New Update', updateStr, HelpColor), server), discordBot.loop)
    except FileNotFoundError:
      pass
    except Exception as e:
      errorLogger.error(e)
      pass
    event_loop.start()


  @discordBot.event
  async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


  async def MessageThread(embed: discord.Embed, server: Server):
    guild = discordBot.get_guild(server.ServerId)
    if not guild:
      return 
    channel = guild.get_channel(server.ChannelId)
    if not channel or not isinstance(channel, discord.TextChannel):
      return
    
    return await channel.send(embed=embed)


  @tasks.loop(time=eventtimes)
  async def event_loop():
    allServers = serverservice.GetAllServers()
    for server in allServers:
      asyncio.run_coroutine_threadsafe(EventThread(choice(list(EventType)), server), discordBot.loop)

  async def EventThread(eventType: EventType, server: Server):
    try:
      guild = discordBot.get_guild(server.ServerId)
      if not guild:
        return 
      channel = guild.get_channel(server.ChannelId)
      if not channel or not isinstance(channel, discord.TextChannel):
        return
      
      match EventType.SpecialBattle:
        case EventType.SpecialBattle:
          sTrainer = serverservice.SpecialBattleEvent(server)
          await SpecialBattleEventView(server, channel, sTrainer).send()
        case EventType.SpecialTrade:
          serverservice.PokemonCountEvent(server)
        case _:
          spawnPkmn, wishUsers = serverservice.SpecialSpawnEvent(server)
          await SpecialSpawnEventView(server, channel, spawnPkmn).send(wishUsers)
    except Exception as e:
      errorLogger.error(f'Server {server.ServerName} Event: {e}')
      serverservice.DeleteServer(server)

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
