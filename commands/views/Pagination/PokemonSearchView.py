import discord

from commands.views.Pagination.BasePaginationView import BasePaginationView
from globals import PokemonColor
from middleware.decorators import button_check
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
    embed = discordservice.CreateEmbed(self.title, self.CreateEmbedDesc(data), PokemonColor)
    
    if self.pageLength == 1:
      embed.set_image(url=pokemonservice.GetPokemonImage(data[0]))

    embed.set_footer(text=f"{self.currentPage}/{int(len(self.data)/self.pageLength)}")
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

  def CreateEmbedDesc(self, data: list[Pokemon | PokemonData]):
    if self.pageLength == 1:
      pkmn = pokemonservice.GetPokemonById(data[0].Pokemon_Id)
      return f"**__{pokemonservice.GetPokemonDisplayName(data[0], data[0].IsFemale)}__**\nAvg. Height: {data[0].Height}\nAvg. Weight: {data[0].Weight}\nTypes: {'/'.join(pkmn.Types)}\nRarity: {pkmn.Rarity}"
    
    newline = '\n'
    return f"{newline.join(sorted(set([x.Name for x in data])))}"
