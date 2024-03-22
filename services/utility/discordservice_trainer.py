from models.Item import Potion
from models.Trainer import Trainer
from services import itemservice, pokemonservice, gymservice
from services.utility import discordservice
from discord import Interaction, Member
from globals import HelpColor, TrainerColor, Checkmark

responseFile = "files/responsefiles/trainerresponses.json"

async def PrintTrainer(interaction: Interaction, trainer: Trainer, targetUser: Member):
	#Stats Section
	totalPkmn = pokemonservice.GetPokemonCount()
	totalBadges = len(gymservice.GetAllBadges())

	stats = f"__Trainer Stats__\nHP: {trainer.Health}\nPokedex: {len(trainer.Pokedex)}/{totalPkmn} ({round((len(trainer.Pokedex)*100)/totalPkmn)}%)\nPokemon Caught: {len(trainer.OwnedPokemon)}\nShiny Count: {len([x for x in trainer.OwnedPokemon if x.IsShiny])}\nGym Badges: {len(trainer.Badges)}/{totalBadges}"

	#Pokeball Section
	pkblString = '\n'.join(f"{itemservice.GetPokeball(int(p)).Name}: {trainer.Pokeballs[p]}" for p in list(sorted(trainer.Pokeballs, key=lambda x: x)) if trainer.Pokeballs[p])
	pkbl = f'{pkblString}' if pkblString else ''

	#Potion Section
	ptnString = '\n'.join(f"{itemservice.GetPotion(int(p)).Name}: {trainer.Potions[p]}" for p in list(sorted(trainer.Potions, key=lambda x: x)) if trainer.Potions[p])
	ptn = f'{ptnString}' if ptnString else ''

	#Candy Section
	cndString = '\n'.join(f"{itemservice.GetCandy(int(c)).Name}: {trainer.Candies[c]}" for c in list(sorted(trainer.Candies, key=lambda x: x)) if trainer.Candies[c])
	candy = f'{cndString}' if cndString else ''

	#Egg Section
	eggString = '\n'.join(f"{itemservice.GetEgg(e.EggId).Name}: {e.SpawnCount}/{itemservice.GetEgg(e.EggId).SpawnsNeeded}{Checkmark if e.SpawnCount == itemservice.GetEgg(e.EggId).SpawnsNeeded else ''}" for e in list(sorted(trainer.Eggs, key=lambda x: x.EggId)))
	eggs = f'__Eggs__\n{eggString if eggString else "Obtain eggs from **/daily**"}'

	#Inventory Section
	newLine = '\n\n'
	inventory = f"__Inventory__\n{newLine.join(s for s in [pkbl,ptn,candy,eggs] if s)}\n\n${trainer.Money}"

	embed = discordservice.CreateEmbed(
			f"{targetUser.display_name}'s Trainer Info", 
			f"{stats}\n\n{inventory}", 
			TrainerColor)
	embed.set_thumbnail(url=targetUser.display_avatar.url)

	return await interaction.followup.send(embed=embed)

async def PrintUsePotion(interaction: Interaction, potion: Potion | None, result: tuple[bool, int]):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='usepotion', 
		responseInd=(0 if not result[0] else 1 if result[1] > 0 else 2) if potion else 3, 
		color=TrainerColor, 
		params=[potion.Name if potion else '', result[1]],
		eph=True)

async def PrintModifyTeam(interaction: Interaction, response: int, pkmnId: int):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='modifyteam', 
		responseInd=response, 
		color=TrainerColor, 
		params=[pokemonservice.GetPokemonById(pkmnId).Name] if pkmnId else [],
		eph=True)

async def PrintStarter(interaction: Interaction, trainer: Trainer, server: str):
	if trainer:
		embed = discordservice.CreateEmbed(
				f"{interaction.user.display_name}'s Journey Begins!",
				f"Starter: {pokemonservice.GetPokemonDisplayName(trainer.OwnedPokemon[0])}\nStarting Money: ${trainer.Money}\nStarting Pokeballs: 5",
				TrainerColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(trainer.OwnedPokemon[0]))
		await discordservice.SendEmbed(interaction, embed)
		embed2 = discordservice.CreateEmbed(
					f"Welcome to PokeTrainer!",
					f"You just began your journey in the server {server}. Use commands such as **/spawn** to interact with the bot! More interactions can be found using the **/help** command. Don't forget your **/daily** reward!",
					HelpColor)
		return await discordservice.SendDMs(interaction, [embed2])
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='starter', 
		responseInd=0, 
		color=TrainerColor)

async def PrintBadges(interaction: Interaction, targetUser: Member, region: str = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='badges', 
		responseInd=0 if not region else 1, 
		color=TrainerColor,
		params=[targetUser.display_name] if not region else [region],
		eph=True)

async def PrintRelease(interaction: Interaction, name: str):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='release', 
		responseInd=0, 
		color=TrainerColor, 
		params=[name],
		eph=True)

async def PrintDaily(interaction: Interaction, success: bool, eggName: str|None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='daily', 
		responseInd=0 if not success else 1 if not eggName else 2, 
		color=TrainerColor, 
		params=[eggName])

async def PrintMyEggs(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='myeggs', 
		responseInd=0, 
		color=TrainerColor, 
		params=[],
		eph=True)

async def PrintChangeZone(interaction: Interaction, responseId: int, params: list[str]):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='changezone', 
		responseInd=responseId, 
		color=TrainerColor, 
		params=params,
		eph=True)