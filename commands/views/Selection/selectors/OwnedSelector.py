import uuid
import discord

from models.Pokemon import Pokemon
from services import pokemonservice

class OwnedSelector(discord.ui.Select):
    def __init__(self, data: list[Pokemon], max_select: int = 25, defaultId: str = None, customId: str = None, defer: bool = True):
        self.defer = defer
        if len(data) > 25:
            data = data[:25]
        pkmnData = pokemonservice.GetPokemonByIdList([d.Pokemon_Id for d in data])
        if len(data) < max_select:
            max_select = len(data)
        options=[discord.SelectOption(
            label=pokemonservice.GetPokemonDisplayName(d, next(p for p in pkmnData if d.Pokemon_Id == p.Id)),
            description= pokemonservice.GetPokemonDescription(d, next(p for p in pkmnData if d.Pokemon_Id == p.Id)),
            value=d.Id,
            default=(defaultId and d.Id == defaultId)
        ) for d in data]
        super().__init__(options=options, max_values=max_select, min_values=1, placeholder='Select Pokemon', custom_id=(customId if customId else uuid.uuid4().hex))
    
    async def callback(self, inter: discord.Interaction):
        if self.defer:
            await inter.response.defer()
        await self.view.PokemonSelection(inter, self.values)
