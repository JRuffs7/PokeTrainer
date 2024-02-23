from discord import AppCommandOptionType, User, app_commands
from discord.ext import commands
from discord.user import discord
from globals import AdminList
from services import serverservice, trainerservice
from services.utility import discordservice


def is_admin():

  def predicate(inter: discord.Interaction) -> bool:
    return inter.permissions.administrator

  return app_commands.check(predicate)


def is_bot_admin():

  def predicate(ctx) -> bool:
    return ctx.author.id in AdminList

  return commands.check(predicate)


def server_check():

	async def predicate(inter: discord.Interaction) -> bool:
		serv = serverservice.GetServer(inter.guild_id)
		if not serv:
			await discordservice.SendServerError(inter)
			return False
		return True

	return app_commands.check(predicate)

def trainer_check():

  async def predicate(inter: discord.Interaction) -> bool:
    userId = next((int(o["value"]) for o in inter.data["options"] if o["type"] == 6), inter.user.id) if "options" in inter.data.keys() else inter.user.id
    trainer = trainerservice.GetTrainer(inter.guild_id, userId if userId else inter.user.id)
    if not trainer:
      await discordservice.SendTrainerError(inter)
      return False
    return True

  return app_commands.check(predicate)