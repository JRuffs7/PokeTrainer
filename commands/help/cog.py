from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord

from globals import ErrorColor, HelpColor
from services import helpservice
from services.utility import discordservice


class HelpCommands(commands.Cog, name="HelpCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="help",
      description="Sends a DM of the full help docs or a specified command")
  async def help(self, inter: discord.Interaction, command: str | None):
    print("HELP called")
    if not command:
      helpList = helpservice.BuildFullHelp()

      gl = discordservice.CreateEmbed("PokeTrainer Help", helpList[0],
                                      HelpColor)
      gm = discordservice.CreateEmbed("", helpList[1], HelpColor)
      cm = discordservice.CreateEmbed("", helpList[2], HelpColor)
      await discordservice.SendDMs(inter, [gl, gm, cm])
      return await discordservice.SendMessage(
          inter, "Help DM sent.",
          "For more information on specific commands, use **/help *command***",
          HelpColor, True)
    else:
      (valid, description) = helpservice.BuildCommandHelp(
          command.lower(), inter)
      if valid:
        return await discordservice.SendMessage(inter,
                                                f"{command.lower()} Command",
                                                description, HelpColor, True)
      return await discordservice.SendMessage(
          inter, "Invalid Command",
          f"The {command.lower()} command either does not exist or is restricted to administrators only. To find commands you may have access to, use **~help** for a full list.",
          ErrorColor, True)


async def setup(bot: commands.Bot):
  await bot.add_cog(HelpCommands(bot))
