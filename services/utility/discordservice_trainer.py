from services.utility import discordservice
from discord import Interaction, Member
from globals import TrainerColor

responseFile = "files/responsefiles/trainerresponses.json"

async def PrintDailyResponse(inter: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=inter, 
		filename=responseFile, 
		command='daily', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintMyEggsResponse(inter: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=inter, 
		filename=responseFile, 
		command='myeggs', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintModifyTeamResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='modifyteam', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintStarter(interaction: Interaction, response: int, params: list):
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='starter', 
		responseInd=response,
		params=params,
		color=TrainerColor)

async def PrintBadges(interaction: Interaction, targetUser: Member, region: str = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='badges', 
		responseInd=0 if not region else 1, 
		color=TrainerColor,
		params=[targetUser.display_name] if not region else [region])

async def PrintRelease(interaction: Interaction, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='release', 
		responseInd=0, 
		color=TrainerColor, 
		params=params)

async def PrintMyPokemon(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='mypokemon', 
		responseInd=0, 
		color=TrainerColor, 
		params=[])
