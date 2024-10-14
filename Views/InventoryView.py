from math import ceil
import discord

from globals import TrainerColor
from middleware.decorators import defer
from models.Move import MoveData
from models.Trainer import Trainer
from services import itemservice, moveservice
from services.utility import discordservice


class InventoryView(discord.ui.View):

	def __init__(self, trainer: Trainer, thumbnail: str):
		self.trainer = trainer
		self.thumbnail = thumbnail
		super().__init__(timeout=300)
		self.AddButtons('pokeballs')

	def AddButtons(self, category: str):
		self.clear_items()
		if category == 'pokeballs':
			self.category = 'POKEBALLS'
			self.data = [i for i in itemservice.GetAllPokeballs() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
			btn1 = discord.ui.Button(label="TMs", style=discord.ButtonStyle.green, custom_id="tms")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Potions", style=discord.ButtonStyle.green, custom_id="potions")
			btn2.callback = self.cat_button
		if category == 'potions':
			self.category = 'POTIONS'
			self.data = [i for i in itemservice.GetAllPotions() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
			btn1 = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.green, custom_id="pokeballs")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Candy", style=discord.ButtonStyle.green, custom_id="candy")
			btn2.callback = self.cat_button
		if category == 'candy':
			self.category = 'CANDY'
			self.data = [i for i in itemservice.GetAllCandies() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
			btn1 = discord.ui.Button(label="Potions", style=discord.ButtonStyle.green, custom_id="potions")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Evo Items", style=discord.ButtonStyle.green, custom_id="evos")
			btn2.callback = self.cat_button
		if category == 'evos':
			self.category = 'EVOLUTION ITEMS'
			self.data = [i for i in itemservice.GetAllEvoItems() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
			btn1 = discord.ui.Button(label="Candy", style=discord.ButtonStyle.green, custom_id="candy")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="TMs", style=discord.ButtonStyle.green, custom_id="tms")
			btn2.callback = self.cat_button
		if category == 'tms':
			self.category = 'TECH MACHINES'
			self.data = moveservice.GetMovesById([int(i) for i in self.trainer.TMs if self.trainer.TMs[i] > 0])
			btn1 = discord.ui.Button(label="Evo Items", style=discord.ButtonStyle.green, custom_id="evos")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.green, custom_id="pokeballs")
			btn2.callback = self.cat_button
		self.currentpage = 1
		self.totalpages = max(ceil(len(self.data)/15),1)
		self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=(self.currentpage==self.totalpages), custom_id='prev')
		self.prevBtn.callback = self.page_button
		self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=(self.currentpage==self.totalpages), custom_id='next')
		self.nextBtn.callback = self.page_button
		self.add_item(btn1)
		self.add_item(self.prevBtn)
		self.add_item(self.nextBtn)
		self.add_item(btn2)

	@defer
	async def cat_button(self, inter: discord.Interaction):
		self.AddButtons(inter.data['custom_id'])
		await self.update_message()

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'prev':
			self.currentpage = (self.currentpage - 1) if self.currentpage > 1 else self.totalpages
		else:
			self.currentpage = (self.currentpage + 1) if self.currentpage < self.totalpages else 1
		await self.update_message()

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f'Your Inventory',
				self.Description(),
				TrainerColor,
				thumbnail=self.thumbnail,
				footer=f'{self.currentpage}/{self.totalpages}')
		await self.message.edit(embed=embed, view=self)

	def Description(self):
		if not self.data:
			return f'**Money: ${self.trainer.Money}**\n\n**__{self.category}__**\nYou do not own any {self.category.title()}.'
		self.data.sort(key=lambda x: x.Id)
		itemList = '\n'.join([f'TM{i.Id}-{i.Name}: {self.trainer.TMs[str(i.Id)]}' if type(i) is MoveData else f'{i.Name}: {self.trainer.Items[str(i.Id)]}' for i in self.data[(15*(self.currentpage-1)):(15*(self.currentpage))]])
		return f'**Money: ${self.trainer.Money}**\n\n**__{self.category}__**\n{itemList}'
		

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()