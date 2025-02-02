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

async def PrintMyPokemonResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='mypokemon', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintBadgesResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='badges', 
		responseInd=response, 
		color=TrainerColor,
		params=params)

async def PrintReleaseResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='release', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintStarterResponse(interaction: Interaction, response: int, params: list):
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='starter', 
		responseInd=response,
		color=TrainerColor,
		params=params)

async def PrintResetTrainerResponse(interaction: Interaction, response: int, params: list):
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='resettrainer', 
		responseInd=response,
		color=TrainerColor,
		params=params)

async def PrintChangeRegionResponse(interaction: Interaction, response: int, params: list):
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='changeregion', 
		responseInd=response,
		color=TrainerColor,
		params=params)
