from globals import BattleColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/gymresponses.json"

async def PrintGymBattleResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='gymbattle', 
		responseInd=response, 
		color=BattleColor, 
		params=params)

async def PrintGymInfoResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='gyminfo', 
		responseInd=response, 
		color=BattleColor, 
		params=params)

async def PrintEliteFourResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='elitefour', 
		responseInd=response, 
		color=BattleColor, 
		params=params)

async def PrintExitEliteFourResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='exitelitefour', 
		responseInd=response, 
		color=BattleColor, 
		params=params)