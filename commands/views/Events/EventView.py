import asyncio
import calendar
import os
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
		self.eventTime = int(os.environ['EVENT_TIME'])
		super().__init__(timeout=self.eventTime*60)

	async def endevent(self):
		try:
			self.embed.title = self.server.CurrentEvent.EventName
			self.embed.set_footer(text='Event has ended.')
			await self.message.edit(embed=self.embed, view=self)
			await serverservice.EndEvent(self.server)
			await self.message.delete()
			self.eventLog.info(f"{self.server.ServerName} - Event Ended")
		except Exception as e:
			self.eventLog.error(f"SERVER {self.server.ServerName}: {e}")

	async def send(self):
		timestamp = calendar.timegm((datetime.now(UTC)+timedelta(minutes=self.eventTime)).timetuple())
		self.embed.title += f' (Ends <t:{timestamp}:R>)'
		self.message = await self.channel.send(embed=self.embed, view=self)
		await asyncio.sleep(self.eventTime*60)
		await self.endevent()
