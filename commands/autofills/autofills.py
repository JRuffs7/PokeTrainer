from discord import Interaction, app_commands
from services import pokemonservice


async def autofill_pokemon(inter: Interaction, current: str):
	data = []
	pokemonList = pokemonservice.GetAllPokemon()
	pokemonList.sort(key=lambda x: x.Name)
	for pkmn in pokemonList:
		if current.lower() in pkmn.Name.lower():
			data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
		if len(data) == 25:
			break
	return data