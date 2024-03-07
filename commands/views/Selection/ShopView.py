import discord
from middleware.decorators import button_check

from services import itemservice, trainerservice
from models.Trainer import Trainer
from commands.views.Selection.selectors.ShopSelectors import BuySell, ItemChoice, AmountChoice


class ShopView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.fullballList, self.fullptnList = itemservice.GetFullShop()
		super().__init__(timeout=300)
		self.buysellview = BuySell()
		self.add_item(self.buysellview)

	@button_check
	async def BuySellSelection(self, inter: discord.Interaction, choice: str):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.buysellchoice = choice
		if choice == 'buy':
			self.ballList = [b for b in self.fullballList if b.BuyAmount <= self.trainer.Money]
			self.potionList = [p for p in self.fullptnList if p.BuyAmount <= self.trainer.Money]
		else:
			self.ballList = [itemservice.GetPokeball(int(i)) for i in self.trainer.Pokeballs if self.trainer.Pokeballs[i] > 0]
			self.potionList = [itemservice.GetPotion(int(i)) for i in self.trainer.Potions if self.trainer.Potions[i] > 0]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.buysellchoice == 'buy')
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		await self.message.edit(view=self)
		await inter.response.defer()

	@button_check
	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		if choice == '-1':
			return
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.itemchoice = choice
		isPokeball = choice.startswith('b')
		itemId = int(choice[1:])
		item = next(i for i in (self.fullballList if isPokeball else self.fullptnList) if i.Id == itemId)
		if self.buysellchoice == 'buy':
			maxAmount = self.trainer.Money // item.BuyAmount
		else:
			maxAmount = self.trainer.Pokeballs[choice[1:]] if isPokeball else self.trainer.Potions[choice[1:]]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.buysellchoice == 'buy', self.itemchoice)
		self.amountview = AmountChoice(maxAmount)
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		self.add_item(self.amountview)
		await self.message.edit(view=self)
		await inter.response.defer()

	@button_check
	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		self.amountchoice = int(choice)
		await inter.response.defer()


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='You left the shop.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.buysellchoice and self.itemchoice and self.amountchoice:
			item = next(i for i in (self.fullballList if self.itemchoice.startswith('b') else self.fullptnList) if i.Id == int(self.itemchoice[1:]))
			buying = self.buysellchoice == 'buy'
			trainerservice.ModifyItemList(
				self.trainer.Pokeballs if self.itemchoice.startswith('b') else self.trainer.Potions, 
				self.itemchoice[1:], 
				self.amountchoice if buying else (0 - self.amountchoice),
				)
			self.trainer.Money += (0 - (self.amountchoice)*item.BuyAmount) if buying else ((self.amountchoice)*item.SellAmount)
			trainerservice.UpsertTrainer(self.trainer)

			self.clear_items()
			message = f"{item.Name} x{self.amountchoice} purchased for ${(self.amountchoice)*item.BuyAmount}" if buying else f"{item.Name} x{self.amountchoice} sold for ${(self.amountchoice)*item.SellAmount}"
			await self.message.edit(content=f"{message}\nYou now have **${self.trainer.Money}**", view=self)
		await inter.response.defer()


	async def send(self):
		await self.interaction.response.send_message(content=f"Money: ${self.trainer.Money}", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
