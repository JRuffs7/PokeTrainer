from globals import PokemonColor
from services.utility import discordservice
from discord import Interaction

responseFile = "files/responsefiles/pokemonresponses.json"

async def PrintPokeInfoResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='pokeinfo', 
		responseInd=response, 
		color=PokemonColor, 
		params=params,
		eph=True)

async def PrintEvolveResponse(interaction: Interaction, response: int):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='evolve', 
		responseInd=response, 
		color=PokemonColor, 
		params=[],
		eph=True)

async def PrintSpawnResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='spawn', 
		responseInd=response, 
		color=PokemonColor, 
		params=params,
		eph=True)

async def PrintHatchResponse(interaction: Interaction, response: int):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='hatch', 
		responseInd=response, 
		color=PokemonColor, 
		params=[],
		eph=True)

async def PrintGiveCandyResponse(interaction: Interaction, response: int):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='givecandy', 
		responseInd=response, 
		color=PokemonColor, 
		params=[],
		eph=True)