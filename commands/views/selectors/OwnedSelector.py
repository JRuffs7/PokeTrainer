import discord

class OwnedSelector(discord.ui.Select):
    def __init__(self, data, max_select, defaultId = None):
        if len(data) > 25:
            data = data[:25]
        if len(data) < max_select:
            max_select = len(data)
        options=[discord.SelectOption(
            label=f"{d.GetNameString()}",
            description= f"Lvl. {d.Level}({d.CurrentExp}/{(50 * d.Rarity) if d.Rarity <= 3 else 250}) | H:{d.Pokemon.Height} | W:{d.Pokemon.Weight} | Types: {'/'.join(d.Types)}",
            value=f'{d.Id}',
            default=(defaultId and d.Id == defaultId)
            ) for d in data
        ]
        super().__init__(options=options, max_values=max_select, min_values=1, placeholder='Select Pokemon')
    
    async def callback(self, inter: discord.Interaction):
        await self.view.PokemonSelection(inter, self.values)

    def SetValues(self, valueList):
        for option in self.options:
            if option.value in valueList:
                self.values.append(option.value)