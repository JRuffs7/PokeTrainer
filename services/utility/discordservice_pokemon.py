from globals import ErrorColor, PokemonColor, SuccessColor
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
		params=params)

async def PrintEvolveResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='evolve', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)

async def PrintHatchResponse(interaction: Interaction, response: int):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='hatch', 
		responseInd=response, 
		color=PokemonColor, 
		params=[])

async def PrintGiveCandyResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='givecandy', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)

async def PrintDaycareResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='daycare', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)

async def PrintBattleSimResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='battlesim', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)

async def PrintWishlistResponse(interaction: Interaction, response: int, pkmnname: str|None = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='wishlist', 
		responseInd=response, 
		color=ErrorColor if response else SuccessColor, 
		params=[pkmnname])

async def PrintPokeShopResponse(interaction: Interaction, response: int, pkmnname: str|None = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='pokeshop', 
		responseInd=response, 
		color=ErrorColor, 
		params=[pkmnname])

async def PrintSpawnLegendaryResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='spawnlegendary', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)

async def PrintUsePotionResponse(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='usepotion', 
		responseInd=response, 
		color=PokemonColor, 
		params=params)