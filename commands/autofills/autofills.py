from discord import Interaction, app_commands
from services import itemservice, pokemonservice, zoneservice


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


async def autofill_potions(inter: Interaction, current: str):
	data: list[app_commands.Choice] = []
	potions = itemservice.GetAllPotions()
	potions.sort(key=lambda x: x.Id)
	for ptn in potions:
		if current.lower() in ptn.Name.lower():
			data.append(app_commands.Choice(name=ptn.Name, value=ptn.Id))
		if len(data) == 25:
			break
	return data


async def autofill_pokeballs(inter: Interaction, current: str):
	data: list[app_commands.Choice] = []
	balls = itemservice.GetAllPokeballs()
	balls.sort(key=lambda x: x.Id)
	for ball in balls:
		if current.lower() in ball.Name.lower():
			data.append(app_commands.Choice(name=ball.Name, value=ball.Id))
		if len(data) == 25:
			break
	return data


async def autofill_candies(inter: Interaction, current: str):
	data: list[app_commands.Choice] = []
	candies = itemservice.GetAllCandies()
	candies.sort(key=lambda x: x.Id)
	for candy in candies:
		if current.lower() in candy.Name.lower():
			data.append(app_commands.Choice(name=candy.Name, value=candy.Id))
		if len(data) == 25:
			break
	return data


async def autofill_zones(inter: Interaction, current: str):
	data: list[app_commands.Choice] = []
	zones = zoneservice.GetAllZones()
	zones.sort(key=lambda x: (-(x.Id == 0),x.Name))
	for zone in zones:
		types = zone.Types
		types.sort()
		displayName = f'{zone.Name} ({"/".join(types)})'
		if current.lower() in displayName.lower():
			data.append(app_commands.Choice(name=displayName, value=zone.Id))
		if len(data) == 25:
			break
	return data