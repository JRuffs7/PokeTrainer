from discord import Interaction, app_commands
from services import pokemonservice, statservice, trainerservice


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


async def autofill_types(inter: Interaction, current: str):
	choiceList = []
	searchList = statservice.GetAllTypes()
	searchList.sort(key=lambda x: x.Name)
	for type in searchList:
		if current.lower() in type.Name.lower():
				choiceList.append(app_commands.Choice(name=type.Name, value=type.Id))
				if len(choiceList) == 25:
					break
	return choiceList


async def autofill_owned(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon])
    pkmnList.sort(key=lambda x: x.Name)
    for pkmn in pkmnList:
      if current.lower() in pkmn.Name.lower():
        data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
      if len(data) == 25:
        break
    return data


async def autofill_boxpkmn(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Id not in trainer.Team and p.Id not in trainer.Daycare and p.Pokemon_Id != 132])
    pkmnList.sort(key=lambda x: x.Name)
    for pkmn in pkmnList:
      if current.lower() in pkmn.Name.lower():
        data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
      if len(data) == 25:
        break
    return data


async def autofill_nonteam(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Id not in trainer.Team and p.Id not in trainer.Daycare and p.Pokemon_Id != 132])
    pkmnList.sort(key=lambda x: x.Name)
    for pkmn in pkmnList:
      if current.lower() in pkmn.Name.lower():
        data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
      if len(data) == 25:
        break
    return data