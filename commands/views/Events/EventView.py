import asyncio
from datetime import UTC, datetime, timedelta
import logging
import discord

from models.Server import Server
from services import serverservice

class EventView(discord.ui.View):

	def __init__(
			self, server: Server, channel: discord.TextChannel, embed: discord.Embed):
		self.eventLog = logging.getLogger('event')
		self.eventLog.info(f"{server.ServerName} - {server.CurrentEvent.EventName} Begins")
		self.server = server
		self.channel = channel
		self.messagethread = None
		self.embed = embed
		self.embed.set_footer(text=timedelta(minutes=60))
		super().__init__(timeout=3600)

	async def send(self):
		self.message = await self.channel.send(embed=self.embed, view=self, delete_after=3605)
		self.server.CurrentEvent.MessageId = self.message.id
		sentAt = datetime.now(UTC)+timedelta(minutes=1)
		while datetime.now(UTC) < sentAt:
			self.embed.set_footer(text=str(sentAt-datetime.now(UTC)).split('.',2)[0])
			await self.message.edit(embed=self.embed, view=self)
			await asyncio.sleep(0.85)
		self.embed.set_footer(text='Event ended.')
		await self.message.edit(embed=self.embed, view=self)
		self.eventLog.info(f"{self.server.ServerName} - {self.server.CurrentEvent.EventName} Ended")
		serverservice.UpsertServer(self.server)
