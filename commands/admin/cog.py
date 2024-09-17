import asyncio
import logging
from random import choice, sample
from discord import Interaction, Member, TextChannel, app_commands
from discord.ext import commands
from Views.Battles.CpuBattleView import CpuBattleView
from globals import SuperShinyOdds
from middleware.decorators import is_bot_admin, trainer_check
from models.Gym import GymLeader
from models.Server import Server
from services import itemservice, pokemonservice, serverservice, trainerservice

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
			trainer.OwnedPokemon.append(newPkmn)
			trainerservice.UpsertTrainer(trainer)

	@app_commands.command(name="testfight",
                        description="Battle each gym leader from every region.")
	@trainer_check
	async def testfight(self, inter: Interaction, wild: bool):
		trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
		allPkmn = pokemonservice.GetAllPokemon()
		trainer.OwnedPokemon.clear()
		trainer.OwnedPokemon = [pokemonservice.GenerateSpawnPokemon(p, level=choice(range(1,101))) for p in sample(allPkmn, 6)]
		trainer.Team = [p.Id for p in trainer.OwnedPokemon]
		if wild:
			enemyPkmn = choice(allPkmn)
			team = [pokemonservice.GenerateSpawnPokemon(enemyPkmn, 2, level=choice(range(1,101)))]
			name = pokemonservice.GetPokemonDisplayName(team[0], enemyPkmn)
		else:
			team =  [pokemonservice.GenerateSpawnPokemon(p, 2, level=choice(range(1,101))) for p in sample(allPkmn, 6)]
			name = 'GymTest'
		leader = GymLeader({
			'Id': 1,
			'Name': name,
			'Sprite': '',
			'Team': team,
			'Reward': (0,0) if wild else (0,2000),
			'Generation': 1,
			'MainType': '' if wild else 'Rock',
			'BadgeId': 0 if wild else 1
		})
		await CpuBattleView(
			trainer, 
			leader,
			wild,
			choice([1,2]) == 1).send(inter)

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
