import discord
from commands.views.Selection.selectors.GenericSelector import AmountSelector
from middleware.decorators import defer

from services import itemservice, trainerservice
from models.Trainer import Trainer
from commands.views.Selection.selectors.ShopSelectors import BuySell, ItemChoice


class SpecialShopView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.fullitemlist = itemservice.GetAllItems()
		self.buysellchoice = None
		self.itemchoice = None
		self.amountchoice = None
		super().__init__(timeout=300)
		self.buysellview = BuySell()
		self.add_item(self.buysellview)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def BuySellSelection(self, inter: discord.Interaction, choice: str):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.buysellchoice = choice
		self.itemchoice = None
		self.amountchoice = None
		if choice == 'buy':
			self.itemlist = [i for i in self.fullitemlist if i.Id in self.trainer.Shop.ItemIds and i.BuyAmount <= self.trainer.Money]
		else:
			self.itemlist = [itemservice.GetItem(int(i)) for i in self.trainer.EvolutionItems if self.trainer.EvolutionItems[i] > 0]

		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.itemlist, [], [], choice == 'buy')
		self.add_item(self.buysellview)
		self.add_item(self.itemview)
		await self.message.edit(content=f"Money: ${self.trainer.Money}", view=self)

	async def ItemSelection(self, inter: discord.Interaction, choice: str):
		if choice == '-1':
			return
		
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)
		
		self.itemchoice = next(i for i in self.fullitemlist if i.Id == int(choice[1:]))
		self.amountchoice = 1
		self.buysellview = BuySell(self.buysellchoice)
		self.itemview = ItemChoice(self.itemlist, [], [], self.buysellchoice == 'buy', choice)
		self.add_item(self.buysellview)
		self.add_item(self.itemview)

		if self.buysellchoice != 'buy':
			self.amountchoice = None
			self.amountview = AmountSelector(self.trainer.EvolutionItems[choice[1:]])
			self.add_item(self.amountview)
		currOwned = self.trainer.EvolutionItems[choice[1:]] if choice[1:] in self.trainer.EvolutionItems else 0
		await self.message.edit(content=f"Money: ${self.trainer.Money}\nYou currently have {currOwned} {self.itemchoice.Name}(s)", view=self)

	async def AmountSelection(self, inter: discord.Interaction, choice: str):
		self.amountchoice = int(choice)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='You left the shop.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.buysellchoice and self.itemchoice and self.amountchoice:
			buying = self.buysellchoice == 'buy'
			trainerservice.ModifyItemList(
				self.trainer.EvolutionItems, 
				str(self.itemchoice.Id), 
				self.amountchoice if buying else (0 - self.amountchoice),
			)
			self.trainer.Money += (0 - (self.amountchoice)*self.itemchoice.BuyAmount) if buying else ((self.amountchoice)*self.itemchoice.SellAmount)
			if buying:
				self.trainer.Shop.ItemIds.remove(self.itemchoice.Id)
			trainerservice.UpsertTrainer(self.trainer)

			for item in self.children:
				if type(item) is not discord.ui.Button:
					self.remove_item(item)
			self.buysellview = BuySell()
			self.add_item(self.buysellview)
			message = f"{self.itemchoice.Name} x{self.amountchoice} purchased for ${(self.amountchoice)*self.itemchoice.BuyAmount}" if buying else f"{self.itemchoice.Name} x{self.amountchoice} sold for ${(self.amountchoice)*self.itemchoice.SellAmount}"
			await self.message.edit(content=f"{message}\nMoney: ${self.trainer.Money}", view=self)

	async def send(self):
		await self.interaction.followup.send(content=f"Money: ${self.trainer.Money}", view=self, ephemeral=True)
		self.message = await self.interaction.original_response()