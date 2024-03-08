from discord import Interaction
from globals import HelpColor
from models.Help import Help
from services.utility import discordservice

responseFile = "files/responsefiles/helpresponses.json"

async def PrintHelpResponse(interaction: Interaction, response: int, commandName: str = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='help', 
		responseInd=response, 
		color=HelpColor, 
		params=[commandName],
		eph=True)

async def PrintCommandHelp(interaction: Interaction, helpCommand: Help):
	embed = discordservice.CreateEmbed(f"Help: {helpCommand.Name} Command" if helpCommand.ShortString else f"Help: {helpCommand.Name}", helpCommand.HelpString, HelpColor)
	return await discordservice.SendEmbed(interaction, embed, True)