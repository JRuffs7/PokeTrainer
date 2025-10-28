import asyncio
from datetime import UTC, datetime, timedelta
import logging
import os
import discord
from discord.ext import commands, tasks
from globals import HelpColor, ShortDateFormat, discordLink, topggLink, initTracking, cleansetimes
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
        allServers = discordBot.guilds
        for server in allServers:
          asyncio.run_coroutine_threadsafe(MessageThread(discordservice.CreateEmbed('New Update', updateStr, HelpColor), server), discordBot.loop)
    except FileNotFoundError:
      pass
    except Exception as e:
      errorLogger.error(e)
      pass
    cleanse_servers.start()

  @discordBot.event
  async def on_command_error(ctx, error):
    errorLogger.error(error)

  @tasks.loop(time=cleansetimes)
  async def cleanse_servers():
    for guild in discordBot.guilds:
      server = serverservice.GetServer(guild.id)
      if not server:
        server = Server({'Servername': guild.name,'ServerId': guild.id,'LastActivity': datetime.now(UTC).strftime(ShortDateFormat)})
      if not server.LastActivity:
        server.LastActivity = datetime.now(UTC).strftime(ShortDateFormat)
      serverservice.UpsertServer(server)
      
      lastActivity = datetime.strptime(server.LastActivity, ShortDateFormat)

      if (lastActivity + timedelta(days=30)) < datetime.now():

        await MessageThread(discordservice.CreateEmbed(
          'Sorry To Leave',
          'Due to prolonged inactivity on this server, PokeTrainer has decided to remove itself in order to create free space for other servers to invite it. Your data WILL NOT be deleted, and you are free to add PokeTrainer back whenever you wish! Thank you for playing and we hope to see you again.',
          HelpColor), guild)
        await guild.leave()

  async def MessageThread(embed: discord.Embed, guild: discord.Guild):
    if not guild:
      return 
    server = serverservice.GetServer(guild.id) or Server.from_dict({'ServerName': guild.name, 'ServerId': guild.id})
    if datetime.today().date() == initTracking.date():
      server.LastActivity = datetime.now(UTC).strftime(ShortDateFormat)

    channel = guild.get_channel(server.ChannelId)
    if not channel:
      member = guild.get_member(discordBot.user.id)
      channel = next((c for c in guild.text_channels if c.permissions_for(member).send_messages),None)
    if not channel or not isinstance(channel, discord.TextChannel):
      await guild.leave()
      serverservice.DeleteServer(server)
      return
    else:
      server.ChannelId = channel.id
    serverservice.UpsertServer(server)
    return await channel.send(embed=embed)

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])