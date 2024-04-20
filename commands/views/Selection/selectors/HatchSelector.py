import discord

from models.Egg import TrainerEgg
from services import itemservice

class HatchSelector(discord.ui.Select):
    def __init__(self, data: list[TrainerEgg]):
        if len(data) > 25:
            data = data[:25]
        options=[discord.SelectOption(
            label=f"{itemservice.GetEgg(e.EggId).Name}",
            description= f"Hatch Rarity: {', '.join([str(h) for h in itemservice.GetEgg(e.EggId).Hatch])}",
            value=e.Id
            ) for e in data
        ]
        super().__init__(options=options, max_values=len(data), min_values=1, placeholder='Hatch Egg(s)...')
    
    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.view.EggSelection(inter, self.values)