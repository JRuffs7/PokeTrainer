import os

import discord
import asyncio
from discord.ext import commands, tasks
import random

from globals import PokemonCaughtColor, ErrorColor
from services import trainerservice, serverservice, pokemonservice
from services.utility import discordservice
from models.CustomException import TrainerInvalidException

intents = discord.Intents.all()
discordBot = commands.Bot(command_prefix='~',
                          case_insensitive=True,
                          help_command=None,
                          intents=intents)


async def StartBot():

  @discordBot.event
  async def on_ready():
    print(f"{discordBot.user} up and running")
    spawn_loop.start()

  @discordBot.event
  async def on_reaction_add(reaction, user):
    #Reaction is not made by the bot
    if user.id == discordBot.user.id:
      return

    #Reaction on a non-bot message
    if reaction.message.author.id != discordBot.user.id:
      return
    
    try:
      result = await trainerservice.ReationReceived(discordBot, user, reaction)
      if result:
        em = reaction.message.embeds[0].set_footer(
            text=f"Caught by {user.display_name}",
            icon_url=user.display_avatar.url)
        em.color = PokemonCaughtColor
        await reaction.message.edit(embed=em)
    except TrainerInvalidException:
      embed = discordservice.CreateEmbed(
          "Trainer Missing!",
          "You have not started your PokeTrainer journey yet! To do so, use one of the **/starter*region*** commands. Please use **/help** for more explanation on how PokeTrainer is used.",
          ErrorColor)
      await user.send(embed=embed)


  @tasks.loop(seconds=300)
  async def spawn_loop():
    print("SPAWN")
    servers = serverservice.GetServers()
    for server in servers:
      asyncio.run_coroutine_threadsafe(spawn_thread(server), GetBot().loop)


  async def spawn_thread(server):
      print(f"SPAWN: {server.ServerId}")
      channel = random.choice(server.ChannelIds)
      if random.randint(1, 100) < server.SpawnChance:
        if server.DeletePrevious:
          await discordservice.DeleteMessage(server.ServerId, server.LastSpawnChannel, server.LastSpawnMessage)

        pkmn = pokemonservice.GetRandomSpawnPokemon()
        if pkmn:
          message = await discordservice.SendPokemon(server.ServerId, channel,
                                                    pkmn)
          if message:
            server.LastSpawned = pkmn
            server.LastSpawnMessage = message.id
            server.LastSpawnChannel = channel
            server.CaughtBy = 0
            server.FoughtBy = []
            serverservice.UpsertServer(server)

  for f in os.listdir("commands"):
    if os.path.exists(os.path.join("commands", f, "cog.py")):
      await discordBot.load_extension(f"commands.{f}.cog")

  await discordBot.start(token=os.environ['TOKEN'])


def GetBot():
  return discordBot
