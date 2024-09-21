import discord
from commands.views.Selection.selectors.OwnedSelector import OwnedSelector
from globals import SuccessColor
from middleware.decorators import defer

from models.Pokemon import Pokemon, PokemonData
from services import commandlockservice, pokemonservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class NicknameView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemon: list[Pokemon]):
		self.trainer = trainer
		self.pokemon = pokemon
		self.pokemondata = pokemonservice.GetPokemonById(pokemon[0].Pokemon_Id)
		super().__init__(timeout=300)
		self.ownlist = OwnedSelector(pokemon, 1, defer=False)
		cancelbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)
		cancelbtn.callback = self.cancel_button
		self.add_item(self.ownlist)
		self.add_item(cancelbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	async def PokemonSelection(self, inter: discord.Interaction, choices: list[str]):
		for item in self.children:
				if type(item) is not discord.ui.Button:
					self.remove_item(item)
		self.ownlist = OwnedSelector(self.pokemon, 1, defer=False)
		self.add_item(self.ownlist)
		await self.message.edit(view=self)
		self.nameinput = NicknameModal(self.trainer, self.pokemondata, self.message, choices[0])
		await inter.response.send_modal(self.nameinput)

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()


	async def send(self, inter: discord.Interaction):
		await inter.followup.send(view=self)
		self.message = await inter.original_response()


class NicknameModal(discord.ui.Modal):

	def __init__(self, trainer: Trainer, data: PokemonData, message: discord.InteractionMessage, pokemonId: str):
		self.trainer = trainer
		self.data = data
		self.message = message
		self.pokemon = next(p for p in self.trainer.OwnedPokemon if p.Id == pokemonId)
		super().__init__(title='New Nickname')
		self.entered = None
		self.nameInput = discord.ui.TextInput(label='Nickname',placeholder='Nickname',default=self.pokemon.Nickname,max_length=20,required=False)
		self.add_item(self.nameInput)
		
	@defer
	async def on_submit(self, inter: discord.Interaction):
		await self.message.delete(delay=0.1)
		oldname = self.pokemon.Nickname if self.pokemon.Nickname else self.data.Name
		self.pokemon.Nickname = self.nameInput.value if self.nameInput.value else None
		trainerservice.UpsertTrainer(self.trainer)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		await inter.followup.send(embed=discordservice.CreateEmbed(
			'Nickname Set', 
			f'<@{inter.user.id}> changed {oldname} to now have the {f"nickname **{self.pokemon.Nickname}**" if self.pokemon.Nickname else f"name **{self.data.Name}**"}.',
			SuccessColor))