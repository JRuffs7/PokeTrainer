from discord import Member
from discord.ext import commands

from middleware.permissionchecks import is_bot_admin
from services import serverservice, trainerservice
from services.utility import discordservice

class AdminCommands(commands.Cog, name="AdminCommands"):

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="sync")
	@is_bot_admin()
	async def sync(self, ctx: commands.Context):
		print("Syncing bot commands")
		await ctx.bot.tree.sync()
		print("Synced bot commands")

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

	@commands.command(name="deleteuser")
	@is_bot_admin()
	async def deleteuser(self, ctx: commands.Context, user: Member):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id)
		if trainer:
			trainerservice.DeleteTrainer(trainer)

	@commands.command(name="addhealth")
	@is_bot_admin()
	async def addhealth(self, ctx: commands.Context, user: Member, amount: int):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id)
		if trainer:
			trainer.Health += amount
			trainer.Health = 100 if trainer.Health > 100 else 0 if trainer.Health < 0 else trainer.Health
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="givemoney")
	@is_bot_admin()
	async def givemoney(self, ctx: commands.Context, user: Member, amount: int):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id)
		if trainer:
			trainer.Money += amount
			trainer.Money = 0 if trainer.Money < 0 else trainer.Money
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addpokeball")
	@is_bot_admin()
	async def addpokeball(self, ctx: commands.Context, user: Member, type: int, amount: int):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		if trainer:
			trainer.PokeballList = trainerservice.ModifyItemList(
					trainer.PokeballList, type if type == 1 or type == 2 or type == 3 else 1, amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addpotion")
	@is_bot_admin()
	async def addpotion(self, ctx: commands.Context, user: Member, type: int, amount: int):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		if trainer:
			trainer.PotionList = trainerservice.ModifyItemList(
					trainer.PotionList, type if type == 1 or type == 2 or type == 3 else 1, amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addbadge")
	@is_bot_admin()
	async def addbadge(self, ctx: commands.Context, user: Member, badge: int):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		if trainer and badge not in trainer.Badges:
			trainer.Badges.append(badge)
			trainerservice.UpsertTrainer(trainer)




async def setup(bot: commands.Bot):
  await bot.add_cog(AdminCommands(bot))
