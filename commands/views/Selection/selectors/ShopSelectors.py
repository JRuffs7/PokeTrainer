import discord

from models.Item import Candy, Item, Pokeball, Potion


class BuySell(discord.ui.Select):
	def __init__(self, default: str = None):
		options=[
				discord.SelectOption(
					label='Buy',
					description='Purchase items from the shop.',
					value='buy',
					default=(default == 'buy')
				),
				discord.SelectOption(
					label='Sell',
					description= 'Sell items from your inventory.',
					value='sell',
					default=(default == 'sell')
				),
		]
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Buy/Sell')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.BuySellSelection(inter, self.values[0])
        
class ItemChoice(discord.ui.Select):
	def __init__(self, itemList: list[Item], buying: bool, default: str = None):
		options=([
			discord.SelectOption(
				label=f'{i.Name} - ${i.BuyAmount if buying else i.SellAmount}',
				description= f'{i.Description}' if buying else None,
				value=f'{i.Id}',
				default=(default == f'{i.Id}')
			) for i in itemList if (i.BuyAmount if buying else i.SellAmount)
		]) if len(itemList) > 0 else [
			discord.SelectOption(
					label='Not enough money' if buying else 'No Items To Sell',
					value='-1',
					default=True
				)
		]
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Item')
	
	async def callback(self, inter: discord.Interaction):
		await inter.response.defer()
		await self.view.ItemSelection(inter, self.values[0])
      