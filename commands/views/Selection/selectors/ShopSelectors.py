import discord

from models.Item import Candy, Pokeball, Potion


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
	def __init__(self, ballList: list[Pokeball], ptnList: list[Potion], cndyList: list[Candy], buying: bool, default: str = None):
		options=([
			discord.SelectOption(
				label=f'{b.Name} - ${b.BuyAmount if buying else b.SellAmount}',
				description= f'{b.Description}' if buying else None,
				value=f'b{b.Id}',
				default=(default == f'b{b.Id}')
			) for b in ballList if (b.BuyAmount if buying else b.SellAmount)
		]+[
			discord.SelectOption(
				label=f'{p.Name} - ${p.BuyAmount if buying else p.SellAmount}',
				description= f'{p.Description}' if buying else None,
				value=f'p{p.Id}',
				default=(default == f'p{p.Id}')
			) for p in ptnList if (p.BuyAmount if buying else p.SellAmount)
		]+[
			discord.SelectOption(
				label=f'{c.Name} - ${c.BuyAmount if buying else c.SellAmount}',
				description= f'{c.Description}' if buying else None,
				value=f'c{c.Id}',
				default=(default == f'c{c.Id}')
			) for c in cndyList if (c.BuyAmount if buying else c.SellAmount)
		]) if len(ballList) > 0 or len(ptnList) > 0 or len(cndyList) > 0 else [
			discord.SelectOption(
					label='Not enough money' if buying else 'No Items To Sell',
					value='-1',
					default=True
				)
		]
		super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Item')
	
	async def callback(self, inter: discord.Interaction):
		await self.view.ItemSelection(inter, self.values[0])
      