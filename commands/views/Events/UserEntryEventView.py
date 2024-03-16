from datetime import datetime
import discord

from commands.views.Events.EventView import EventView

from globals import EventColor, ShortDateFormat
from middleware.decorators import trainer_check
from models.Server import Server
from models.enums import EventType, StatCompare
from services import pokemonservice, trainerservice
from services.utility import discordservice

class UserEntryEventView(EventView):

	def __init__(self, server: Server, channel: discord.TextChannel, botImg: str):
		embed = discordservice.CreateEmbed(
				server.CurrentEvent.EventName,
				'Press the enter button to submit for a chance to win the following:\n1st Place: 1x Masterball\n2nd Place: 5x Ultraballs\n3rd Place: 10x Greatballs\n\nTies will win the same reward, regardless of the number of users!',
				EventColor)
		embed.set_thumbnail(url=botImg)
		super().__init__(server, channel, embed)
		
	@discord.ui.button(label='Drop', style=discord.ButtonStyle.danger)
	@trainer_check
	async def drop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		if str(interaction.user.id) not in self.server.CurrentEvent.EventEntries:
			return 
		self.server.CurrentEvent.EventEntries.pop(str(interaction.user.id))
		await self.SendToThread(interaction, False)
		return await interaction.followup.send(content=f"Successfully dropped out of the contest.", ephemeral=True)

	@discord.ui.button(label='Enter', style=discord.ButtonStyle.success)
	@trainer_check
	async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		if str(interaction.user.id) not in self.server.CurrentEvent.EventEntries:
			entry = trainerservice.EventEntry(trainerservice.GetTrainer(interaction.guild_id, interaction.user.id), self.server.CurrentEvent)
			if self.server.CurrentEvent.EventType == EventType.StatCompare.value:
				heightBased = self.server.CurrentEvent.SubType in [StatCompare.Shortest.value, StatCompare.Tallest.value]
				self.server.CurrentEvent.EventEntries[str(interaction.user.id)] = entry.Height if heightBased else entry.Weight
				await self.SendToThread(interaction, True)
				return await interaction.followup.send(content=f"You have entered the event with {pokemonservice.GetPokemonDisplayName(entry)} with a {f'height of {entry.Height}' if heightBased else f'weight of {entry.Weight}'}.", ephemeral=True)
			else:
				self.server.CurrentEvent.EventEntries[str(interaction.user.id)] = entry
				await self.SendToThread(interaction, True)
				return await interaction.followup.send(content=f"You have entered the event with a count of {entry}.", ephemeral=True)

	async def SendToThread(self, interaction: discord.Interaction, enter: bool):
		if not self.messagethread or not interaction.guild.get_channel_or_thread(self.messagethread.id):
			self.messagethread = await self.message.create_thread(
				name=f"{self.server.CurrentEvent.EventName}-{datetime.utcnow().strftime(ShortDateFormat)}",
				auto_archive_duration=60)
			self.server.CurrentEvent.ThreadId = self.messagethread.id
		await self.messagethread.send(f'<@{interaction.user.id}> has entered the event.' if enter else f'<@{interaction.user.id}> has left the event.')
		self.eventLog.info(f"{self.server.ServerName} - {interaction.user.display_name} {'entered' if enter else 'dropped out'}")