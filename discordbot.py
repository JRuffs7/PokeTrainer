import asyncio
import logging
import os

import discord
from discord.ext import commands
from globals import HelpColor, discordLink, topggLink
from models.Server import Server

from services import serverservice
from services.utility import discordservice

intents = discord.Intents.all()
discordBot = commands.Bot(command_prefix='~',
                          case_insensitive=True,
                          help_command=None,
                          intents=intents)
logger = logging.getLogger('discord')
errorLogger = logging.getLogger('error')


async def StartBot():
  
  @discordBot.event
  async def on_ready():
    logger.info(f"{discordBot.user} up and running - {os.environ['BUILD']}")

    if int(os.environ['GLOBAL_SYNC']) == 1:
      logger.info(f'Global Sync Command Startup')
      await discordBot.tree.sync()
      logger.info(f'Syncing complete.')
      
    try:
      os.remove('dataaccess/utility/locks.sqlite3')
    except Exception:
      pass

    try:
      updateStr = ''
      with open('updatefile.txt', 'r') as file:
        updateStr = file.read()
      os.remove('updatefile.txt')
      if updateStr:
        updateStr += f"\n\nCheck out recent updates in more detail by using **/help update**\n\nFeel free to report any issues to the [Discord Server]({discordLink})\nDon't forget to [Upvote the Bot]({topggLink}) for **5 Free Rare Candies**!"
        allServers = serverservice.GetAllServers()
        for server in allServers:
          asyncio.run_coroutine_threadsafe(MessageThread(discordservice.CreateEmbed('New Update', updateStr, HelpColor), server), discordBot.loop)
    except FileNotFoundError:
      pass
    except Exception as e:
      errorLogger.error(e)
      pass

    #event_loop.start()


  @discordBot.event
  async def on_command_error(ctx, error):
    errorLogger.error(error)


  async def MessageThread(embed: discord.Embed, server: Server):
    guild = discordBot.get_guild(server.ServerId)
    if not guild:
      return 
    channel = guild.get_channel(server.ChannelId)
    if not channel or not isinstance(channel, discord.TextChannel):
      return
    
    return await channel.send(embed=embed)

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
