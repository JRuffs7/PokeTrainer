from math import ceil
import discord

from commands.views.Pagination.BasePaginationView import BasePaginationView
from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import TrainerColor
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice
from services.utility import discordservice


class MyPokemonView(BasePaginationView):

  def __init__(
      self, interaction: discord.Interaction, targetUser: discord.Member, trainer: Trainer, pageLength: int, data: list[Pokemon], title: str, order: str = None):
    self.targetuser = targetUser
    self.trainer = trainer
    self.title = title
    self.order = order
    self.pokemondata = pokemonservice.GetPokemonByIdList([d.Pokemon_Id for d in data])
    super(MyPokemonView, self).__init__(interaction, pageLength, data)

  async def send(self, ephemeral: bool = False):
    await self.interaction.followup.send(view=self, ephemeral=ephemeral)
    self.message = await self.interaction.original_response()
    await self.update_message(self.data[:self.pageLength])

  async def update_message(self, data: list[Pokemon]):
    self.update_buttons()
    embed = discordservice.CreateEmbed(
        self.title,
        self.SingleEmbedDesc(data[0]) if self.pageLength == 1 else self.ListEmbedDesc(data),
        TrainerColor)
    if self.pageLength == 1:
      embed.set_image(url=pokemonservice.GetPokemonImage(data[0],next(p for p in self.pokemondata if p.Id == data[0].Pokemon_Id)))
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

  def SingleEmbedDesc(self, pokemon: Pokemon):
    pkmn = next(p for p in self.pokemondata if p.Id == pokemon.Pokemon_Id)
    pkmnData = t2a(body=[['CurrentExp:', f"{pokemon.CurrentExp}/{pokemonservice.NeededExperience(pokemon.Level, pkmn.Rarity, len(pkmn.EvolvesInto) > 0)}", '|', 'Height:', pokemon.Height],
                            ['Can Evolve:',f"{'Yes' if pokemonservice.CanPokemonEvolve(pkmn, pokemon.Level) else 'No'}", '|','Weight:', pokemon.Weight], 
                            ['Types:', f"{'/'.join(pkmn.Types)}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
                      first_col_heading=False,
                      alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
                      style=PresetStyle.plain,
                      cell_padding=0)
    return f"**__{pokemonservice.GetPokemonDisplayName(pokemon, pkmn)} (Lvl. {pokemon.Level})__**\n```{pkmnData}```"

  def ListEmbedDesc(self, data: list[Pokemon]):
    namingArray = []
    for x in data:
      pkmnData = next(p for p in self.pokemondata if p.Id == x.Pokemon_Id)
      if self.order == 'height':
        detailStr = f'({x.Height}m)'
      elif self.order == 'weight':
        detailStr = f'({x.Weight}kg)'
      elif self.order == 'dex':
        detailStr = f'#{pkmnData.PokedexId}'
      else:
        detailStr = f'(Lvl. {x.Level})'
      namingArray.append(pokemonservice.GetPokemonDisplayName(x, pkmnData) + f' {detailStr}')
    newline = '\n'
    return f"{newline.join(namingArray)}"
