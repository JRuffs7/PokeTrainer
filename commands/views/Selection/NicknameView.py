import discord
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from middleware.decorators import defer

from models.Pokemon import Pokemon, PokemonData
from services import pokemonservice, trainerservice
from models.Trainer import Trainer


class NicknameView(discord.ui.View):
  
	def __init__(self, interaction: discord.Interaction, trainer: Trainer, pokemon: list[Pokemon]):
		self.interaction = interaction
		self.trainer = trainer
		self.pokemondata = pokemonservice.GetPokemonById(pokemon[0].Pokemon_Id)
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(pokemon, 1, defer=False)
		self.add_item(self.ownlist)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		await self.message.delete()
		self.nameinput = NicknameModal(self.trainer, self.pokemondata, choices[0])
		await inter.response.send_modal(self.nameinput)

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
	@defer
	async def cancel_button(self, inter: discord.Interaction,
												button: discord.ui.Button):
		self.clear_items()
		await self.message.delete()


	async def send(self):
		await self.interaction.followup.send(view=self)
		self.message = await self.interaction.original_response()


class NicknameModal(discord.ui.Modal):

	def __init__(self, trainer: Trainer, data: PokemonData, pokemonId: str):
		self.trainer = trainer
		self.data = data
		self.pokemon = next(p for p in self.trainer.OwnedPokemon if p.Id == pokemonId)
		super().__init__(title='New Nickname')
		self.entered = None
		self.nameInput = discord.ui.TextInput(label='Nickname',placeholder='Nickname',default=self.pokemon.Nickname,max_length=20,required=False)
		self.add_item(self.nameInput)
		
	@defer
	async def on_submit(self, interaction: discord.Interaction):
		oldname = self.pokemon.Nickname if self.pokemon.Nickname else self.data.Name
		self.pokemon.Nickname = self.nameInput.value if self.nameInput.value else None
		trainerservice.UpsertTrainer(self.trainer)
		await interaction.followup.send(content=f'{oldname} now has the nickname {self.pokemon.Nickname if self.pokemon.Nickname else self.data.Name}', ephemeral=True)