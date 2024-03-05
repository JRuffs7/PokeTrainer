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

def SpawnDesc(pokemon: Pokemon):
	pkmn = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
	spawnData = t2a(body=[['Rarity:', f"{pkmn.Rarity}", '|', 'Height:', pokemon.Height],
											 ['Color:',f"{pkmn.Color}", '|','Weight:', pokemon.Weight], 
											 ['Types:', f"{pkmn.Types[0]}"f"{'/' + pkmn.Types[1] if len(pkmn.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0)
	return f"```{spawnData}```"