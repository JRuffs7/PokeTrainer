from datetime import UTC, datetime
import discord

from Views.Selectors import PokemonSelector
from globals import DateFormat, TrainerColor
from middleware.decorators import defer
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import commandlockservice, pokemonservice, trainerservice
from services.utility import discordservice


class DayCareView(discord.ui.View):

	def __init__(self, user: discord.User|discord.Member, trainer: Trainer, owndaycare: bool):
		self.user = user
		self.trainer = trainer
		self.daycare = trainerservice.GetDaycare(trainer)
		self.daycaredata = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in self.daycare])
		self.owndaycare = owndaycare
		self.currentpage = 0
		super().__init__(timeout=300)
		self.AddButtons()

	def AddButtons(self):
		if len(self.trainer.Daycare) > 1:
			self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
			self.prevBtn.callback = self.page_button
			self.add_item(self.prevBtn)
		if self.owndaycare:
			rmvbtn = discord.ui.Button(label="Remove", style=discord.ButtonStyle.danger)
			rmvbtn.callback = self.remove_button
			self.add_item(rmvbtn)
		if len(self.trainer.Daycare) > 1:
			self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
			self.nextBtn.callback = self.page_button
			self.add_item(self.nextBtn)
		clsbtn = discord.ui.Button(label="Close", style=discord.ButtonStyle.gray)
		clsbtn.callback = self.close_button
		self.add_item(clsbtn)

	async def on_timeout(self):
		if self.owndaycare:
			commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.user.display_name}'s Daycare",
				self.SingleEmbedDesc(),
				TrainerColor,
				image=(pokemonservice.GetPokemonImage(
					self.daycare[self.currentpage], 
					next(p for p in self.daycaredata if p.Id == self.daycare[self.currentpage].Pokemon_Id))),
				footer=f"{self.currentpage+1}/{len(self.trainer.Daycare)}")
		await self.message.edit(embed=embed, view=self)
	
	@defer
	async def close_button(self, inter: discord.Interaction):
		await self.on_timeout()

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'prev':
			self.currentpage -= 1
		else:
			self.currentpage += 1
		self.prevBtn.disabled = self.currentpage == 0
		self.nextBtn.disabled = self.currentpage == (len(self.trainer.Daycare)-1)
		await self.update_message()

	@defer
	async def remove_button(self, inter: discord.Interaction):
		if not self.owndaycare or inter.user.id != self.user.id:
			return
		
		pkmn = self.daycare[self.currentpage]
		data = next(p for p in self.daycaredata if p.Id == pkmn.Pokemon_Id)
		timeAdded = datetime.strptime(self.trainer.Daycare.pop(pkmn.Id), DateFormat).replace(tzinfo=UTC)
		minutesSpent = int((datetime.now(UTC) - timeAdded).total_seconds()//60)
		pokemonservice.AddExperience(pkmn, data, minutesSpent)
		trainerservice.UpsertTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content=f'**{pokemonservice.GetPokemonDisplayName(pkmn, data)}** has been removed from the daycare and is now **Level {pkmn.Level}**!', embed=None, view=None)
		self.stop()
		
	def SingleEmbedDesc(self):
		pkmn = self.daycare[self.currentpage]
		data = next(p for p in self.daycaredata if p.Id == pkmn.Pokemon_Id)
		timeAdded = datetime.strptime(self.trainer.Daycare[pkmn.Id], DateFormat).replace(tzinfo=UTC)
		minutesSpent = int((datetime.now(UTC) - timeAdded).total_seconds()//60)
		simLevel = pokemonservice.SimulateLevelGain(pkmn, data, minutesSpent)
		return f'**__{pokemonservice.GetPokemonDisplayName(pkmn, data)}__**\n\nLevel: {pkmn.Level} -> {simLevel}'

	async def NewEgg(self, inter: discord.Interaction):
		self.clear_items()
		nxtbtn = discord.ui.Button(label="Next", style=discord.ButtonStyle.gray)
		nxtbtn.callback = self.next_button
		self.add_item(nxtbtn)
		embed = discordservice.CreateEmbed(
			f"New Egg!",
			f'Your Pokemon **{" and ".join([pokemonservice.GetPokemonDisplayName(d, next(da for da in self.daycaredata if da.Id == d.Pokemon_Id)) for d in self.daycare])}** had an egg! Check out the progress and information using **/myeggs**.',
			TrainerColor)
		await inter.followup.send(embed=embed, view=self)
		self.message = await inter.original_response()

	@defer
	async def next_button(self, inter: discord.Interaction):
		self.clear_items()
		self.AddButtons()
		await self.update_message()

	async def send(self, inter: discord.Interaction):
		if self.owndaycare and trainerservice.CheckDaycareForEgg(self.trainer):
			await self.NewEgg(inter)
		else:
			await inter.followup.send(view=self)
			self.message = await inter.original_response()
			await self.update_message()


class DayCareAddView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemonList: list[Pokemon]):
		self.trainer = trainer
		self.pokemonlist = pokemonList
		self.pokemonchoice = None if len(pokemonList) > 1 else pokemonList[0].Id
		super().__init__(timeout=300)
		if not self.pokemonchoice:
			cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)
			cnclbtn.callback = self.cancel_button
			sbmtbtn = discord.ui.Button(label="Submit", style=discord.ButtonStyle.green)
			sbmtbtn.callback = self.submit_button
			self.ownlist = PokemonSelector(pokemonList)
			self.add_item(cnclbtn)
			self.add_item(sbmtbtn)
			self.add_item(self.ownlist)

	async def on_timeout(self):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.delete()
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		self.pokemonchoice = choice

	@defer
	async def cancel_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await self.on_timeout()

	@defer
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		if not self.pokemonchoice:
			return
		await self.AddToDaycare()
	
	async def AddToDaycare(self):
		self.clear_items()
		pkmn = next(p for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)
		data = next(p for p in self.daycaredata if p.Id == pkmn.Pokemon_Id)
		self.trainer.Daycare[pkmn.Id] = datetime.now(UTC).strftime(DateFormat)
		trainerservice.UpsertTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await self.message.edit(content=f'Added **{pokemonservice.GetPokemonDisplayName(pkmn, data)}** to your daycare.', view=self)
		
	async def send(self, inter: discord.Interaction):
		if self.pokemonchoice:
			await inter.followup.send(content='Adding to Daycare...')
			self.message = await inter.original_response()
			await self.AddToDaycare()
		else:
			await inter.followup.send(view=self)
			self.message = await inter.original_response()
