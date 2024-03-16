from datetime import datetime
import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge
from commands.views.Events.EventView import EventView

from globals import EventColor, MasterBallReaction
from middleware.decorators import trainer_check
from models.Pokemon import Pokemon
from models.Server import Server
from services import pokemonservice, serverservice, trainerservice
from services.utility import discordservice

class SpecialSpawnEventView(EventView):

	def __init__(self, server: Server, channel: discord.TextChannel, pokemon: Pokemon, title: str):
		self.captureLog = logging.getLogger('capture')
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		self.userentries = []
		embed = discordservice.CreateEmbed(
				title,
				self.PokemonDesc(),
				EventColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(pokemon))
		super().__init__(server, channel, embed)

	@discord.ui.button(label=MasterBallReaction)
	@trainer_check
	async def masterball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		if interaction.user.id in self.userentries:
			return await interaction.followup.send(content=f"You already captured this special encounter! Wait for more to show up in the future.", ephemeral=True)
		trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
		if trainer.Pokeballs['4'] <= 0:
			return await interaction.followup.send(content=f"You do not have any Masterballs. Participate in non-legendary public events to receive one.", ephemeral=True)
		elif trainerservice.TryCapture(MasterBallReaction, trainer, self.pokemon):
			if not self.messagethread or not interaction.guild.get_channel_or_thread(self.messagethread.id):
				self.messagethread = await self.message.create_thread(
					name=f"{self.pkmndata.Name}-{datetime.utcnow().strftime('%m/%d/%Y')}",
					auto_archive_duration=60)
				self.server.CurrentEvent.ThreadId = self.messagethread.id
				serverservice.UpsertServer(self.server)
			await self.messagethread.send(self.CaptureDesc(interaction.user.id))
			self.userentries.append(interaction.user.id)
			self.eventLog.info(f"{self.server.ServerName} - {interaction.user.display_name} participated")
			self.captureLog.info(f'{self.server.ServerName} - {interaction.user.display_name} used Masterball and caught a {self.pkmndata.Name}')
			return
		else:
			return await interaction.followup.send(f"Capture failed for some reason. Try again.", delete_after=10)

	def CaptureDesc(self, userId: int):
		pkmnType = 'starter' if self.pkmndata.IsStarter else 'Legendary' if self.pkmndata.IsLegendary else 'Ultra Beast' if self.pkmndata.IsUltraBeast else 'Paradox' if self.pkmndata.IsParadox else 'fossil' if self.pkmndata.IsFossil else 'Mythical'
		return f'<@{userId}> used a Masterball and captured the {pkmnType} Pokemon {pokemonservice.GetPokemonDisplayName(self.pokemon)}!'

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
