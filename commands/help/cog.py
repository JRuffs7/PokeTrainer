from discord import app_commands, Interaction
from discord.ext import commands

from globals import HelpColor
from middleware.decorators import method_logger
from services import helpservice
from services.utility import discordservice, discordservice_help


class HelpCommands(commands.Cog, name="HelpCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot


  async def command_autofill(self, inter: Interaction, current: str):
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
  @method_logger(True)
  async def help(self, 
                 inter: Interaction, 
                 command: str | None):
    if not command:
      helpList = helpservice.BuildFullHelp(inter.user.guild_permissions.administrator)

      su = discordservice.CreateEmbed("PokeTrainer Help", helpList[0], HelpColor)
      sp = discordservice.CreateEmbed("", helpList[1], HelpColor)
      tr = discordservice.CreateEmbed("", helpList[2], HelpColor)
      cm = discordservice.CreateEmbed("", helpList[3], HelpColor)

      if (not await discordservice.SendDMs(inter, [su, sp])) or (not await discordservice.SendDMs(inter, [tr, cm])):
        return await discordservice_help.PrintHelpResponse(inter, 1, [helpList[3]])
      return await discordservice_help.PrintHelpResponse(inter, 0)
    else:
      helpComm = helpservice.BuildCommandHelp(command, inter.user.guild_permissions.administrator)
      if not helpComm:
        return await discordservice_help.PrintHelpResponse(inter, 2, [command.lower()])
      return await discordservice_help.PrintCommandHelp(inter, helpComm)
      


async def setup(bot: commands.Bot):
  await bot.add_cog(HelpCommands(bot))
