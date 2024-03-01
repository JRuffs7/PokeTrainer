from globals import BattleColor, ErrorColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/gymresponses.json"

async def PrintGymBattleResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='gymbattle', 
		responseInd=response, 
		color=BattleColor if response != 1 else ErrorColor, 
		params=params,
		eph=True)