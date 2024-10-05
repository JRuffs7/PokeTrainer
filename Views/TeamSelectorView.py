import discord

from Views.Selectors import PokemonSelector, TeamSelector
from middleware.decorators import defer
from models.Trainer import Trainer

from services import commandlockservice, pokemonservice, trainerservice


class TeamSelectorView(discord.ui.View):
  
  def __init__(self, trainer: Trainer, pokemonId: int|None = None):
    self.trainer = trainer
    self.adding = pokemonId is not None
    self.pokemonchoice = None
    self.teamslotchoice = None
    self.currentteam = trainerservice.GetTeam(trainer)
    self.modifypokemonlist = [x for x in trainer.OwnedPokemon if x.Id not in trainer.Team and x.Pokemon_Id == pokemonId] if pokemonId else self.currentteam
    if pokemonId:
      self.modifypokemonlist.sort(key=lambda x: -x.IsShiny)
    super().__init__(timeout=300)
    self.ownedselectview = PokemonSelector(self.modifypokemonlist, descType=3)
    self.teamslotview = TeamSelector(self.currentteam, pokemonId is not None)
    self.add_item(self.ownedselectview)
    self.add_item(self.teamslotview)

  async def on_timeout(self):
    await self.message.delete()
    commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
    return await super().on_timeout()

  async def PokemonSelection(self, inter: discord.Interaction, choice: str):
    self.pokemonchoice = choice[0]

  async def TeamSlotSelection(self, inter: discord.Interaction, choice: str):
    self.teamslotchoice = int(choice)

  @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
  @defer
  async def cancel_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    self.clear_items()
    commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
    await self.message.edit(content='Canceled team editing.', view=self)

  @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
  @defer
  async def submit_button(self, inter: discord.Interaction,
                        button: discord.ui.Button):
    if not self.pokemonchoice or self.teamslotchoice is None:
      return

    pkmn = next(p for p in self.trainer.OwnedPokemon if p.Id == self.pokemonchoice)
    #removing team member
    if self.teamslotchoice == -1:
      self.trainer.Team = [p for p in self.trainer.Team if p != self.pokemonchoice]
      trainerservice.UpsertTrainer(self.trainer)
      await self.message.edit(content=f"{pokemonservice.GetPokemonDisplayName(pkmn)} has been removed from your team.", embed=None, view=None)
    #swapping/adding
    else:
      if self.adding and self.teamslotchoice == len(self.trainer.Team):
        message = f"{pokemonservice.GetPokemonDisplayName(pkmn)} was added to the team!"
      else:
        message = f"{pokemonservice.GetPokemonDisplayName(pkmn)} was swapped into slot {int(self.teamslotchoice) + 1}"
      trainerservice.SetTeamSlot(self.trainer, self.teamslotchoice, self.pokemonchoice)
      await self.message.edit(content=message, embed=None, view=None)
    commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)

  async def send(self, inter: discord.Interaction):
    await inter.followup.send(view=self)
    self.message = await inter.original_response()
