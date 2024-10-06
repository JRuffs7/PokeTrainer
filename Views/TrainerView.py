from datetime import UTC, datetime
from math import ceil, floor
import discord

from globals import Dexmark, Incomplete, ShortDateFormat, TrainerColor, region_name
from middleware.decorators import defer
from models.Trainer import Trainer
from services import gymservice, itemservice, missionservice, pokemonservice, trainerservice
from services.utility import discordservice


class TrainerView(discord.ui.View):

	def __init__(self, targetUser: discord.User|discord.Member, trainer: Trainer):
		self.targetuser = targetUser
		self.trainer = trainer
		self.currentpage = 1
		self.totalpkmn = pokemonservice.GetAllPokemon()
		self.allregions = gymservice.GetRegions()
		self.totalpages = len(self.allregions)+3
		super().__init__(timeout=300)
		self.firstbtn = discord.ui.Button(label="|<", style=discord.ButtonStyle.green, custom_id="first", disabled=True)
		self.firstbtn.callback = self.page_button
		self.prevbtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
		self.prevbtn.callback = self.page_button
		self.nextbtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
		self.nextbtn.callback = self.page_button
		self.lastbtn = discord.ui.Button(label=">|", style=discord.ButtonStyle.green, custom_id="last")
		self.lastbtn.callback = self.page_button
		self.add_item(self.firstbtn)
		self.add_item(self.prevbtn)
		self.add_item(self.nextbtn)
		self.add_item(self.lastbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.targetuser.display_name}'s Trainer Info",
				self.EmbedDesc(),
				TrainerColor,
				thumbnail=(self.targetuser.display_avatar.url),
				footer=f'{self.currentpage}/{self.totalpages}')
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'first':
			self.currentpage = 1
		elif inter.data['custom_id'] == 'previous':
			self.currentpage -= 1
		elif inter.data['custom_id'] == 'next':
			self.currentpage += 1
		elif inter.data['custom_id'] == 'last':
			self.currentpage = self.totalpages

		self.firstbtn.disabled = self.currentpage == 0
		self.prevbtn.disabled = self.currentpage == 0
		self.lastbtn.disabled = self.currentpage == self.totalpages
		self.nextbtn.disabled = self.currentpage == self.totalpages
		await self.update_message()

	def EmbedDesc(self):
		if self.currentpage == 1:
			basic = f'Region: {region_name(self.trainer.Region)}\nDaily Reward: {"**Ready**" if trainerservice.CanUseDaily(self.trainer) else "Obtained"}'
			dailyMission = missionservice.GetDailyMission(self.trainer.DailyMission.MissionId) if self.trainer.DailyMission else None
			weeklyMission = missionservice.GetWeeklyMission(self.trainer.WeeklyMission.MissionId) if self.trainer.WeeklyMission else None
			if not dailyMission:
				dmissionStr = 'Use **/daily** to acquire a daily mission.'
			else:
				if trainerservice.CanUseDaily(self.trainer):
					dmissionStr = '**Expired**'
				else:
					dmissionStr = f'{dailyMission.Description}\n{self.trainer.DailyMission.Progress}/{dailyMission.Amount}' if self.trainer.DailyMission.Progress < dailyMission.Amount else '**Completed (Rewarded 3x Rare Candy)**'
			if not weeklyMission:
				wmissionStr = 'Use **/daily** to acquire a weekly mission.'
			else:
				if (datetime.now(UTC).date()-datetime.strptime(self.trainer.WeeklyMission.DayStarted, ShortDateFormat).date()).days >= 7:
					wmissionStr = '**Expired**'
				else:
					wmissionStr = f'{weeklyMission.Description}\n{self.trainer.WeeklyMission.Progress}/{weeklyMission.Amount}' if self.trainer.WeeklyMission.Progress < weeklyMission.Amount else '**Completed (Rewarded 1x Masterball)**'
			mission = f'Daily Mission: {dmissionStr}\nWeekly Mission: {wmissionStr}'
			pkdx = len(set(p.PokedexId for p in self.totalpkmn))
			pokedex = f'Pokedex Completion: {len(self.trainer.Pokedex)}/{pkdx} ({round((len(self.trainer.Pokedex)*100)/pkdx)}%)'
			region = f'Region Completion: {len([r for r in gymservice.GetRegions() if trainerservice.RegionCompleted(self.trainer, r)])}/{len(gymservice.GetRegions())}'
			eggs = f'Eggs Obtained: {len(self.trainer.Eggs)}/{(8 if trainerservice.HasRegionReward(self.trainer, 8) else 5)}'
			daycare = f'Daycare Slots: {len(self.trainer.Daycare)}/2'

			title = '__**BASE INFORMATION**__'
			desc = f'{basic}\n\n{mission}\n\n{pokedex}\n{region}\n\n{eggs}\n{daycare}'
		elif self.currentpage == 2:
			totalPkdx = len(set(p.PokedexId for p in self.totalpkmn))
			livingDex = len(set(p.Pokemon_Id for p in self.trainer.OwnedPokemon))
			pokedexString = f'Pokedex: {len(self.trainer.Pokedex)}/{totalPkdx} ({round((len(self.trainer.Pokedex)*100)/totalPkdx)}%)'
			formdexString = f'Form Dex: {len(self.trainer.Formdex)}/{len(self.totalpkmn)} ({round((len(self.trainer.Formdex)*100)/len(self.totalpkmn))}%)'
			shinydexString = f'Shiny Dex: {len(self.trainer.Shinydex)}/{len(self.totalpkmn)} ({round((len(self.trainer.Shinydex)*100)/len(self.totalpkmn))}%)'
			livedexString = f'Living Dex: {livingDex}/{len(self.totalpkmn)} ({round((livingDex*100)/len(self.totalpkmn))}%)'

			title = '__**NATIONAL POKEDEX**__'
			desc = f'{pokedexString}\n{formdexString}\n{shinydexString}\n{livedexString}'
		elif self.currentpage == 3:
			eggString = f'Eggs: {len(self.trainer.Eggs)}/{(8 if trainerservice.HasRegionReward(self.trainer, 8) else 5)}'
			if len(self.trainer.Eggs) == 0:
				eggString += '\nNo Eggs! Use **/daily** to obtain more.'
			else:
				for e in self.trainer.Eggs:
					egg = itemservice.GetEgg(e.EggId)
					eggString += f'\n{egg.Name} ({e.SpawnCount}/{egg.SpawnsNeeded}){f" {Dexmark}" if e.SpawnCount == egg.SpawnsNeeded else ""}'
			daycareString = f'Daycare Slots: {len(self.trainer.Daycare)}/2'
			if len(self.trainer.Daycare) == 0:
				daycareString += '\nUse **/daycare** to put a Pokemon in the Daycare.'
			else:
				for p in self.trainer.Daycare:
					pokemon = next(po for po in self.trainer.OwnedPokemon if po.Id == p)
					data = next(po for po in self.totalpkmn if po.Id == pokemon.Pokemon_Id)
					daycareString += f'\n{pokemonservice.GetPokemonDisplayName(pokemon, data)}'
					
			title = f'__**OTHER**__'
			desc = f'{eggString}\n\n{daycareString}'
		elif self.currentpage < self.totalpages:
			region = self.currentpage-3
			badges = [b.Id for b in gymservice.GetBadgesByRegion(region)]
			numBadges = [b for b in self.trainer.Badges if b in badges]
			eliteFour = 1 if region in self.trainer.EliteFour else 0
			pokemon = [p for p in self.totalpkmn if p.Generation == region]
			idList = [p.Id for p in pokemon]
			pkdx = list(set(p.PokedexId for p in pokemon))
			cmpltPkdx = [p for p in self.trainer.Pokedex if p in pkdx]
			cmpltFrmdx = [p for p in self.trainer.Formdex if p in idList]
			cmpltShndx = [p for p in self.trainer.Shinydex if p in idList]
			cmpltLvdx = list(set(p.Id for p in self.trainer.OwnedPokemon if p.Id in idList))

			completionString = f'**Completion (Excl. Shiny): {round(((len(cmpltPkdx)+len(cmpltFrmdx)+len(numBadges)+eliteFour)*100)/(len(pkdx)+len(idList)+len(badges)+1),2)}%**'
			badgeString = f'Badges: {len(numBadges)}/{len(badges)}'
			eliteFourString = f'Champion: {Incomplete if region not in self.trainer.EliteFour else Dexmark}'
			pokedexString = f'Pokedex: {len(cmpltPkdx)}/{len(pkdx)} ({round((len(cmpltPkdx)*100)/len(pkdx))}%)'
			formdexString = f'Form Dex: {len(cmpltFrmdx)}/{len(idList)} ({round((len(cmpltFrmdx)*100)/len(idList))}%)'
			shinydexString = f'Shiny Dex: {len(cmpltShndx)}/{len(idList)} ({round((len(cmpltShndx)*100)/len(idList))}%)'
			livedexString = f'Living Dex: {len(cmpltLvdx)}/{len(idList)} ({round((len(cmpltLvdx)*100)/len(idList))}%)'

			title = f'__**{region_name(region).upper()} REGION**__'
			desc = f'{completionString}\n\n{badgeString}\n{eliteFourString}\n\n{pokedexString}\n{formdexString}\n{shinydexString}\n{livedexString}'
		else:
			region = 1000
			badges = [b.Id for b in gymservice.GetBadgesByRegion(region)]
			numBadges = [b for b in self.trainer.Badges if b in badges]

			completionString = f'**Completion: {floor(len(numBadges)*100/len(badges))}%**'
			badgeString = f'Badges: {len(numBadges)}/{len(badges)}'
			eliteFourString = f'Champion: {Incomplete if len(numBadges) < len(badges) else Dexmark}'

			title = f'__**{region_name(region).upper()} REGION**__'
			desc = f'{completionString}\n\n{badgeString}\n{eliteFourString}'
		return f'{title}\n\n{desc}'

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()