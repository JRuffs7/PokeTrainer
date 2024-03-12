import discord

from commands.views.Selection.selectors.TeamSelectors import TeamChoice
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from middleware.decorators import button_check
from models.Trainer import Trainer

from services import pokemonservice, trainerservice


class TeamSelectorView(discord.ui.View):
  
  def __init__(self, interaction: discord.Interaction, trainer: Trainer, idFilter: int | None = None):
    self.interaction = interaction
    self.user = interaction.user
    self.trainer = trainer
    self.adding = idFilter is not None
    self.pokemonchoice = None
    self.teamslotchoice = None
    
    self.currentteam = [next(p for p in trainer.OwnedPokemon if p.Id == t) for t in trainer.Team]
    self.modifypokemonlist = [
      x for x in trainer.OwnedPokemon if 
      x.Id not in trainer.Team and 
      x.Pokemon_Id == idFilter
    ] if idFilter else self.currentteam
    if idFilter:
      self.modifypokemonlist.sort(key=lambda x: (x.Pokemon_Id, -x.IsShiny))

    super().__init__(timeout=300)
    self.ownedselectview = OwnedSelector(self.modifypokemonlist, 1)
    self.teamslotview = TeamChoice(self.currentteam, idFilter is not None)
    self.add_item(self.ownedselectview)
    self.add_item(self.teamslotview)

  @button_check
  async def PokemonSelection(self, inter: discord.Interaction, choice: str):
    self.pokemonchoice = choice[0]
    await inter.response.defer()

  @button_check
  async def TeamSlotSelection(self, inter: discord.Interaction, choice: str):
    self.teamslotchoice = int(choice)
    await inter.response.defer()


  @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
  async def cancel_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    self.clear_items()
    await self.message.edit(content='Canceled team editing.', view=self)

  @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
  async def submit_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    if not self.pokemonchoice or self.teamslotchoice is None:
      return await inter.response.defer()

    self.clear_items()
    pkmn = next(p for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)
    #removing team member
    if self.teamslotchoice == -1:
      self.trainer.Team = [p for p in self.trainer.Team if p != self.pokemonchoice]
      trainerservice.UpsertTrainer(self.trainer)
      await self.message.edit(content=f"{pokemonservice.GetPokemonDisplayName(pkmn)} has been removed from your team.", view=self)
    #swapping/adding
    else:
      if self.adding and self.teamslotchoice == len(self.trainer.Team):
        message = f"{next(pokemonservice.GetPokemonDisplayName(p) for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)} was added to the team!"
      else:
        message = f"{next(pokemonservice.GetPokemonDisplayName(p) for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)} was swapped into slot {int(self.teamslotchoice) + 1}"
      trainerservice.SetTeamSlot(self.trainer, self.teamslotchoice, self.pokemonchoice)
      await self.message.edit(content=message, view=self)
    await inter.response.defer()


  async def send(self):
    await self.interaction.response.send_message(view=self, ephemeral=True)
    self.message = await self.interaction.original_response()
