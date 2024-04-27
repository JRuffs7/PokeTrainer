import discord

class EvolveSelector(discord.ui.Select):
    def __init__(self, data: list):
        if len(data) > 25:
            data = data[:25]
        options=[discord.SelectOption(
            label=f"{d['Pokemon'].Name}",
            description= f"{d['Description']}",
            value=f"{d['Pokemon'].Id}"
            ) for d in data
        ]
        super().__init__(options=options, max_values=1, min_values=1, placeholder='Evolve Into...')
    
    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.view.EvolveSelection(inter, self.values[0])