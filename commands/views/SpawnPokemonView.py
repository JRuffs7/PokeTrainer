import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge

from globals import Checkmark, FightReaction, GreatBallReaction, PokeballReaction, PokemonColor, UltraBallReaction
from models.Pokemon import Pokemon
from models.Trainer import Trainer
from services import pokemonservice, trainerservice
from services.utility import discordservice

class SpawnPokemonView(discord.ui.View):

	def __init__(
			self, interaction: discord.Interaction, trainer: Trainer, pokemon: Pokemon):
		self.battleLog = logging.getLogger('battle')	
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		super().__init__(timeout=60)

	async def send(self, ephemeral: bool = False):
		if not self.pokemon:
			await self.interaction.response.send_message("Failed to spawn a Pokemon. Please try again.", ephemeral=True)
		await self.interaction.response.send_message(view=self, ephemeral=ephemeral)
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				self.GetTitle(),
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(self.pokemon))
		await self.message.edit(embed=embed, view=self)

	@discord.ui.button(label=PokeballReaction)
	async def pokeball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Pokeball")

	@discord.ui.button(label=GreatBallReaction)
	async def greatball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Greatball")

	@discord.ui.button(label=UltraBallReaction)
	async def ultraball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await self.TryCapture(interaction, button.label, "Ultraball")

	@discord.ui.button(label=FightReaction, custom_id="fight")
	async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		fight = trainerservice.TryWildFight(self.trainer, self.pokemon)
		if fight is None:
			await self.message.edit(content=f"You do not have any health! Restore with **/usepotion**. You can buy potions from the **/shop**", view=self)
			await interaction.response.defer()
		elif fight > 10 or self.trainer.Health == 0:
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> was defeated by a wild {pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)} and lost {fight}hp.\nNo experience or money gained.')
			self.battleLog.info(f'{self.trainer.UserId} was defeated by a wild {self.pkmndata.Name}.')
		else:
			trainerPoke = next(p for p in self.trainer.OwnedPokemon if p.Id == self.trainer.Team[0])
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> defeated  a wild {pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)}!\n{pokemonservice.GetPokemonDisplayName(trainerPoke)} gained {self.pkmndata.Rarity}xp\nTrainer lost {fight}hp and gained $50.')
			self.battleLog.info(f'{self.trainer.UserId} defeated a wild {self.pkmndata.Name}!')

	async def TryCapture(self, interaction: discord.Interaction, label: str, ball: str):
		pokeballId = '1' if label == PokeballReaction else '2' if label == GreatBallReaction else '3' if label == UltraBallReaction else '4'
		if self.trainer.Pokeballs[str(pokeballId)] <= 0:
			await self.message.edit(content=f"You do not have any {ball}s. Buy some from the **/shop** or try another ball!", view=self)
			await interaction.response.defer()
		elif trainerservice.TryCapture(label, self.trainer, self.pokemon):
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> used a {ball} and captured a {pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})!')
		else:
			await self.message.edit(content=f"Capture failed! Try again", view=self)
			await interaction.response.defer()

	def GetTitle(self):
		return f'{f"{Checkmark} " if self.pkmndata.PokedexId in self.trainer.Pokedex else ""}{pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})'

	def PokemonDesc(self):
		pkmnData = t2a(
			body=[
				['Rarity:', f"{self.pkmndata.Rarity}", '|', 'Height:', self.pokemon.Height],
				['Color:',f"{self.pkmndata.Color}", '|','Weight:', self.pokemon.Weight], 
				['Types:', f"{self.pkmndata.Types[0]}"f"{'/' + self.pkmndata.Types[1] if len(self.pkmndata.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"```{pkmnData}```"
