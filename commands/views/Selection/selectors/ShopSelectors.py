import discord

from models.Item import Pokeball, Potion


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
		await self.view.BuySellSelection(inter, self.values[0])
        
class ItemChoice(discord.ui.Select):
	def __init__(self, ballList: list[Pokeball], ptnList: list[Potion], buying: bool, default: str = None):
		options=([
			discord.SelectOption(
				label=f'{d.Name} - ${d.BuyAmount if buying else d.SellAmount}',
				description= f'{d.Description}' if buying else None,
				value=f'b{d.Id}',
				default=(default == f'b{d.Id}')
			) for d in ballList if (d.BuyAmount if buying else d.SellAmount)
		]+[
			discord.SelectOption(
				label=f'{d.Name} - ${d.BuyAmount if buying else d.SellAmount}',
				description= f'{d.Description}' if buying else None,
				value=f'p{d.Id}',
				default=(default == f'p{d.Id}')
			) for d in ptnList if (d.BuyAmount if buying else d.SellAmount)
		]) if len(ballList) > 0 or len(ptnList) > 0 else [
			discord.SelectOption(
					label='Not enough money' if buying else 'No Items To Sell',
					value='-1',
					default=True
				)
		]
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Item')
	
	async def callback(self, inter: discord.Interaction):
		await self.view.ItemSelection(inter, self.values[0])
        
class AmountChoice(discord.ui.Select):
	def __init__(self, maximum: int | None):
			maximum = 11 if not maximum or maximum > 10 else maximum + 1
			options=[
					discord.SelectOption(
						label=f'{num}',
						value=f'{num}'
					) for num in range(1, maximum)
			]
			super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Amount')
	
	async def callback(self, inter: discord.Interaction):
		await self.view.AmountSelection(inter, self.values[0])