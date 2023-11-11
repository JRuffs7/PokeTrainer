import discord

from typing import List

from services import trainerservice
from models.Pokemon import PokedexEntry
from commands.views.selectors.OwnedSelector import TeamSelector, OwnedSelector


class TeamSelectorView(discord.ui.View):
  
  def __init__(self, interaction: discord.Interaction, currentTeam: List[PokedexEntry], pokeList: List[PokedexEntry]):
    try:
      self.interaction = interaction
      self.pokeList = pokeList
      super().__init__(timeout=300)
      positionOptions = TeamSelector(currentTeam)
      pokemonOptions = OwnedSelector(pokeList, 1)
      self.add_item(positionOptions)
      self.add_item(pokemonOptions)
    except Exception as e:
      print(f"{e}")

  #async def interaction_check(self, interaction: discord.Interaction) -> bool:
  #  return interaction.user.id == self.trainer.UserId

  async def TeamSlotSelection(self, inter: discord.Interaction, choice):
    self.teamslotchoice = choice[0]
    await inter.response.defer()

  async def PokemonSelection(self, inter: discord.Interaction, choice):
    self.pokemonchoice = choice[0]
    await inter.response.defer()


  @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
  async def cancel_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    await self.message.delete()
    await inter.response.send_message(content='Canceled team change.',ephemeral=True)

  @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
  async def submit_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    if self.pokemonchoice and self.teamslotchoice:
      trainerservice.SetTeamSlot(trainerservice.GetTrainer(inter.guild_id, inter.user.id), int(self.teamslotchoice), self.pokemonchoice)
      await self.message.delete()
      await inter.response.send_message(content=f"{next((p.GetNameString() for p in self.pokeList if p.Pokemon.Id.lower() == self.pokemonchoice.lower()), None) or 'Error'} set in Slot {int(self.teamslotchoice) + 1}",ephemeral=True)


  async def send(self):
    await self.interaction.response.send_message(view=self, ephemeral=True)
    self.message = await self.interaction.original_response()
