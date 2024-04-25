import discord
from middleware.decorators import defer

from services import itemservice, trainerservice, pokemonservice
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

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def EvolveSelection(self, inter: discord.Interaction, choice: str):
		self.evolvechoice = pokemonservice.GetPokemonById(int(choice))

	async def PokemonSelection(self, inter: discord.Interaction, choice: list[str]):
		for item in self.children:
			if type(item) is not discord.ui.Button:
				self.remove_item(item)

		self.pokemonchoice = next(p for p in self.trainer.OwnedPokemon if p.Id == choice[0])
		self.pkmnChoiceData = pokemonservice.GetPokemonById(self.pokemonchoice.Pokemon_Id)
		self.evolvechoice = None
		self.ownlist = OwnedSelector(self.evolveMon, 1, choice[0])
		self.evlist = EvolveSelector(pokemonservice.GetPokemonByIdList(pokemonservice.AvailableEvolutions(self.pokemonchoice, self.pkmnChoiceData, [itemservice.GetItem(int(i)) for i in self.trainer.EvolutionItems if self.trainer.EvolutionItems[i] > 0])))
		self.add_item(self.ownlist)
		self.add_item(self.evlist)
		await self.message.edit(view=self)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.edit(content='Canceled evolution.', view=self)

	@discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
	@defer
	async def submit_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		if self.pokemonchoice and self.evolvechoice:
			evolvedPokemon = trainerservice.Evolve(self.trainer, self.pokemonchoice, self.evolvechoice)
			self.clear_items()
			await self.message.edit(content=f"**{pokemonservice.GetPokemonDisplayName(self.pokemonchoice, self.pkmnChoiceData)}** evolved into **{pokemonservice.GetPokemonDisplayName(evolvedPokemon, self.evolvechoice)}**", view=self)

	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()
