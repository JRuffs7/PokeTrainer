from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord

from globals import ErrorColor, HelpColor
from middleware.permissionchecks import is_admin
from services import helpservice, pokemonservice, trainerservice
from services.utility import discordservice


class DebugCommands(commands.Cog, name="DebugCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command(name="sync")
  @commands.has_permissions(administrator=True)
  async def sync(self, ctx):
    print("Syncing bot commands")
    await ctx.bot.tree.sync()
    print("Synced bot commands")

  #Add Pokemon test
  @commands.command(name="cheatAddPokemon")
  @commands.has_permissions(administrator=True)
  async def addPokemon(self, ctx: commands.Context, pokemonId: int,
                       shiny: bool | None):
    trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
    if not trainer:
      return
    pokemon = pokemonservice.GetPokemon(pokemonId)
    if not pokemon:
      return
    spawn = pokemonservice.GenerateSpawnPokemon(pokemon)
    if shiny:
      spawn.IsShiny = True
    trainer.OwnedPokemon.append(spawn)
    trainerservice.UpsertTrainer(trainer)

  #Add Pokemon test
  @commands.command(name="cheatSetMoney")
  @commands.has_permissions(administrator=True)
  async def setMoney(self, ctx: commands.Context, amount: int):
    trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
    if not trainer:
      return
    trainer.Money = amount
    trainerservice.UpsertTrainer(trainer)

#Modify pokeball test

  @commands.command(name="cheatModifypokeball")
  @commands.has_permissions(administrator=True)
  async def modify_pokeball(self, ctx: commands.Context, amount: int):
    try:
      trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
      if trainer is None:
        return await ctx.message.channel.send(
            "This trainer doesn't exist, ya dummy")
      trainer.PokeballList = trainerservice.ModifyItemList(
          trainer.PokeballList, 1, amount)
      trainerservice.UpsertTrainer(trainer)
      await ctx.message.channel.send("You modified your pokeball list!!!!!")
    except Exception as e:
      print(f"{e}")


#Modify potion test

  @commands.command(name="cheatModifypotion")
  @commands.has_permissions(administrator=True)
  async def modify_potion(self, ctx: commands.Context, amount: int):
    try:
      trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
      if trainer is None:
        return await ctx.message.channel.send(
            "This trainer doesn't exist, ya dummy")
      trainer.PotionList = trainerservice.ModifyItemList(
          trainer.PotionList, 1, amount)
      trainerservice.UpsertTrainer(trainer)
      await ctx.message.channel.send("You modified your potions list!!!!!")
    except Exception as e:
      print(f"{e}")


async def setup(bot: commands.Bot):
  await bot.add_cog(DebugCommands(bot))
