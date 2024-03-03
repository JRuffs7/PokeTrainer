import logging
from discord import Member
from discord.ext import commands
from middleware.decorators import method_logger, is_bot_admin
from services import pokemonservice, serverservice, trainerservice
from services.utility import discordservice

class AdminCommands(commands.Cog, name="AdminCommands"):

	logger = logging.getLogger('discord')

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name="sync")
	@method_logger
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

	@commands.command(name="liveupdate")
	@method_logger
	@is_bot_admin
	async def liveupdate(self, ctx: commands.Context, message: str):
		if not message or not ctx.guild:
			return
		print(ctx.guild.id)
		servers = [s for s in serverservice.GetServers() if s.ServerId != ctx.guild.id]
		for serv in servers:
			print(serv.ServerId)
			await discordservice.SendMessageNoInteraction(serv.ServerId, serv.ChannelIds[0], message)

	@commands.command(name="deleteuser")
	@is_bot_admin
	async def deleteuser(self, ctx: commands.Context, user: Member = None):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.DeleteTrainer(trainer)
		

	@commands.command(name="addhealth")
	@method_logger
	@is_bot_admin
	async def addhealth(self, ctx: commands.Context, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainer.Health += amount
			trainer.Health = 100 if trainer.Health > 100 else 0 if trainer.Health < 0 else trainer.Health
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="givemoney")
	@method_logger
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
	@method_logger
	@is_bot_admin
	async def addball(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer.PokeballList, type if type == 1 or type == 2 or type == 3 else 1, amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addpotion")
	@method_logger
	@is_bot_admin
	async def addpotion(self, ctx: commands.Context, type: int, amount: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer.PotionList, type if type == 1 or type == 2 or type == 3 else 1, amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addbadge")
	@method_logger
	@is_bot_admin
	async def addbadge(self, ctx: commands.Context, badge: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer and badge not in trainer.Badges:
			trainer.Badges.append(badge)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addpokemon")
	@method_logger
	@is_bot_admin
	async def addpokemon(self, ctx: commands.Context, pokemonId: int, user: Member = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if trainer and pokemon:
			newPkmn = pokemonservice.GenerateSpawnPokemon(pokemon, 1)
			newPkmn.Level = 1
			trainer.OwnedPokemon.append(newPkmn)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="testpokemon")
	@method_logger
	@is_bot_admin
	async def testpokemon(self, ctx: commands.Context, pokemonId: int):
		if not ctx.guild:
			return
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if pokemon:
			print(f"{pokemon.Name}: {pokemon.PokedexId}")



async def setup(bot: commands.Bot):
  await bot.add_cog(AdminCommands(bot))
