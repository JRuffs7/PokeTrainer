from datetime import UTC, datetime
from models.Item import Potion
from models.Trainer import Trainer
from services import missionservice, pokemonservice, gymservice, zoneservice
from services.utility import discordservice
from discord import Interaction, Member
from globals import HelpColor, ShortDateFormat, TrainerColor

responseFile = "files/responsefiles/trainerresponses.json"

async def PrintTrainer(interaction: Interaction, trainer: Trainer, targetUser: Member):
	newDay = datetime.strptime(trainer.LastDaily, ShortDateFormat).date() < datetime.now(UTC).date() if trainer.LastDaily else True
	#Stats Section
	healthString = f'HP: {trainer.Health}'
	zoneString = f'Current Zone: **{zoneservice.GetZone(trainer.CurrentZone).Name}**'
	if newDay:
		dailyString = f'Daily Reward: **Ready**'
	else:
		dailyString = 'Daily Reward: On cooldown'
	if not trainer.Shop or datetime.strptime(trainer.Shop.LastRecycle, ShortDateFormat).date() < datetime.now(UTC).date():
		shopString = f'Sp. Shop Refresh: **Ready**'
	else:
		shopString = 'Sp. Shop Refresh: On cooldown'

	newLine = '\n'
	stats = f'__Trainer Stats__\n{newLine.join([healthString, zoneString, dailyString, shopString])}'

	#Mission Section
	dailyMission = missionservice.GetDailyMission(trainer.DailyMission.MissionId) if trainer.DailyMission else None
	weeklyMission = missionservice.GetWeeklyMission(trainer.WeeklyMission.MissionId) if trainer.WeeklyMission else None
	if not dailyMission:
		dmissionStr = 'Use **/daily** to acquire a daily mission.'
	else:
		if newDay:
			progressStr = 'Expired'
		else:
			progressStr = f'{trainer.DailyMission.Progress}/{dailyMission.Amount}' if trainer.DailyMission.Progress < dailyMission.Amount else 'Completed (Rewarded 3x Rare Candy)'
		dmissionStr = f'{dailyMission.Description}\n**{progressStr}**'
	if not weeklyMission:
		wmissionStr = 'Use **/daily** to acquire a weekly mission.'
	else:
		if (datetime.now(UTC).date()-datetime.strptime(trainer.WeeklyMission.DayStarted, ShortDateFormat).date()).days >= 7:
			progressStr = 'Expired'
		else:
			progressStr = f'{trainer.WeeklyMission.Progress}/{weeklyMission.Amount}' if trainer.WeeklyMission.Progress < weeklyMission.Amount else 'Completed (Rewarded 1x Masterball)'
		wmissionStr = f'{weeklyMission.Description}\n**{progressStr}**'
	mission = f'__Missions__\n{dmissionStr}\n{wmissionStr}'

	#Dex Section
	totalPkmn = pokemonservice.GetAllPokemon()
	totalPkdx = len(set(p.PokedexId for p in totalPkmn))
	pokedexString = f'Pokedex: {len(trainer.Pokedex)}/{totalPkdx} ({round((len(trainer.Pokedex)*100)/totalPkdx)}%)'
	formdexString = f'Form Dex: {len(trainer.Formdex)}/{len(totalPkmn)} ({round((len(trainer.Formdex)*100)/len(totalPkmn))}%)'
	shinydexString = f'Shiny Dex: {len(trainer.Shinydex)}/{len(totalPkmn)} ({round((len(trainer.Shinydex)*100)/len(totalPkmn))}%)'
	badgeString = f'Gym Badges: {len(trainer.Badges)}/{len(gymservice.GetAllBadges())}'
	dex = f'__Completion__\n{newLine.join([pokedexString, formdexString, shinydexString, badgeString])}'

	#Other Section
	eggString = f'Eggs: {len(trainer.Eggs)}/5'
	daycareString = f'Daycare: {len(trainer.Daycare)}/2'
	other = f'__Other__\n{newLine.join([eggString, daycareString])}'

	embed = discordservice.CreateEmbed(
			f"{targetUser.display_name}'s Trainer Info", 
			f"{stats}\n\n{mission}\n\n{dex}\n\n{other}", 
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
		pkmnData = pokemonservice.GetPokemonById(trainer.OwnedPokemon[0].Pokemon_Id)
		embed = discordservice.CreateEmbed(
				f"{interaction.user.display_name}'s Journey Begins!",
				f"Starter: {pokemonservice.GetPokemonDisplayName(trainer.OwnedPokemon[0], pkmnData)}\nStarting Money: ${trainer.Money}\nStarting Pokeballs: 5",
				TrainerColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(trainer.OwnedPokemon[0], pkmnData))
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

async def PrintDaily(interaction: Interaction, success: bool, boosted: bool, freeMasterball: bool, newWeekly: bool, eggName: str|None):
	responseID = 0 if not success else 1 if not eggName else 2
	missionStr = f'\nAcquired a new Weekly Mission.' if newWeekly else ''
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='daily', 
		responseInd=responseID+2 if freeMasterball else responseID, 
		color=TrainerColor, 
		params=['20' if boosted else '10', '500' if boosted else '200', missionStr, eggName])

async def PrintMyEggs(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='myeggs', 
		responseInd=0, 
		color=TrainerColor, 
		params=[],
		eph=True)

async def PrintMyPokemon(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='mypokemon', 
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