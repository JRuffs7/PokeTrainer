from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord

from globals import ErrorColor, HelpColor
from services import helpservice
from services.utility import discordservice


class HelpCommands(commands.Cog, name="HelpCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot


  async def command_autofill(self, inter: discord.Interaction, current: str):
    allHelpComms = helpservice.GetAllHelpCommands(inter.user.guild_permissions.administrator)
    commands = []
    for x in allHelpComms:
      helpList = allHelpComms[x]
      commands += [h.Name for h in helpList]
    commands.sort()
    choices = []
    for c in commands:
      if current.lower() in c.lower():
        choices.append(app_commands.Choice(name=c,value=c))
        if len(choices) == 25:
          break
    return choices


  @app_commands.command(
      name="help",
      description="Sends a full help doc as a DM, or single command in the channel")
  @app_commands.autocomplete(command=command_autofill)
  async def help(self, 
                 inter: discord.Interaction, 
                 command: str | None):
    print("HELP called")
    if not command:
      helpList = helpservice.BuildFullHelp()

      su = discordservice.CreateEmbed("PokeTrainer Help", helpList[0], HelpColor)
      sp = discordservice.CreateEmbed("", helpList[1], HelpColor)
      tr = discordservice.CreateEmbed("", helpList[2], HelpColor)
      cm = discordservice.CreateEmbed("", helpList[3], HelpColor)

      await discordservice.SendDMs(inter, [su, sp, tr, cm])
      return await discordservice.SendMessage(
          inter, "Help DM sent.",
          "For more information on specific commands, use **/help** and specify a command",
          HelpColor, True)
    else:
      helpComm = helpservice.BuildCommandHelp(command, inter.user.guild_permissions.administrator)
      if not helpComm:
        return await discordservice.SendMessage(
          inter, "Invalid Command",
          f"The {command.lower()} command either does not exist or is restricted to administrators only. To find commands you may have access to, use **/help** for a full list.",
          ErrorColor, True)
      return await discordservice.SendMessage(inter, f"{command.lower()} Command", helpComm.HelpString, HelpColor, True)
      


async def setup(bot: commands.Bot):
  await bot.add_cog(HelpCommands(bot))
