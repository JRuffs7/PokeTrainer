from globals import BattleColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/shopresponses.json"

async def PrintSpecialShopResponse(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='specialshop', 
		responseInd=0, 
		color=BattleColor, 
		params=[],
		eph=True)