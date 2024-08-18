import asyncio
import logging
from discord import Member, TextChannel
from discord.ext import commands
from globals import SuperShinyOdds
from middleware.decorators import is_bot_admin
from models.Server import Server
from services import battleservice, itemservice, pokemonservice, serverservice, trainerservice

class AdminCommands(commands.Cog, name="AdminCommands"):

	logger = logging.getLogger('command')
	err = logging.getLogger('error')

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	#region Test Commands

	@commands.command(name="deleteuser")
	@is_bot_admin
	async def deleteuser(self, ctx: commands.Context, user: Member = None):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.DeleteTrainer(trainer)
		

	@commands.command(name="addhealth")
	@is_bot_admin
	async def addhealth(self, ctx: commands.Context, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainer.Health += amount
			trainer.Health = 100 if trainer.Health > 100 else 0 if trainer.Health < 0 else trainer.Health
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addmoney")
	@is_bot_admin
	async def givemoney(self, ctx: commands.Context, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainer.Money += amount
			trainer.Money = 0 if trainer.Money < 0 else trainer.Money
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addball")
	@is_bot_admin
	async def addball(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer, str(type) if type in [i.Id for i in itemservice.GetAllPokeballs()] else '4', amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addpotion")
	@is_bot_admin
	async def addpotion(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer, str(type) if type in [i.Id for i in itemservice.GetAllPotions()] else '17', amount)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addcandy")
	@is_bot_admin
	async def addcandy(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer, str(type) if type in [i.Id for i in itemservice.GetAllCandies()] else '50', amount)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="additem")
	@is_bot_admin
	async def additem(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer.EvolutionItems, str(type) if type >= 80 else '84', amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addbadge")
	@is_bot_admin
	async def addbadge(self, ctx: commands.Context, badge: int = None, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		badge = badge if badge else len(trainer.Badges) + 1
		if trainer and badge not in trainer.Badges:
			trainer.Badges.append(badge)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addpokemon")
	@is_bot_admin
	async def addpokemon(self, ctx: commands.Context, pokemonId: int, level: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if trainer and pokemon:
			newPkmn = pokemonservice.GenerateSpawnPokemon(pokemon, SuperShinyOdds, level)
			newPkmn.Level = 1
			trainer.OwnedPokemon.append(newPkmn)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="testpokemon")
	@is_bot_admin
	async def testpokemon(self, ctx: commands.Context, pokemonId: int):
		if not ctx.guild:
			return
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if pokemon:
			print(f"{pokemon.__dict__}")

	@commands.command(name="testfight")
	@is_bot_admin
	async def testfight(self, ctx: commands.Context, pokemon1: int, pokemon2: int = None, pokemon3: int = None, pokemon4: int = None, pokemon5: int = None, pokemon6: int = None):
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		
		enemyTeam = pokemonservice.GetPokemonByIdList([p for p in [pokemon1, pokemon2, pokemon3, pokemon4, pokemon5, pokemon6] if p])


	#endregion

	#region Real Commands

	@commands.command(name="globalmessage")
	@is_bot_admin
	async def globalmessage(self, ctx: commands.Context, message: str):
		self.logger.info(f'GLOBAL MESSAGE SENT')
		if not ctx.guild:
			return
		allServers = serverservice.GetAllServers()
		for server in allServers:
			asyncio.run_coroutine_threadsafe(self.MessageThread(message, server), self.bot.loop)

	async def MessageThread(self, message: str, server: Server):
		guild = self.bot.get_guild(server.ServerId)
		if not guild:
			return 
		channel = guild.get_channel(server.ChannelId)
		if not channel or not isinstance(channel, TextChannel):
			return
		
		return await channel.send(message)
		
	@commands.command(name="sync")
	@is_bot_admin
	async def sync(self, ctx: commands.Context, serverOnly: int | None):
		try:
			if serverOnly:
				self.logger.info(f'Local Sync Command called by {ctx.author.display_name} in server {ctx.guild.name}')
				await ctx.bot.tree.sync(guild=ctx.guild)
			else:
				self.logger.info(f'Global Sync Command called by {ctx.author.display_name} in server {ctx.guild.name}')
				await ctx.bot.tree.sync()
			self.logger.info(f'Syncing complete.')
		except Exception as e:
			self.logger.critical(f"{e}")

	#endregion
	
async def setup(bot: commands.Bot):
  await bot.add_cog(AdminCommands(bot))
