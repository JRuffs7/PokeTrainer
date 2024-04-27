from datetime import UTC, datetime
import discord

from globals import DateFormat, TrainerColor
from middleware.decorators import defer
from models.Trainer import Trainer
from services import itemservice, pokemonservice, trainerservice
from services.utility import discordservice


class InventoryView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.trainer = trainer
		self.allpkbls = itemservice.GetAllPokeballs()
		self.allpkbls.sort(key=lambda x: x.Id)
		self.allptns = itemservice.GetAllPotions()
		self.allptns.sort(key=lambda x: x.Id)
		self.allcndy = itemservice.GetAllCandies()
		self.allcndy.sort(key=lambda x: x.Id)
		self.allitems = itemservice.GetAllItems()
		self.allitems.sort(key=lambda x: x.Id)
		self.currentPage = 0
		super().__init__(timeout=300)
		self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
		self.prevBtn.callback = self.page_button
		self.add_item(self.prevBtn)
		self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
		self.nextBtn.callback = self.page_button
		self.add_item(self.nextBtn)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		if self.currentPage ==0:
			desc = self.Description(self.trainer.Pokeballs, self.allpkbls)
		elif self.currentPage == 1:
			desc = self.Description(self.trainer.Potions, self.allptns)
		elif self.currentPage == 2:
			desc = self.Description(self.trainer.Candies, self.allcndy)
		else:
			desc = self.Description(self.trainer.EvolutionItems, self.allitems)
		embed = discordservice.CreateEmbed(
				f'{self.interaction.user.display_name}s Inventory',
				desc,
				TrainerColor)
		embed.set_thumbnail(url=self.interaction.user.display_avatar.url)
		embed.set_footer(text=f'{self.currentPage+1}/4')
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, interaction: discord.Interaction):
		if interaction.data['custom_id'] == 'prev':
			self.currentPage -= 1
		else:
			self.currentPage += 1
		self.prevBtn.disabled = self.currentPage == 0
		self.nextBtn.disabled = self.currentPage == 3
		await self.update_message()

	@defer
	async def remove_button(self, interaction: discord.Interaction):
		await self.message.delete(delay=0.01)
		pkmn = self.pokemon[self.currentPage]
		data = next(p for p in self.pkmndata if p.Id == pkmn.Pokemon_Id)
		timeAdded = datetime.strptime(self.trainer.Daycare.pop(pkmn.Id), DateFormat).replace(tzinfo=UTC)
		hoursSpent = int((datetime.now(UTC) - timeAdded).total_seconds()//3600)
		pokemonservice.AddExperience(pkmn, data, 10*hoursSpent)
		trainerservice.UpsertTrainer(self.trainer)
		await interaction.followup.send(content=f'{pokemonservice.GetPokemonDisplayName(pkmn, data)} has been removed from the daycare and is now Level {pkmn.Level}!', ephemeral=True)

	def Description(self, ownList: dict[str,int], fullList: list):
		title = 'POKEBALLS' if self.currentPage == 0 else 'POTIONS' if self.currentPage == 1 else 'CANDY' if self.currentPage ==  2 else 'EVOLUTION ITEMS'
		if not [v for v in ownList.values() if v > 0]:
			return f'Money: {self.trainer.Money}\n\n**__{title}__\n\nYou do not own any of these items.'
		
		newLine = '\n'
		if self.currentPage == 3:
			return f'**Money: ${self.trainer.Money}**\n\n**__{title}__**\n{newLine.join([f"{i.Name}: {ownList[str(i.Id)]}" for i in fullList if str(i.Id) in ownList and ownList[str(i.Id)]>0])}'
		return f'**Money: ${self.trainer.Money}**\n\n**__{title}__**\n{newLine.join([f"{i.Name}: {ownList[str(i.Id)] if str(i.Id) in ownList else 0}" for i in fullList])}'
		