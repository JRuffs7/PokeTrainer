import discord

from models.Pokemon import Pokemon
from services import pokemonservice

class OwnedSelector(discord.ui.Select):
    def __init__(self, data: list[Pokemon], max_select: int = 25, defaultId: str = None):
        if len(data) > 25:
            data = data[:25]
        if len(data) < max_select:
            max_select = len(data)
        options=[discord.SelectOption(
            label=pokemonservice.GetPokemonDisplayName(d),
            description= pokemonservice.GetOwnedPokemonDescription(d),
            value=f'{d.Id}',
            default=(defaultId and d.Id == defaultId)
        ) for d in data]
        super().__init__(options=options, max_values=max_select, min_values=1, placeholder='Select Pokemon')
    
    async def callback(self, inter: discord.Interaction):
        await self.view.PokemonSelection(inter, self.values)
