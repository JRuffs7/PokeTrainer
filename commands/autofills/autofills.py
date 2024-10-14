from discord import Interaction, app_commands
from globals import region_name
from services import gymservice, moveservice, pokemonservice, statservice, trainerservice


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

async def autofill_regions(inter: Interaction, current: str):
	choiceList = []
	searchList = gymservice.GetRegions()
	searchList.sort()
	for region in searchList:
		if current.lower() in region_name(region):
				choiceList.append(app_commands.Choice(name=region_name(region), value=region))
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


async def autofill_tradable(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Id not in trainer.Team and p.Id not in trainer.Daycare])
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
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in trainer.OwnedPokemon if p.Id not in trainer.Team and p.Id not in trainer.Daycare])
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

async def autofill_team(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    team = trainerservice.GetTeam(trainer)
    pkmnList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in team])
    for pkmn in team:
      pData = next(p for p in pkmnList if p.Id == pkmn.Pokemon_Id)
      if (pkmn.Nickname and (current.lower() in pkmn.Nickname.lower())) or (current.lower() in pData.Name.lower()):
        data.append(app_commands.Choice(name=f'{pkmn.Nickname} ({pData.Name}) - Lvl. {pkmn.Level}' if pkmn.Nickname else f'{pData.Name} - Lvl. {pkmn.Level}', value=pkmn.Id))
      if len(data) == 25:
        break
    return data

async def autofill_tms(inter: Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    movelist = moveservice.GetMovesById([int(m) for m in trainer.TMs if trainer.TMs[m] > 0])
    movelist.sort(key=lambda x: x.Name)
    for move in movelist:
      if current.lower() in ("TM-"+move.Name.lower()):
        data.append(app_commands.Choice(name=f'TM-{move.Name}', value=move.Id))
      if len(data) == 25:
        break
    return data