from discord.ext import commands

from middleware.permissionchecks import is_bot_admin
from services import serverservice
from services.utility import discordservice

class AdminCommands(commands.Cog, name="AdminCommands"):

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="liveupdate")
	@is_bot_admin()
	async def liveupdate(self, ctx: commands.Context, message: str):
		if not message or not ctx.guild:
			return
		print(ctx.guild.id)
		servers = [s for s in serverservice.GetServers() if s.ServerId != ctx.guild.id]
		for serv in servers:
			print(serv.ServerId)
			await discordservice.SendMessageNoInteraction(serv.ServerId, serv.ChannelIds[0], message)


async def setup(bot: commands.Bot):
  await bot.add_cog(AdminCommands(bot))
