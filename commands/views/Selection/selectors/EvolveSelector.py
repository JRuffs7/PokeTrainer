import discord

from models.Pokemon import PokemonData

class EvolveSelector(discord.ui.Select):
    def __init__(self, data: list[PokemonData]):
        if len(data) > 25:
            data = data[:25]
        options=[discord.SelectOption(
            label=f"{d.Name}",
            description= f"Types: {'/'.join(d.Types) if d.Types else ''} | Rarity: {d.Rarity}" if d.Id != -1 else 'Random Evolution From This Line',
            value=f'{d.Id}'
            ) for d in data
        ]
        super().__init__(options=options, max_values=1, min_values=1, placeholder='Evolve Into...')
    
    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.view.EvolveSelection(inter, self.values[0])