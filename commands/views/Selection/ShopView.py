import discord
from commands.views.Selection.selectors.GenericSelector import AmountSelector
from middleware.decorators import button_check

from services import itemservice, trainerservice
from models.Trainer import Trainer
from commands.views.Selection.selectors.ShopSelectors import BuySell, ItemChoice


class ShopView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.fullballList = itemservice.GetAllPokeballs()
		self.fullptnList = itemservice.GetAllPotions()
		self.fullcndylist = itemservice.GetAllCandies()
		super().__init__(timeout=300)
		self.buysellview = BuySell()
		self.add_item(self.buysellview)

	@button_check
	async def BuySellSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.buysellchoice = choice
		self.itemchoice = None
		self.amountchoice = None
		if choice == 'buy':
			self.ballList = [b for b in self.fullballList if b.BuyAmount and b.BuyAmount <= self.trainer.Money]
			self.potionList = [p for p in self.fullptnList if p.BuyAmount and p.BuyAmount <= self.trainer.Money]
			self.candyList = [c for c in self.fullcndylist if c.BuyAmount and c.BuyAmount <= self.trainer.Money]
		else:
			self.ballList = [itemservice.GetPokeball(int(i)) for i in self.trainer.Pokeballs if self.trainer.Pokeballs[i] > 0]
			self.potionList = [itemservice.GetPotion(int(i)) for i in self.trainer.Potions if self.trainer.Potions[i] > 0]
			self.candyList = [itemservice.GetCandy(int(i)) for i in self.trainer.Candies if self.trainer.Candies[i] > 0]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.candyList, self.buysellchoice == 'buy')
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		await self.message.edit(view=self)

	@button_check
	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		if choice == '-1':
			return
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.itemchoice = choice
		self.amountchoice = None
		itemId = int(choice[1:])
		item = next(i for i in (self.fullballList if choice[0] == 'b' else self.fullptnList if choice[0] == 'p' else self.candyList) if i.Id == itemId)
		if self.buysellchoice == 'buy':
			maxAmount = self.trainer.Money // item.BuyAmount
		else:
			maxAmount = self.trainer.Pokeballs[choice[1:]] if choice[0] == 'b' else self.trainer.Potions[choice[1:]] if choice[0] == 'p' else self.trainer.Candies[choice[1:]]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.candyList, self.buysellchoice == 'buy', self.itemchoice)
		self.amountview = AmountSelector(maxAmount)
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		self.add_item(self.amountview)
		await self.message.edit(view=self)

	@button_check
	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		self.amountchoice = int(choice)


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		self.clear_items()
		await self.message.edit(content='You left the shop.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		if self.buysellchoice and self.itemchoice and self.amountchoice:
			item = next(i for i in (self.fullballList if self.itemchoice[0] == 'b' else self.fullptnList if self.itemchoice[0] == 'p' else self.fullcndylist) if i.Id == int(self.itemchoice[1:]))
			buying = self.buysellchoice == 'buy'
			trainerservice.ModifyItemList(
				self.trainer.Pokeballs if self.itemchoice[0] == 'b' else self.trainer.Potions if self.itemchoice[0] == 'p' else self.trainer.Candies, 
				self.itemchoice[1:], 
				self.amountchoice if buying else (0 - self.amountchoice),
				)
			self.trainer.Money += (0 - (self.amountchoice)*item.BuyAmount) if buying else ((self.amountchoice)*item.SellAmount)
			trainerservice.UpsertTrainer(self.trainer)

			self.clear_items()
			message = f"{item.Name} x{self.amountchoice} purchased for ${(self.amountchoice)*item.BuyAmount}" if buying else f"{item.Name} x{self.amountchoice} sold for ${(self.amountchoice)*item.SellAmount}"
			await self.message.edit(content=f"{message}\nYou now have **${self.trainer.Money}**", view=self)


	async def send(self):
		await self.interaction.followup.send(content=f"Money: ${self.trainer.Money}", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
