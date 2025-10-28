from math import ceil
import discord
from table2ascii import Alignment, PresetStyle, table2ascii as t2a

from globals import TradeColor
from middleware.decorators import defer
from models.Item import Item
from models.Move import MoveData
from models.Trainer import Trainer
from services import itemservice, moveservice
from services.utility import discordservice


class ShopView(discord.ui.View):

	def __init__(self, trainer: Trainer|None):
		self.trainer = trainer
		super().__init__(timeout=300)
		self.AddButtons('pokeballs')

	def AddButtons(self, category: str):
		self.clear_items()
		if category == 'pokeballs':
			self.category = 'POKEBALLS'
			self.data = itemservice.GetAllPokeballs()
			self.data.sort(key=lambda x: x.BuyAmount)
			btn1 = discord.ui.Button(label="TMs", style=discord.ButtonStyle.green, custom_id="tms")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Potions", style=discord.ButtonStyle.green, custom_id="potions")
			btn2.callback = self.cat_button
		if category == 'potions':
			self.category = 'POTIONS'
			self.data = itemservice.GetAllPotions()
			self.data.sort(key=lambda x: x.BuyAmount)
			btn1 = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.green, custom_id="pokeballs")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Evo Items", style=discord.ButtonStyle.green, custom_id="evos")
			btn2.callback = self.cat_button
		if category == 'evos':
			self.category = 'EVOLUTION ITEMS'
			self.data = itemservice.GetAllEvoItems()
			self.data.sort(key=lambda x: x.BuyAmount)
			btn1 = discord.ui.Button(label="Potions", style=discord.ButtonStyle.green, custom_id="potions")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="TMs", style=discord.ButtonStyle.green, custom_id="tms")
			btn2.callback = self.cat_button
		if category == 'tms':
			self.category = 'TECH MACHINES'
			self.data = moveservice.GetTMMoves()
			self.data.sort(key=lambda x: x.Id)
			btn1 = discord.ui.Button(label="Evo Items", style=discord.ButtonStyle.green, custom_id="evos")
			btn1.callback = self.cat_button
			btn2 = discord.ui.Button(label="Pokeballs", style=discord.ButtonStyle.green, custom_id="pokeballs")
			btn2.callback = self.cat_button
		self.currentpage = 1
		self.totalpages = ceil(len(self.data)/10)
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

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				'PokeTrainer Item Shop',
				self.EmbedDesc(),
				TradeColor)
		embed.set_footer(text=f"{self.currentpage}/{self.totalpages}")
		await self.message.edit(embed=embed, view=self)

	def EmbedDesc(self):
		data = self.data[(10*(self.currentpage-1)):(10*self.currentpage)]
		shopData = t2a(
			header=['Item Name', 'Buy', 'Sell'],
			body=[
				[
					f'TM{d.Id}-{d.Name}' if type(d) is MoveData else d.Name, 
					f'${d.Cost}' if type(d) is MoveData else f'${d.BuyAmount}' if d.BuyAmount else '-', 
					f'${int(d.Cost/2)}' if type(d) is MoveData else f'${d.SellAmount}' if d.SellAmount else '-'
				] for d in data
			], 
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.minimalist,
			cell_padding=0)
		return f'Trainer Money: **${self.trainer.Money if self.trainer else "0"}**\n\nUse **/buy** and **/sell** to trade items.\n```{shopData}```'

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()