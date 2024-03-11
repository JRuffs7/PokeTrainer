import logging
import discord

class EventView(discord.ui.View):

	def __init__(
			self, channel: discord.TextChannel, embed: discord.Embed):
		self.captureLog = logging.getLogger('capture')
		self.channel = channel
		self.messagethread = None
		self.embed = embed
		super().__init__(timeout=3600)

	async def send(self):
		self.message = await self.channel.send(embed=self.embed, view=self, delete_after=3600)
