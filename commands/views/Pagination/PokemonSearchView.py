from math import ceil
import discord
from table2ascii import Alignment, Merge, PresetStyle, table2ascii as t2a

from commands.views.Pagination.BasePaginationView import BasePaginationView
from globals import PokemonColor
from models.Pokemon import Pokemon, PokemonData
from services import pokemonservice
from services.utility import discordservice


class PokemonSearchView(BasePaginationView):

  def __init__(self, interaction: discord.Interaction, pageLength: int, dataList: list[Pokemon | PokemonData], title: str):
    self.title = title
    super(PokemonSearchView, self).__init__(interaction, pageLength, dataList)

  async def send(self):
    if not self.data:
      await self.interaction.response.send_message("There are no Pokemon that fit the search. Try again.", ephemeral=True)

    await self.interaction.response.send_message(view=self, ephemeral=True)
    self.message = await self.interaction.original_response()
    await self.update_message(self.data[:self.pageLength])

  async def update_message(self, data):
    self.update_buttons()
    embed = discordservice.CreateEmbed(self.title, self.SingleDesc(data[0]) if self.pageLength == 1 else self.ListDesc(data), PokemonColor)
    
    if self.pageLength == 1:
      embed.set_image(url=pokemonservice.GetPokemonImage(data[0]))

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

  def SingleDesc(self, pokemon: Pokemon):
    pkmn = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
    pkmnData = t2a(body=[['Rarity:', f"{pkmn.Rarity}", '|', 'Avg. Height:', pokemon.Height],
                         ['Color:',f"{pkmn.Color}", '|','Avg. Weight:', pokemon.Weight], 
                         ['Types:', f"{'/'.join(pkmn.Types)}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0)
    return f"**__{pokemonservice.GetPokemonDisplayName(pokemon, pokemon.IsFemale)}__**\n```{pkmnData}```"
  
  def ListDesc(self, data: list[PokemonData]):
    newline = '\n'
    slash = '\\'
    return f"{newline.join([f'**{x.Name}** ({slash.join(x.Types)})' if 'type' in self.title else f'**{x.Name}**' for x in data])}"
