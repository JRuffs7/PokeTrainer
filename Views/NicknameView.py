import discord
from Views.Selectors import PokemonSelector
from globals import ErrorColor, SuccessColor
from middleware.decorators import defer

from models.Pokemon import Pokemon
from services import pokemonservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class NicknameView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemonList: list[Pokemon]):
		self.trainer = trainer
		self.pokemonlist = pokemonList
		super().__init__(timeout=300)
		self.pkmnlist = PokemonSelector(pokemonList, defer=False)
		cancelbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)
		cancelbtn.callback = self.cancel_button
		self.add_item(self.pkmnlist)
		self.add_item(cancelbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choice: str):
		for item in self.children:
				if type(item) is not discord.ui.Button:
					self.remove_item(item)
		self.pkmnlist = PokemonSelector(self.pokemonlist, defer=False)
		self.add_item(self.pkmnlist)
		await self.message.edit(view=self)
		self.nameinput = NicknameModal(self.trainer, self.message, choice, next(p for p in self.trainer.OwnedPokemon if p.Id == choice).Nickname)
		await inter.response.send_modal(self.nameinput)

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()


	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()


class NicknameModal(discord.ui.Modal):

	def __init__(self, trainer: Trainer, message: discord.InteractionMessage, pokemonId: str, currentName: str|None):
		self.trainer = trainer
		self.message = message
		self.pokemonId = pokemonId
		super().__init__(timeout=60, title='New Nickname (20 characters max)')
		self.nameInput = discord.ui.TextInput(label='Nickname',placeholder='Nickname',default=currentName,max_length=20,required=False)
		self.add_item(self.nameInput)
	
	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		return await super().on_timeout()
		
	@defer
	async def on_submit(self, inter: discord.Interaction):
		await self.message.delete(delay=0.1)
		self.trainer = trainerservice.GetTrainer(self.trainer.ServerId, self.trainer.UserId)
		pokemon = next((p for p in self.trainer.OwnedPokemon if p.Id == self.pokemonId), None)
		if not pokemon:
			await inter.followup.send(embed=discordservice.CreateEmbed(
			'Failed To Set Nickname', 
			f'There was an issue trying to find the selected Pokemon. Try again.',
			ErrorColor))
		data = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		oldname = pokemon.Nickname if pokemon.Nickname else data.Name
		pokemon.Nickname = self.nameInput.value if self.nameInput.value else None
		trainerservice.UpsertTrainer(self.trainer)
		await inter.followup.send(embed=discordservice.CreateEmbed(
			'Nickname Set', 
			f'<@{inter.user.id}> changed {oldname} to now have the {f"nickname **{pokemon.Nickname}**" if pokemon.Nickname else f"name **{data.Name}**"}.',
			SuccessColor))