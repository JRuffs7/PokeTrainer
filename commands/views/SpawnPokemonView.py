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
		self.captureLog = logging.getLogger('capture')	
		self.interaction = interaction
		self.trainer = trainer
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		super().__init__(timeout=60)

	async def send(self):
		if not self.pokemon:
			return await self.interaction.response.send_message("Failed to spawn a Pokemon. Please try again.", ephemeral=True)
		embed = discordservice.CreateEmbed(
				self.GetTitle(),
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(self.pokemon))
		trainerPkmn = next(p for p in self.trainer.OwnedPokemon if p.Id == self.trainer.Team[0])
		await self.interaction.response.send_message(content=f'{pokemonservice.GetPokemonDisplayName(trainerPkmn)} would be used to fight unless changed.', embed=embed, view=self, ephemeral=True)
		self.message = await self.interaction.original_response()

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
		updatedTrainer = trainerservice.GetTrainer(self.interaction.guild_id, self.interaction.user.id)
		trainerPkmn = next(p for p in updatedTrainer.OwnedPokemon if p.Id == updatedTrainer.Team[0])
		fight = trainerservice.TryWildFight(updatedTrainer, self.pokemon)
		if fight is None:
			await self.message.edit(content=f"You do not have any health! Restore with **/usepotion**. You can buy potions from the **/shop**", view=self)
			await interaction.response.defer()
		elif fight >= 10 or updatedTrainer.Health == 0:
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> and {pokemonservice.GetPokemonDisplayName(trainerPkmn)} were defeated by a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)} (Lvl. {self.pokemon.Level})** and lost {fight}hp.\nNo experience or money gained.')
			self.battleLog.info(f'{interaction.user.display_name} was defeated by a wild {self.pkmndata.Name}')
		else:
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> defeated a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon, False, False)} (Lvl. {self.pokemon.Level})**!\n{pokemonservice.GetPokemonDisplayName(trainerPkmn)} gained {self.pkmndata.Rarity*self.pokemon.Level*2 if self.pkmndata.Rarity <= 2 else self.pkmndata.Rarity*self.pokemon.Level}xp\nTrainer lost {fight}hp and gained $50.')
			self.battleLog.info(f'{interaction.user.display_name} defeated a wild {self.pkmndata.Name}')

	async def TryCapture(self, interaction: discord.Interaction, label: str, ball: str):
		updatedTrainer = trainerservice.GetTrainer(self.interaction.guild_id, self.interaction.user.id)
		trainerPkmn = next(p for p in updatedTrainer.OwnedPokemon if p.Id == updatedTrainer.Team[0])
		pokeballId = '1' if label == PokeballReaction else '2' if label == GreatBallReaction else '3' if label == UltraBallReaction else '4'
		if updatedTrainer.Pokeballs[str(pokeballId)] <= 0:
			await self.message.edit(content=f"You do not have any {ball}s. Buy some from the **/shop**, try another ball, or fight!\n{pokemonservice.GetPokemonDisplayName(trainerPkmn)} would be used to fight unless changed.", view=self)
			await interaction.response.defer()
		elif trainerservice.TryCapture(label, updatedTrainer, self.pokemon):
			self.captureLog.info(f'{interaction.guild.name} - {self.interaction.user.display_name} used {ball} and caught a {self.pkmndata.Name}')
			await self.message.delete()
			await interaction.response.send_message(content=f'<@{self.interaction.user.id}> used a {ball} and captured a wild **{pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})**!\nAlso gained $25')
		else:
			await self.message.edit(content=f"Capture failed! Try again or fight.\n{pokemonservice.GetPokemonDisplayName(trainerPkmn)} would be used to fight unless changed.", view=self)
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
