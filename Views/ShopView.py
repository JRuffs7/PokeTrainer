from math import ceil
import discord
from table2ascii import Alignment, PresetStyle, table2ascii as t2a
from Views.BasePageView import BasePageView

from globals import TradeColor
from middleware.decorators import defer
from models.Item import Item
from models.Move import MoveData
from models.Trainer import Trainer
from services import itemservice, moveservice
from services.utility import discordservice


class ShopView(discord.ui.View):

	def __init__(self, trainer: Trainer|None, itemType: str|None):
		self.trainer = trainer
		pkbl = [i for i in itemservice.GetAllPokeballs() if i.BuyAmount or i.SellAmount] if not itemType or itemType == 'pokeball' else []
		pkbl.sort(key=lambda x: x.BuyAmount)
		ptn = [i for i in itemservice.GetAllPotions() if i.BuyAmount or i.SellAmount] if not itemType or itemType == 'potion' else []
		ptn.sort(key=lambda x: x.BuyAmount)
		cnd = [i for i in itemservice.GetAllCandies() if i.BuyAmount or i.SellAmount] if not itemType or itemType == 'candy' else []
		cnd.sort(key=lambda x: x.BuyAmount)
		evo = [i for i in itemservice.GetAllEvoItems() if i.BuyAmount or i.SellAmount] if not itemType or itemType == 'evolution' else []
		evo.sort(key=lambda x: x.Name)
		tms = [m for m in moveservice.GetTMMoves() if m.Cost] if not itemType or itemType == 'tm' else []
		tms.sort(key=lambda x: x.Name)
		self.currentpage = 1
		self.data = pkbl+ptn+cnd+evo+tms
		self.totalpages = ceil(len(self.data)/10)
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

	async def update_message(self):
		self.update_buttons()
		embed = discordservice.CreateEmbed(
				'PokeTrainer Item Shop',
				self.EmbedDesc(),
				TradeColor)
		embed.set_footer(text=f"{self.currentpage}/{self.totalpages}")
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

	def EmbedDesc(self, data: list[Item|MoveData]):
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
		return f'Trainer Money: ${self.trainer.Money}\n\nUse **/buy** and **/sell** to trade items.\n```{shopData}```'

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message(self.data[:self.pageLength])