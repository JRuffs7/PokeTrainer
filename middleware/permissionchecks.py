from discord import app_commands
from discord.user import discord


def is_admin():

  def predicate(inter: discord.Interaction) -> bool:
    return inter.permissions.administrator

  return app_commands.check(predicate)
