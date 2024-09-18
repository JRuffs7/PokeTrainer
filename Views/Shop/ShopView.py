from math import ceil
import discord
from table2ascii import Alignment, PresetStyle, table2ascii as t2a
from Views.BasePageView import BasePageView

from globals import TradeColor
from models.Item import Item
from models.Move import MoveData
from models.Trainer import Trainer
from services import itemservice, moveservice
from services.utility import discordservice


class ShopView(BasePageView):

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
		super(ShopView, self).__init__(trainer.UserId if trainer else None, 10, pkbl+ptn+cnd+evo+tms)

	async def update_message(self, data: list[Item|MoveData]):
		self.update_buttons()
		embed = discordservice.CreateEmbed(
				'PokeTrainer Item Shop',
				self.EmbedDesc(data),
				TradeColor)
		embed.set_footer(text=f"{self.currentPage}/{ceil(len(self.data)/self.pageLength)}")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="|<", style=discord.ButtonStyle.green, custom_id="first")
	async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
	async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">|", style=discord.ButtonStyle.green, custom_id="last")
	async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if await self.button_click(interaction, button.custom_id):
			await self.update_message(self.get_currentPage_data())

	def EmbedDesc(self, data: list[Item|MoveData]):
		shopData = t2a(
			header=['Item Name', 'Buy', 'Sell'],
			body=[
				[
					f'TM-{d.Name}' if type(d) is MoveData else d.Name, 
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