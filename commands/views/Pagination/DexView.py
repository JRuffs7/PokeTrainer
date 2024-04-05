from math import ceil
import discord
from table2ascii import Alignment, Merge, PresetStyle, table2ascii as t2a

from commands.views.Pagination.BasePaginationView import BasePaginationView

from globals import Dexmark, TrainerColor
from models.Pokemon import PokemonData
from models.Trainer import Trainer
from services.utility import discordservice


class DexView(BasePaginationView):

	def __init__(
			self, interaction: discord.Interaction, targetUser: discord.Member, trainer: Trainer, dexType: int|None, pageLength: int, data: list[PokemonData], title: str):
		self.targetuser = targetUser
		self.trainer = trainer
		self.dexType = dexType
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
		trainerdex = self.trainer.Pokedex if not self.dexType else self.trainer.Formdex
		pkmnData = t2a(body=[['Rarity:', f'{pokemon.Rarity}', '|', 'Height:', pokemon.Height/10],
                         ['Color:',f'{pokemon.Color}', '|','Weight:', pokemon.Weight/10], 
                         ['Capture:',f'{pokemon.CaptureRate}/255', '|','Female:', f'{pokemon.FemaleChance}/8' if pokemon.FemaleChance >= 0 else 'N/A'], 
                         ['Types:', f'{"/".join(pokemon.Types)}', Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0) if pokemon.PokedexId in self.trainer.Pokedex else ''
		dataString = f'\n```{pkmnData}```' if pkmnData else ''
		if self.currentPage == 1:
			return f"**__{pokemon.Name}__** {Dexmark if (pokemon.PokedexId if not self.dexType else pokemon.Id) in trainerdex else ''}{dataString}"
		return f"**__{pokemon.Name}__** {Dexmark if pokemon.Id in self.trainer.Shinydex else ''}{dataString}"

	def ListEmbedDesc(self, data: list[PokemonData]):
		trainerdex = self.trainer.Pokedex if not self.dexType else self.trainer.Formdex if self.dexType == 1 else self.trainer.Shinydex
		newline = '\n'
		dexList = [f'{x.Name} {Dexmark if (x.PokedexId if not self.dexType else x.Id) in trainerdex else ""}' for x in data]
		return f'{newline.join(dexList)}'
