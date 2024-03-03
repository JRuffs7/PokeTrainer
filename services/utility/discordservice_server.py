from globals import ErrorColor, ServerColor
from models.Server import Server
from services import eventservice
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/serverresponses.json"

async def PrintRegisterResponse(interaction: Interaction, serv: Server | None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='register', 
		responseInd=0 if serv else 1, 
		color=ServerColor if serv else ErrorColor, 
		params=[serv.ServerName, serv.ChannelId, eventservice.GetEventName(serv.CurrentEventId) if serv else ''],
		eph=True)

async def PrintServerResponse(interaction: Interaction, serv: Server):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='server', 
		responseInd=0, 
		color=ServerColor, 
		params=[serv.ServerName, serv.ChannelId, eventservice.GetEventName(serv.CurrentEventId) if serv else ''],
		eph=True)

async def PrintSwapChannelResponse(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='swapchannel', 
		responseInd=0, 
		color=ServerColor, 
		params=[],
		eph=True)

async def PrintUnregisterResponse(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='unregister', 
		responseInd=0, 
		color=ServerColor, 
		params=[],
		eph=True)