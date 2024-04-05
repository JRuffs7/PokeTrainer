from math import ceil
import discord
from commands.views.Pagination.BasePaginationView import BasePaginationView

from globals import Dexmark, TrainerColor
from models.Egg import TrainerEgg
from services import itemservice
from services.utility import discordservice


class EggView(BasePaginationView):

	def __init__(self, interaction: discord.Interaction, targetUser: discord.User | discord.Member, pageLength: int, data: list[TrainerEgg]):
		self.title = f"{targetUser.display_name}'s Egg List"
		super(EggView, self).__init__(interaction, pageLength, data)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
		await self.update_message(self.data[:self.pageLength])

	async def update_message(self, data: list[TrainerEgg]):
		self.update_buttons()
		embed = discordservice.CreateEmbed(
				self.title,
				self.SingleEmbedDesc(data[0]) if self.pageLength == 1 else self.ListEmbedDesc(data),
				TrainerColor)
		if self.pageLength == 1:
			embed.set_image(url=itemservice.GetEgg(data[0].EggId).Sprite)
		else:
			embed.set_thumbnail(url=self.user.display_avatar.url)
		embed.set_footer(text=f"{self.currentPage}/{ceil(len(self.data)/self.pageLength)}")
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label="|<", style=discord.ButtonStyle.green, custom_id="first")
	async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.button_click(interaction, button.custom_id)
		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="previous")
	async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.button_click(interaction, button.custom_id)
		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.button_click(interaction, button.custom_id)
		await self.update_message(self.get_currentPage_data())

	@discord.ui.button(label=">|", style=discord.ButtonStyle.green, custom_id="last")
	async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.button_click(interaction, button.custom_id)
		await self.update_message(self.get_currentPage_data())

	def SingleEmbedDesc(self, egg: TrainerEgg):
		eggData = itemservice.GetEgg(egg.EggId)
		return f'**__{eggData.Name}{f" {Dexmark}" if egg.SpawnCount == eggData.SpawnsNeeded else ""}__**\nHatch Rarity: {", ".join([str(h) for h in eggData.Hatch])}\nProgress (/spawn): {egg.SpawnCount}/{eggData.SpawnsNeeded}'

	def ListEmbedDesc(self, data: list[TrainerEgg]):
		return '\n'.join([f'{itemservice.GetEgg(egg.EggId).Name} ({egg.SpawnCount}/{itemservice.GetEgg(egg.EggId).SpawnsNeeded}){f" {Dexmark}" if egg.SpawnCount == itemservice.GetEgg(egg.EggId).SpawnsNeeded else ""}' for egg in data])
