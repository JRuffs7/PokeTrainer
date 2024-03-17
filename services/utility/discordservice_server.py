import logging
import discordbot
from globals import ErrorColor, ServerColor
from models.Server import Server
from services.utility import discordservice
from discord import Interaction, TextChannel

errorLog = logging.getLogger('error')

responseFile = "files/responsefiles/serverresponses.json"

async def PrintRegisterResponse(interaction: Interaction, serv: Server | None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='register', 
		responseInd=0 if serv else 1, 
		color=ServerColor if serv else ErrorColor, 
		params=[serv.ServerName, serv.ChannelId, serv.CurrentEvent.EventName if serv.CurrentEvent else ''],
		eph=True)

async def PrintServerResponse(interaction: Interaction, serv: Server):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='server', 
		responseInd=0, 
		color=ServerColor, 
		params=[serv.ServerName, serv.ChannelId, serv.CurrentEvent.EventName if serv.CurrentEvent else ''],
		eph=True)

async def PrintSwapChannelResponse(interaction: Interaction, response: bool):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='swapchannel', 
		responseInd=0 if response else 1, 
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

async def PrintEventWinners(server: Server, winners: list[tuple[int,int]]):
	bot = discordbot.GetBot()
	if server.CurrentEvent.ThreadId:
		try:
			await bot.get_channel(server.CurrentEvent.ThreadId).delete()
		except:
			errorLog.error('Failed to delete thread')

	if winners:
		guild = bot.get_guild(server.ServerId)
		if not guild:
			return 
		channel = guild.get_channel(server.ChannelId)
		if not channel or not isinstance(channel, TextChannel):
			return
		
		winText = '\n'.join([f'<@{w[0]}> - {"1x Masterball" if w[1] == 4 else "5x Ultraball" if w[1] == 3 else "10x Greatball"}' for w in winners])
		message = f'Congratulations to the winners of the {server.CurrentEvent.EventName}!\n\n{winText}'

		await channel.send(message)