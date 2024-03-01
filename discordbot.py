import logging
import os

import discord
from discord.ext import commands

from globals import PokemonCaughtColor
import logs.logsetup
from services import trainerservice

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
  async def on_reaction_add(reaction, user):
    #Reaction is not made by the bot
    if user.id == discordBot.user.id:
      return

    #Reaction on a non-bot message
    if reaction.message.author.id != discordBot.user.id:
      return
    
    result = await trainerservice.ReationReceived(discordBot, user, reaction)
    if result:
      em = reaction.message.embeds[0].set_footer(
          text=f"Caught by {user.display_name}",
          icon_url=user.display_avatar.url)
      em.color = PokemonCaughtColor
      await reaction.message.edit(embed=em)


  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
