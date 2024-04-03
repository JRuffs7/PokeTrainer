from math import ceil
import discord

from commands.views.Pagination.BasePaginationView import BasePaginationView

from globals import Checkmark, TrainerColor
from models.Pokemon import PokemonData
from models.Trainer import Trainer
from services.utility import discordservice


class DexView(BasePaginationView):

	def __init__(
			self, interaction: discord.Interaction, targetUser: discord.Member, trainer: Trainer, dexType: int, pageLength: int, data: list[PokemonData], title: str):
		self.targetuser = targetUser
		self.dexType = dexType
		self.trainerdex = trainer.Pokedex if dexType == 0 else trainer.Formdex if dexType == 1 else trainer.Shinydex
		self.shinydex = trainer.Shinydex
		self.title = title
		super(DexView, self).__init__(interaction, pageLength, data)

	async def send(self, ephemeral: bool = False):
		await self.interaction.followup.send(view=self, ephemeral=ephemeral)
		self.message = await self.interaction.original_response()
		await self.update_message(self.data[:self.pageLength])

	async def update_message(self, data: list[PokemonData]):
		self.update_buttons()
		embed = discordservice.CreateEmbed(
				self.title,
				self.SingleEmbedDesc(data[0]) if self.pageLength == 1 else self.ListEmbedDesc(data),
				TrainerColor)
		if self.pageLength == 1:
			embed.set_image(url=data[0].Sprite if self.currentPage == 1 else data[0].ShinySprite)
		else:
			embed.set_thumbnail(url=self.targetuser.display_avatar.url)
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

	def SingleEmbedDesc(self, pokemon: PokemonData):
		if self.currentPage == 1:
			return f"**__{pokemon.Name}__** {Checkmark if pokemon.Id in self.trainerdex else ''}"
		return f"**__{pokemon.Name}__** {Checkmark if pokemon.Id in self.shinydex else ''}"

	def ListEmbedDesc(self, data: list[PokemonData]):
		newline = '\n'
		dexList = [f'{x.Name} {Checkmark if (x.PokedexId if self.dexType == 0 else x.Id) in self.trainerdex else ""}' for x in data]
		return f'{newline.join(dexList)}'
