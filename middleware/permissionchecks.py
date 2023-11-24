from discord import app_commands
from discord.user import discord
from globals import AdminList


def is_admin():

  def predicate(inter: discord.Interaction) -> bool:
    return inter.permissions.administrator

  return app_commands.check(predicate)


def is_bot_admin():

  def predicate(inter: discord.Interaction) -> bool:
    return inter.user.id in AdminList

  return app_commands.check(predicate)