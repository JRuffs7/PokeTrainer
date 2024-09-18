from globals import BattleColor, TradeColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/shopresponses.json"

async def PrintBuyResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='buy', 
		responseInd=response, 
		color=TradeColor, 
		params=params,
		eph=response == 0)

async def PrintSellResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='sell', 
		responseInd=response, 
		color=TradeColor, 
		params=params,
		eph=response == 0)

async def PrintSpecialShopResponse(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='specialshop', 
		responseInd=0, 
		color=BattleColor, 
		params=[],
		eph=True)