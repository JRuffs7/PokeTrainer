from math import ceil
import discord

from commands.views.Pagination.BasePaginationView import BasePaginationView
from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import TrainerColor
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice
from services.utility import discordservice


class PokedexView(BasePaginationView):

  def __init__(
      self, interaction: discord.Interaction, trainer: Trainer, pageLength: int, data: list[Pokemon], title: str):
    self.trainer = trainer
    self.title = title
    super(PokedexView, self).__init__(interaction, pageLength, data)

  async def send(self, ephemeral: bool = False):
    if not self.data:
      await self.interaction.response.send_message("Target Trainer does not own any Pokemon that fit the filters.", ephemeral=True)
    await self.interaction.response.send_message(view=self, ephemeral=ephemeral)
    self.message = await self.interaction.original_response()
    await self.update_message(self.data[:self.pageLength])

  async def update_message(self, data: list[Pokemon]):
    self.update_buttons()
    embed = discordservice.CreateEmbed(
        self.title,
        self.SingleEmbedDesc(data[0]) if self.pageLength == 1 else self.ListEmbedDesc(data),
        TrainerColor)
    if self.pageLength == 1:
      embed.set_image(url=pokemonservice.GetPokemonImage(data[0]))
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

  def SingleEmbedDesc(self, pokemon: Pokemon):
    pkmn = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
    pkmnData = t2a(body=[['CurrentExp:', f"{pokemon.CurrentExp}/{pokemonservice.NeededExperience(pokemon.Level, pkmn.Rarity, len(pkmn.EvolvesInto) > 0)}", '|', 'Height:', pokemon.Height],
                            ['Can Evolve:',f"{'Yes' if pokemonservice.CanTrainerPokemonEvolve(pokemon) else 'No'}", '|','Weight:', pokemon.Weight], 
                            ['Types:', f"{'/'.join(pkmn.Types)}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0)
    return f"**__{pokemonservice.GetPokemonDisplayName(pokemon)} (Lvl. {pokemon.Level})__**\n```{pkmnData}```"

  def ListEmbedDesc(self, data: list[Pokemon]):
    newline = '\n'
    return f"{newline.join([pokemonservice.GetPokemonDisplayName(x) + f' (Lvl. {x.Level})' for x in data])}"