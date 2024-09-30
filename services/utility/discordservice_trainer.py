from datetime import UTC, datetime
from models.Trainer import Trainer
from services import missionservice, pokemonservice, gymservice, trainerservice
from services.utility import discordservice
from discord import Interaction, Member
from globals import ShortDateFormat, TrainerColor, region_name

responseFile = "files/responsefiles/trainerresponses.json"

async def PrintTrainer(interaction: Interaction, trainer: Trainer, targetUser: Member):
	newDay = datetime.strptime(trainer.LastDaily, ShortDateFormat).date() < datetime.now(UTC).date() if trainer.LastDaily else True
	#Stats Section
	regionStr = f'Current Region: **{region_name(trainer.Region)}**'
	if newDay:
		dailyString = f'Daily Reward: **Ready**'
	else:
		dailyString = 'Daily Reward: On cooldown'
	if not trainer.Shop or datetime.strptime(trainer.Shop.LastRecycle, ShortDateFormat).date() < datetime.now(UTC).date():
		shopString = f'Sp. Shop Refresh: **Ready**'
	else:
		shopString = 'Sp. Shop Refresh: On cooldown'

	newLine = '\n'
	stats = f'__Trainer Stats__\n{newLine.join([regionStr, dailyString, shopString])}'

	#Mission Section
	dailyMission = missionservice.GetDailyMission(trainer.DailyMission.MissionId) if trainer.DailyMission else None
	weeklyMission = missionservice.GetWeeklyMission(trainer.WeeklyMission.MissionId) if trainer.WeeklyMission else None
	if not dailyMission:
		dmissionStr = '**Daily**: Use **/daily** to acquire a daily mission.'
	else:
		if newDay:
			progressStr = 'Expired'
		else:
			progressStr = f'{trainer.DailyMission.Progress}/{dailyMission.Amount}' if trainer.DailyMission.Progress < dailyMission.Amount else 'Completed (Rewarded 3x Rare Candy)'
		dmissionStr = f'**Daily**: {dailyMission.Description}\n{progressStr}'
	if not weeklyMission:
		wmissionStr = '**Weekly**: Use **/daily** to acquire a weekly mission.'
	else:
		if (datetime.now(UTC).date()-datetime.strptime(trainer.WeeklyMission.DayStarted, ShortDateFormat).date()).days >= 7:
			progressStr = 'Expired'
		else:
			progressStr = f'{trainer.WeeklyMission.Progress}/{weeklyMission.Amount}' if trainer.WeeklyMission.Progress < weeklyMission.Amount else 'Completed (Rewarded 1x Masterball)'
		wmissionStr = f'**Weekly**: {weeklyMission.Description}\n{progressStr}'
	mission = f'__Missions__\n{dmissionStr}\n{wmissionStr}'

	#Dex Section
	totalPkmn = pokemonservice.GetAllPokemon()
	totalPkdx = len(set(p.PokedexId for p in totalPkmn))
	livingDex = len(set(p.Pokemon_Id for p in trainer.OwnedPokemon))
	pokedexString = f'Pokedex: {len(trainer.Pokedex)}/{totalPkdx} ({round((len(trainer.Pokedex)*100)/totalPkdx)}%)'
	formdexString = f'Form Dex: {len(trainer.Formdex)}/{len(totalPkmn)} ({round((len(trainer.Formdex)*100)/len(totalPkmn))}%)'
	livedexString = f'Living Dex: {livingDex}/{len(totalPkmn)} ({round((livingDex*100)/len(totalPkmn))}%)'
	shinydexString = f'Shiny Dex: {len(trainer.Shinydex)}/{len(totalPkmn)} ({round((len(trainer.Shinydex)*100)/len(totalPkmn))}%)'
	badgeString = f'Gym Badges: {len(trainer.Badges)}/{len(gymservice.GetAllBadges())}'
	dex = f'__Completion__\n{newLine.join([pokedexString, formdexString, livedexString, shinydexString, badgeString])}'

	#Other Section
	eggString = f'Eggs: {len(trainer.Eggs)}/{(8 if trainerservice.HasRegionReward(trainer, 8) else 5)}'
	daycareString = f'Daycare: {len(trainer.Daycare)}/{4 if trainerservice.HasRegionReward(trainer, 6) else 2}'
	other = f'__Other__\n{newLine.join([eggString, daycareString])}'

	embed = discordservice.CreateEmbed(
			f"{targetUser.display_name}'s Trainer Info", 
			f"{stats}\n\n{mission}\n\n{dex}\n\n{other}", 
			TrainerColor)
	embed.set_thumbnail(url=targetUser.display_avatar.url)
	return await interaction.followup.send(embed=embed)

async def PrintModifyTeam(interaction: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='modifyteam', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintStarter(interaction: Interaction, response: int, params: list):
	await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='starter', 
		responseInd=response,
		params=params,
		color=TrainerColor)

async def PrintBadges(interaction: Interaction, targetUser: Member, region: str = None):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='badges', 
		responseInd=0 if not region else 1, 
		color=TrainerColor,
		params=[targetUser.display_name] if not region else [region])

async def PrintRelease(interaction: Interaction, params: list):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='release', 
		responseInd=0, 
		color=TrainerColor, 
		params=params)

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

async def PrintMyEggsResponse(inter: Interaction, response: int, params: list):
	return await discordservice.SendCommandResponse(
		interaction=inter, 
		filename=responseFile, 
		command='myeggs', 
		responseInd=response, 
		color=TrainerColor, 
		params=params)

async def PrintMyPokemon(interaction: Interaction):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='mypokemon', 
		responseInd=0, 
		color=TrainerColor, 
		params=[])

async def PrintChangeZone(interaction: Interaction, responseId: int, params: list[str]):
	return await discordservice.SendCommandResponse(
		interaction=interaction, 
		filename=responseFile, 
		command='changezone', 
		responseInd=responseId, 
		color=TrainerColor, 
		params=params)