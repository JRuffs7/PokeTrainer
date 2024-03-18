import discord


class AmountSelector(discord.ui.Select):
	def __init__(self, maximum: int | None):
			options=[
					discord.SelectOption(
						label=f'{num}',
						value=f'{num}'
					) for num in range(1, 11 if not maximum or maximum > 10 else maximum + 1)
			]
			super().__init__(options=options, max_values=1, min_values=1, placeholder='Choose Amount')
	
	async def callback(self, inter: discord.Interaction):
		await self.view.AmountSelection(inter, self.values[0])