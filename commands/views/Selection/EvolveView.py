import discord
from middleware.decorators import button_check

from services import trainerservice, pokemonservice
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from commands.views.Selection.selectors.EvolveSelector import EvolveSelector


class EvolveView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, evolveMon: list[Pokemon]):
		self.interaction = interaction
		self.user = interaction.user
		self.trainer = trainer
		self.evolveMon = evolveMon
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(evolveMon, 1)
		self.add_item(self.ownlist)

	@button_check
	async def EvolveSelection(self, inter: discord.Interaction, choice: str):
		await inter.response.defer()
		self.evolvechoice = choice

	@button_check
	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		await inter.response.defer()
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.pokemonchoice = next(p for p in self.trainer.OwnedPokemon if p.Id == choice[0])
		pkmnChoiceData = pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon_Id)
		self.evolvechoice = None
		self.ownlist = OwnedSelector(self.evolveMon, 1, choice[0])
		self.evlist = EvolveSelector([pokemonservice.GetPokemonById(p) for p in pkmnChoiceData.EvolvesInto])
		self.add_item(self.ownlist)
		self.add_item(self.evlist)
		await self.message.edit(view=self)


	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@button_check
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		self.clear_items()
		await self.message.edit(content='Canceled evolution.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@button_check
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		await inter.response.defer()
		if self.pokemonchoice and self.evolvechoice and self.evolvechoice != '0':
			evolvedPokemon = trainerservice.Evolve(self.trainer, self.pokemonchoice, int(self.evolvechoice))
			self.clear_items()
			await self.message.edit(content=f"**{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, False)}** evolved into **{pokemonservice.GetPokemonDisplayName(evolvedPokemon, False)}**", view=self)


	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
