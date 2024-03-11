from datetime import datetime
import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge
from commands.views.Events.EventView import EventView

from globals import MasterBallReaction, PokemonColor
from middleware.decorators import trainer_check
from models.Pokemon import Pokemon
from services import pokemonservice, trainerservice
from services.utility import discordservice

class LegendaryEventView(EventView):

	def __init__(self, channel: discord.TextChannel, pokemon: Pokemon, title: str):
		self.captureLog = logging.getLogger('capture')
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		self.userentries = []
		embed = discordservice.CreateEmbed(
				title,
				self.PokemonDesc(),
				PokemonColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(pokemon))
		super().__init__(channel, embed)

	@discord.ui.button(label=MasterBallReaction)
	@trainer_check
	async def masterball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id in self.userentries:
			await interaction.response.send_message(content=f"You already captured this special encounter! Wait for more to show up in the future.", ephemeral=True)
		trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
		if trainer.Pokeballs['4'] <= 0:
			await interaction.response.send_message(content=f"You do not have any Masterballs. Participate in non-legendary public events to receive one.", ephemeral=True)
		elif trainerservice.TryCapture(MasterBallReaction, trainer, self.pokemon):
			if not self.messagethread or interaction.guild.get_channel_or_thread(self.messagethread.id):
				self.messagethread = self.message.create_thread(
					name=f'{self.pkmndata.Name} - {datetime.utcnow().strftime('%m/%d/%Y')}',
					auto_archive_duration=60)
			await self.messagethread.send(f'<@{self.interaction.user.id}> used a Masterball and captured the legendary {pokemonservice.GetPokemonDisplayName(self.pokemon)}!')
			self.userentries.append(interaction.user.id)
		else:
			await interaction.response.send_message(f"Capture failed for some reason. Try again.", delete_after=10)

	def PokemonDesc(self):
		pkmnData = t2a(
			body=[
				['Height:', f"{self.pokemon.Height}", '|', 'Weight:', self.pokemon.Weight],
				['Types:', f"{self.pkmndata.Types[0]}"f"{'/' + self.pkmndata.Types[1] if len(self.pkmndata.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"{f'{pokemonservice.GetPokemonDisplayName(self.pokemon)} (Lvl. {self.pokemon.Level})'}```{pkmnData}```"
