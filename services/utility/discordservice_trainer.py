from models.Item import Potion
from models.Trainer import Trainer
from services import pokemonservice, gymservice, trainerservice
from services.utility import discordservice
from discord import Interaction, Member
from globals import TrainerColor

responseFile = "files/responsefiles/trainerresponses.json"

async def PrintTrainer(interaction: Interaction, trainer: Trainer, targetUser: Member):
	#Stats Section
	totalPkmn = pokemonservice.GetPokemonCount()
	totalBadges = len(gymservice.GetAllBadges())

	stats = f"__Trainer Stats__\nHP: {trainer.Health}\nPokedex: {len(trainer.Pokedex)}/{totalPkmn} ({round((len(trainer.Pokedex)*100)/totalPkmn)}%)\nPokemon Caught: {len(trainer.OwnedPokemon)}\nShiny Count: {len([x for x in trainer.OwnedPokemon if x.IsShiny])}\nGym Badges: {len(trainer.Badges)}/{totalBadges}"

	#Inventory Section
	items = trainerservice.GetInventory(trainer)
	pkblList = items[1]
	ptnList = items[2]
	newline = '\n'
	pokeballString = f"\n{newline.join([f'{i}: {pkblList[i]}' for i in pkblList])}" if len(pkblList) else ""
	breakStr = f"\n" if len(pkblList) and len(ptnList) else ""
	potionString = f"\n{newline.join([f'{i}: {ptnList[i]}' for i in ptnList])}" if len(ptnList) else ""
	inventory = f"__Inventory__{pokeballString}{breakStr}{potionString}\n\n${trainer.Money}" if interaction.user.id == targetUser.id else ""

	embed = discordservice.CreateEmbed(
			f"{targetUser.display_name}'s Trainer Info", 
			f"{stats}\n\n{inventory}", 
			TrainerColor)
	embed.set_thumbnail(url=targetUser.display_avatar.url)

	return await interaction.response.send_message(embed=embed)

async def PrintUsePotion(interaction: Interaction, potion: Potion, result: tuple[bool, int]):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='usepotion', 
		responseInd=0 if not result[0] else 1 if result[1] > 0 else 2, 
		color=TrainerColor, 
		params=[potion.Name, result[1]],
		eph=True)

async def PrintModifyTeam(interaction: Interaction, response: int, pkmnId: str):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='modifyteam', 
		responseInd=response, 
		color=TrainerColor, 
		params=[pokemonservice.GetPokemonById(pkmnId).Name] if pkmnId else [],
		eph=True)

async def PrintStarter(interaction: Interaction, trainer: Trainer):
	if trainer:
		embed = discordservice.CreateEmbed(
				f"{interaction.user.display_name}'s Journey Begins!",
				f"Starter: {pokemonservice.GetPokemonDisplayName(trainer.OwnedPokemon[0])}\nStarting Money: ${trainer.Money}\nStarting Pokeballs: 5",
				TrainerColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(trainer.OwnedPokemon[0]))
		return await discordservice.SendEmbed(interaction, embed)
	return await discordservice.SendCommandResponse(
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
		command='modifyteam', 
		responseInd=0, 
		color=TrainerColor, 
		params=[name],
		eph=True)