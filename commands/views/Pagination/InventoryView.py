from math import ceil
import discord

from globals import TrainerColor
from middleware.decorators import defer
from models.Trainer import Trainer
from services import itemservice
from services.utility import discordservice


class InventoryView(discord.ui.View):

	def __init__(self, trainer: Trainer, image: str):
		self.trainer = trainer
		self.image = image
		self.allitems = itemservice.GetAllItems()
		self.currentpage = 1
		self.totalpages = 3+max(ceil(len([i for i in self.trainer.Items if int(i) in [it.Id for it in self.allitems if it.EvolutionItem]])/15),1)
		super().__init__(timeout=300)
		self.prevBtn = discord.ui.Button(label="<", style=discord.ButtonStyle.primary, disabled=True, custom_id='prev')
		self.prevBtn.callback = self.page_button
		self.add_item(self.prevBtn)
		self.nextBtn = discord.ui.Button(label=">", style=discord.ButtonStyle.primary, disabled=False, custom_id='next')
		self.nextBtn.callback = self.page_button
		self.add_item(self.nextBtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f'Your Inventory',
				self.Description(),
				TrainerColor,
				thumbnail=self.image,
				footer=f'{self.currentpage}/{self.totalpages}')
		await self.message.edit(embed=embed, view=self)

	@defer
	async def page_button(self, inter: discord.Interaction):
		if inter.data['custom_id'] == 'prev':
			self.currentpage -= 1
		else:
			self.currentpage += 1
		self.prevBtn.disabled = self.currentpage == 1
		self.nextBtn.disabled = self.currentpage == self.totalpages
		await self.update_message()

	def Description(self):
		match self.currentpage:
			case 1:
				title = 'POKEBALLS'
				itemList = [i for i in itemservice.GetAllPokeballs() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
				itemList.sort(key=lambda x: x.Id)
			case 2:
				title = 'POTIONS'
				itemList = [i for i in itemservice.GetAllPotions() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
				itemList.sort(key=lambda x: x.Id)
			case 3:
				title = 'CANDY'
				itemList = [i for i in itemservice.GetAllCandies() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
				itemList.sort(key=lambda x: x.Id)
			case _:
				title = 'EVOLUTION ITEMS'
				itemList = [i for i in itemservice.GetAllEvoItems() if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]
				itemList.sort(key=lambda x: x.Name)
				itemList = itemList[(15*(self.currentpage-4)):(15*(self.currentpage-3))]
		if not itemList:
			return f'**Money: {self.trainer.Money}**\n\n**__{title}__**\n\nYou do not own any {title.title()}.'
		
		newLine = '\n'
		return f'**Money: ${self.trainer.Money}**\n\n**__{title}__**\n{newLine.join([f"{i.Name}: {self.trainer.Items[str(i.Id)]}" for i in itemList if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0])}'
		

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()
		await self.update_message()