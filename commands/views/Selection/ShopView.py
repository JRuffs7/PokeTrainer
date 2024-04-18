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
		self.buysellchoice = None
		self.itemchoice = None
		self.amountchoice = None
		super().__init__(timeout=300)
		self.buysellview = BuySell()
		self.add_item(self.buysellview)

	@button_check
	async def BuySellSelection(self, inter: discord.Interaction, choice: str):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.buysellchoice = choice
		self.itemchoice = None
		self.amountchoice = None
		if choice == 'buy':
			self.ballList = [b for b in self.fullballList if b.BuyAmount and b.BuyAmount <= self.trainer.Money]
			self.potionList = [p for p in self.fullptnList if p.BuyAmount and p.BuyAmount <= self.trainer.Money]
			self.candyList = []
		else:
			self.ballList = [itemservice.GetPokeball(int(i)) for i in self.trainer.Pokeballs if self.trainer.Pokeballs[i] > 0]
			self.potionList = [itemservice.GetPotion(int(i)) for i in self.trainer.Potions if self.trainer.Potions[i] > 0]
			self.candyList = [itemservice.GetCandy(int(i)) for i in self.trainer.Candies if self.trainer.Candies[i] > 0]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.candyList, choice == 'buy')
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		await self.message.edit(content=f"Money: ${self.trainer.Money}", view=self)

	@button_check
	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		if choice == '-1':
			return
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.itemchoice = next(i for i in (self.fullballList if choice[0] == 'b' else self.fullptnList if choice[0] == 'p' else self.fullcndylist) if i.Id == int(choice[1:]))
		self.amountchoice = None
		trainerList = self.trainer.Pokeballs if choice[0] == 'b' else self.trainer.Potions if choice[0] == 'p' else self.trainer.Candies
		if self.buysellchoice == 'buy':
			maxAmount = self.trainer.Money // self.itemchoice.BuyAmount
		else:
			maxAmount = trainerList[choice[1:]]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.ballList, self.potionList, self.candyList, self.buysellchoice == 'buy', choice)
		self.amountview = AmountSelector(maxAmount)
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		self.add_item(self.amountview)
		currOwned = trainerList[choice[1:]] if choice[1:] in trainerList else 0
		await self.message.edit(content=f"Money: ${self.trainer.Money}\nYou currently have {currOwned} {self.itemchoice.Name}(s)", view=self)

	@button_check
	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		self.amountchoice = int(choice)


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
			buying = self.buysellchoice == 'buy'
			trainerservice.ModifyItemList(
				self.trainer.Pokeballs if self.itemchoice.__class__.__name__ == 'Pokeball' else self.trainer.Potions if self.itemchoice.__class__.__name__ == 'Potion' else self.trainer.Candies, 
				str(self.itemchoice.Id), 
				self.amountchoice if buying else (0 - self.amountchoice),
				)
			self.trainer.Money += (0 - (self.amountchoice)*self.itemchoice.BuyAmount) if buying else ((self.amountchoice)*self.itemchoice.SellAmount)
			trainerservice.UpsertTrainer(self.trainer)

			self.clear_items()
			message = f"{self.itemchoice.Name} x{self.amountchoice} purchased for ${(self.amountchoice)*self.itemchoice.BuyAmount}" if buying else f"{self.itemchoice.Name} x{self.amountchoice} sold for ${(self.amountchoice)*self.itemchoice.SellAmount}"
			await self.message.edit(content=f"{message}\nYou now have **${self.trainer.Money}**", view=self)


	async def send(self):
		await self.interaction.followup.send(content=f"Money: ${self.trainer.Money}", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()
