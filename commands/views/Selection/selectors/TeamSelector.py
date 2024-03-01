import discord

class TeamSelector(discord.ui.Select):
    def __init__(self, data):
        options = [discord.SelectOption(
            label=f'Slot {i+1}',
            description=f"{data[i].GetNameString()} (Lvl. {data[i].Level})" if data[i] else 'Empty',
            value=f'{i}'
            ) for i in range(6)
        ]
        super().__init__(options=options, max_values=1, min_values=1, placeholder='Select team slot to change')
    
    async def callback(self, inter: discord.Interaction):
        await self.view.TeamSlotSelection(inter, self.values)