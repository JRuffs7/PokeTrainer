from table2ascii import Merge, table2ascii as t2a, Alignment, PresetStyle
from globals import Checkmark, PokemonColor
from models.Pokemon import Pokemon
from services import pokemonservice
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
