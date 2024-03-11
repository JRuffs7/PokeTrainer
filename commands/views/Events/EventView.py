import logging
import discord

from models.Server import Server
from services import serverservice

class EventView(discord.ui.View):

	def __init__(
			self, server: Server, channel: discord.TextChannel, embed: discord.Embed):
		self.captureLog = logging.getLogger('capture')
		self.server = server
		self.channel = channel
		self.messagethread = None
		self.embed = embed
		super().__init__(timeout=3600)

	async def send(self):
		self.message = await self.channel.send(embed=self.embed, view=self, delete_after=3600)
		self.server.CurrentEvent.MessageId = self.message.id
		serverservice.UpsertServer(self.server)
