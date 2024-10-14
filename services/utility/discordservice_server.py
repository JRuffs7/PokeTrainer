import logging
from globals import ErrorColor, ServerColor
from services.utility import discordservice
from discord import Interaction

errorLog = logging.getLogger('error')

responseFile = "files/responsefiles/serverresponses.json"

async def PrintRegisterResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='register', 
		responseInd=response, 
		color=ServerColor if params else ErrorColor, 
		params=params)

async def PrintServerResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='server', 
		responseInd=response, 
		color=ServerColor, 
		params=params)

async def PrintUnregisterResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='unregister', 
		responseInd=response, 
		color=ServerColor, 
		params=params)

async def PrintInviteResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='invite', 
		responseInd=response, 
		color=ServerColor, 
		params=params)
