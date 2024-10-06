import discord
from globals import TrainerColor
from middleware.decorators import defer

from models.Pokemon import PokemonData
from services import commandlockservice, pokemonservice, trainerservice
from models.Trainer import Trainer
from services.utility import discordservice


class ResetTrainerView(discord.ui.View):
  
	def __init__(self, trainer: Trainer, pokemon: PokemonData):
		self.trainer = trainer
		self.pokemon = pokemon
		super().__init__(timeout=300)
		cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.gray)
		cnclbtn.callback = self.cancel_button
		self.add_item(cnclbtn)
		rstbtn = discord.ui.Button(label="Reset", style=discord.ButtonStyle.primary)
		rstbtn.callback = self.reset_button
		self.add_item(rstbtn)

	async def on_timeout(self):
		await self.message.delete(delay=0.1)
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		return await super().on_timeout()

	@defer
	async def cancel_button(self, inter: discord.Interaction):
		await self.on_timeout()

	@defer
	async def reset_button(self, inter: discord.Interaction):
		self.clear_items()
		cnclbtn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.gray)
		cnclbtn.callback = self.cancel_button
		self.add_item(cnclbtn)
		nobtn = discord.ui.Button(label="No", style=discord.ButtonStyle.red)
		nobtn.callback = self.no_button
		self.add_item(nobtn)
		yesbtn = discord.ui.Button(label="Yes", style=discord.ButtonStyle.green)
		yesbtn.callback = self.yes_button
		self.add_item(yesbtn)

		await self.message.edit(embed=discordservice.CreateEmbed(
			'Reset Trainer?', 
			'**Do you wish to keep your Shiny Pokemon?**\n\nChanges:\n- Revert back to their base evolution (if applicable)\n- New IVs\n- Reset to Level 1\n\nRemain:\n- Nickname\n- Gender\n- Height\n- Weight\n- Pokeball',
			TrainerColor), view=self)

	async def no_button(self, inter: discord.Interaction):
		await inter.response.defer(thinking=True)
		await self.resettrainer(inter,False)

	async def yes_button(self, inter: discord.Interaction):
		await inter.response.defer(thinking=True)
		await self.resettrainer(inter,True)

	async def resettrainer(self, inter: discord.Interaction, keepShiny: bool):
		commandlockservice.DeleteLock(self.trainer.ServerId, self.trainer.UserId)
		self.trainer = trainerservice.ResetTrainer(self.trainer, self.pokemon, keepShiny)
		starter = next(p for p in self.trainer.OwnedPokemon if p.Id in self.trainer.Team)
		embed = discordservice.CreateEmbed(
			f"{inter.user.display_name}'s PokeTrainer Journey Begins!",
			f'Starter: {pokemonservice.GetPokemonDisplayName(starter, self.pokemon)}\nStarting Money: ${self.trainer.Money}\nStarting Pokeballs: 5',
			TrainerColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(starter, self.pokemon))
		await inter.followup.send(embed=embed)

	async def send(self, inter: discord.Interaction):
		await inter.followup.send(embed=discordservice.CreateEmbed(
			'Reset Trainer?', 
			'Are you sure you wish to reset your trainer data? This will remove all your progress and start you back at the beginning.',
			TrainerColor), view=self)
		self.message = await inter.original_response()
