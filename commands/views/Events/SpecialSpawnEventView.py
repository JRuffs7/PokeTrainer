from datetime import UTC, datetime
import logging
import discord

from table2ascii import table2ascii as t2a, PresetStyle, Alignment, Merge
from commands.views.Events.EventView import EventView

from globals import EventColor, MasterBallReaction, ShortDateFormat
from middleware.decorators import trainer_check
from models.Pokemon import Pokemon
from models.Server import Server
from services import pokemonservice, serverservice, trainerservice
from services.utility import discordservice

class SpecialSpawnEventView(EventView):

	def __init__(self, server: Server, channel: discord.TextChannel, pokemon: Pokemon):
		self.captureLog = logging.getLogger('capture')
		self.pokemon = pokemon
		self.pkmndata = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
		self.userentries = []
		embed = discordservice.CreateEmbed(
				'Special Spawn Event',
				self.PokemonDesc(),
				EventColor)
		embed.set_image(url=pokemonservice.GetPokemonImage(pokemon, self.pkmndata))
		super().__init__(server, channel, embed)

	@discord.ui.button(label=MasterBallReaction)
	@trainer_check
	async def masterball_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id in self.userentries:
			return await interaction.followup.send(content=f"You already captured this special encounter! Wait for more to show up in the future.", ephemeral=True)
		self.userentries.append(interaction.user.id)
		trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
		if trainer.Pokeballs['4'] <= 0:
			self.userentries.remove(interaction.user.id)
			return await interaction.followup.send(content=f"You do not have any Masterballs. Participate in non-legendary public events to receive one.", ephemeral=True)
		elif trainerservice.TryCapture(MasterBallReaction, trainer, self.pokemon):
			if not self.messagethread or not interaction.guild.get_channel_or_thread(self.messagethread.id):
				self.messagethread = await self.message.create_thread(
					name=f"{self.pkmndata.Name}-{datetime.now(UTC).strftime(ShortDateFormat)}",
					auto_archive_duration=60)
				self.server.CurrentEvent.ThreadId = self.messagethread.id
				serverservice.UpsertServer(self.server)
			await self.messagethread.send(self.CaptureDesc(interaction.user.id))
			self.eventLog.info(f"{self.server.ServerName} - {interaction.user.display_name} participated")
			self.captureLog.info(f'{self.server.ServerName} - {interaction.user.display_name} used Masterball and caught a {self.pkmndata.Name}')
			return await interaction.followup.send(content=f"You captured a {self.pkmndata.Name}!\nYou used 1x Masterball and gained $25.", ephemeral=True)
		else:
			self.userentries.remove(interaction.user.id)
			return await interaction.followup.send(f"Capture failed for some reason. Try again.", ephemeral=True)

	def CaptureDesc(self, userId: int):
		pkmnType = 'starter' if self.pkmndata.IsStarter else 'Legendary' if self.pkmndata.IsLegendary else 'Ultra Beast' if self.pkmndata.IsUltraBeast else 'Paradox' if self.pkmndata.IsParadox else 'Fossil' if self.pkmndata.IsFossil else 'Mythical'
		return f'<@{userId}> used a Masterball and captured the {pkmnType} Pokemon {pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)}!'

	def PokemonDesc(self):
		pkmnData = t2a(
			body=[
				['Height:', f"{self.pokemon.Height}", '|', 'Weight:', self.pokemon.Weight],
				['Types:', f"{self.pkmndata.Types[0]}"f"{'/' + self.pkmndata.Types[1] if len(self.pkmndata.Types) > 1 else ''}", Merge.LEFT, Merge.LEFT, Merge.LEFT]], 
			first_col_heading=False,
			alignments=[Alignment.LEFT,Alignment.LEFT,Alignment.CENTER,Alignment.LEFT,Alignment.LEFT],
			style=PresetStyle.plain,
			cell_padding=0)
		return f"{f'{pokemonservice.GetPokemonDisplayName(self.pokemon, self.pkmndata)} (Lvl. {self.pokemon.Level})'}```{pkmnData}```"
