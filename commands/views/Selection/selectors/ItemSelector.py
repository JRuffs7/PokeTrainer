import discord

from models.Item import Item

class ItemSelector(discord.ui.Select):
    def __init__(self, data: list[Item], default: str|None = None):
        if len(data) > 25:
            data = data[:25]
        options=[discord.SelectOption(
            label=f"{i.Name}",
            description= f"{i.Description}",
            value=f"{i.Id}",
            default=(f"{i.Id}" == default if default else False)
            ) for i in data
        ]
        super().__init__(options=options, max_values=1, min_values=1, placeholder='Pick One...')
    
    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.view.ItemSelection(inter, self.values[0])
      