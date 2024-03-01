from discord import Interaction
from globals import HelpColor
from services.utility import discordservice

responseFile = "files/responsefiles/helpresponses.json"

async def PrintHelpResponse(interaction: Interaction, commandName: str):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='help', 
		responseInd=1 if commandName else 0, 
		color=HelpColor, 
		params=[commandName],
		eph=True)