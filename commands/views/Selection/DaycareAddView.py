from datetime import UTC, datetime
import discord
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import DateFormat
from middleware.decorators import button_check

from models.Pokemon import Pokemon
from services import pokemonservice, trainerservice
from models.Trainer import Trainer


class DaycareAddView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, pokemon: list[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.pokemon = pokemon
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(pokemon, 2 - len(trainer.Daycare))
		self.add_item(self.ownlist)

	@button_check
	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		await inter.response.defer()
		self.pokemonchoices = choices

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await inter.response.defer()
		self.clear_items()
		await self.message.edit(content='Did not add to daycare.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
		await inter.response.defer()
		if not self.pokemonchoices:
			return
		
		pkmnList = [next(p for p in self.trainer.OwnedPokemon if p.Id == c) for c in self.pokemonchoices]
		for p in self.pokemonchoices:
			if len(self.trainer.Daycare) < 2:
				self.trainer.Daycare[p] = datetime.now(UTC).strftime(DateFormat)
		trainerservice.UpsertTrainer(self.trainer)
		self.clear_items()
		await self.message.edit(content=f'Added {" and ".join([pokemonservice.GetPokemonDisplayName(p) for p in pkmnList])} to your daycare.', view=self)


	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()