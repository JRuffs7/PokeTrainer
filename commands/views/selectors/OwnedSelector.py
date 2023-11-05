from typing import Any
import discord

class TeamSelector(discord.ui.Select):
    def __init__(self, data):
        options = [discord.SelectOption(
            label=f'Slot {i+1}',
            description=f"{data[i].GetNameString()} (Lvl. {data[i].Pokemon.Level})" if data[i] else 'Empty',
            value=f'{i}'
            ) for i in range(6)
        ]
        super().__init__(options=options, max_values=1, min_values=1, placeholder='Select team slot to change')
    
    async def callback(self, inter: discord.Interaction):
        await self.view.TeamSlotSelection(inter, self.values)

class OwnedSelector(discord.ui.Select):
    def __init__(self, data, max_select):
        if len(data) > 25:
            data = data[:25]
        options=[discord.SelectOption(
            label=f"{d.GetNameString()}",
            description= f"Lvl. {d.Pokemon.Level}({d.Pokemon.CurrentExp}/{(50 * d.Rarity) if d.Rarity <= 3 else 250}) | Types: {'/'.join(d.Types)}",
            value=f'{d.Pokemon.Id}'
            ) for d in data
        ]
        super().__init__(options=options, max_values=max_select, min_values=1, placeholder='Select Pokemon to place in slot')
    
    async def callback(self, inter: discord.Interaction):
        await self.view.PokemonSelection(inter, self.values)