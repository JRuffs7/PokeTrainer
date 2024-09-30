from globals import TradeColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/traderesponses.json"

async def PrintTradeResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='trade', 
		responseInd=response, 
		color=TradeColor, 
		params=params)