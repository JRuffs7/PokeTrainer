import discord

from globals import TrainerColor
from middleware.decorators import defer
from models.Item import Candy, Item, Pokeball, Potion
from models.Trainer import Trainer
from services import itemservice
from services.utility import discordservice


class InventoryView(discord.ui.View):

	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.trainer = trainer
		self.allitems = itemservice.GetAllItems()
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
		desc = self.Description()
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

	def Description(self):
		title = 'POKEBALLS' if self.currentPage == 0 else 'POTIONS' if self.currentPage == 1 else 'CANDY' if self.currentPage ==  2 else 'EVOLUTION ITEMS'
		match self.currentPage:
			case 0:
				itemList = itemservice.GetAllPokeballs()
			case 1:
				itemList = itemservice.GetAllPotions()
			case 2:
				itemList = itemservice.GetAllCandies()
			case _:
				itemList = itemservice.GetAllEvoItems()

		if not [i for i in itemList if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0]:
			return f'**Money: {self.trainer.Money}**\n\n**__{title}__**\n\nYou do not own any {title.lower()}.'
		
		newLine = '\n'
		if self.currentPage == 3:
			return f'**Money: ${self.trainer.Money}**\n\n**__{title}__**\n{newLine.join([f"{i.Name}: {self.trainer.Items[str(i.Id)]}" for i in itemList if str(i.Id) in self.trainer.Items and self.trainer.Items[str(i.Id)] > 0])}'
		return f'**Money: ${self.trainer.Money}**\n\n**__{title}__**\n{newLine.join([f"{i.Name}: {self.trainer.Items[str(i.Id)] if str(i.Id) in self.trainer.Items else 0}" for i in itemList])}'
		