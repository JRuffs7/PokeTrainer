import logging
import discord

class EventView(discord.ui.View):

	def __init__(
			self, channel: discord.TextChannel, embed: discord.Embed):
		self.captureLog = logging.getLogger('capture')
		self.channel = channel
		self.embed = embed
		super().__init__(timeout=60)

	async def send(self):
		self.message = await self.channel.send(embed=self.embed, view=self)
