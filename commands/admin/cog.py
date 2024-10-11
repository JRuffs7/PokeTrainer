import asyncio
from datetime import UTC, datetime
import logging
import math
from random import choice
import uuid
from discord import Member, TextChannel
from discord.ext import commands
from globals import DateFormat, SuperShinyOdds
from middleware.decorators import is_bot_admin
from models.Egg import TrainerEgg
from models.Server import Server
from services import commandlockservice, gymservice, moveservice, pokemonservice, serverservice, trainerservice

class AdminCommands(commands.Cog, name="AdminCommands"):

	logger = logging.getLogger('command')
	err = logging.getLogger('error')

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	#region Test Commands

	@commands.command(name="deleteuser")
	@is_bot_admin
	async def deleteuser(self, ctx: commands.Context, user: Member|None = None):
		if not user or not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.DeleteTrainer(trainer)
		
	@commands.command(name="addmoney")
	@is_bot_admin
	async def givemoney(self, ctx: commands.Context, amount: int, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainer.Money = max(trainer.Money + amount, 0)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="additem")
	@is_bot_admin
	async def additem(self, ctx: commands.Context, item: int, amount: int, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer:
			trainerservice.ModifyItemList(trainer, str(item), amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addtm")
	@is_bot_admin
	async def additem(self, ctx: commands.Context, move: int, amount: int = 1, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer and moveservice.GetMoveById(move).Cost:
			trainerservice.ModifyTMList(trainer, str(move), amount)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addbadge")
	@is_bot_admin
	async def addbadge(self, ctx: commands.Context, badge: int, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer and gymservice.GetBadgeById(badge) and badge not in trainer.Badges:
			trainer.Badges.append(badge)
			trainerservice.UpsertTrainer(trainer)
			
	@commands.command(name="addelitefour")
	@is_bot_admin
	async def addelitefour(self, ctx: commands.Context, id: int, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		if trainer and next((e for e in gymservice.GetAllEliteFour() if e.Id == id),None) and id not in trainer.CurrentEliteFour:
			trainer.CurrentEliteFour.append(id)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addpokemon")
	@is_bot_admin
	async def addpokemon(self, ctx: commands.Context, pokemonId: int, level: int, user: Member|None = None):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, user.id if user else ctx.author.id)
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if trainer and pokemon:
			newPkmn = pokemonservice.GenerateSpawnPokemon(pokemon, level, SuperShinyOdds)
			trainer.OwnedPokemon.append(newPkmn)
			trainerservice.UpsertTrainer(trainer)

	@commands.command(name="addegg")
	@is_bot_admin
	async def addegg(self, ctx: commands.Context, pokemonId: int):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		pokemon = pokemonservice.GetPokemonById(pokemonId)
		if trainer and pokemon and len(trainer.Eggs) < 5:
			trainer.Eggs.append(TrainerEgg.from_dict({
			'Id': uuid.uuid4().hex,
			'Generation': pokemon.Generation,
			'OffspringId': pokemon.Id,
			'SpawnCount': choice(range(pokemon.HatchCount)) if choice([0,1]) == 1 else pokemon.HatchCount,
			'SpawnsNeeded': pokemon.HatchCount,
			'ShinyOdds': int(trainerservice.GetShinyOdds(trainer)/2),
			'IVs': {'2': 16, '5': 16, '3': 20}
			}))
			trainerservice.UpsertTrainer(trainer)
			print([e.Id for e in trainer.Eggs])

	@commands.command(name="clearlock")
	@is_bot_admin
	async def clearlock(self, ctx: commands.Context, user: Member|None = None):
		if not ctx.guild:
			return
		commandlockservice.DeleteLock(ctx.guild.id, user.id if user else ctx.author.id)

	@commands.command(name="testspawnrate")
	@is_bot_admin
	async def testspawnrate(self, ctx: commands.Context, spawnrate: int|None = None):
		rates = [p for p in pokemonservice.GetAllPokemon() if p.EncounterChance and (not spawnrate or p.EncounterChance == (5 if spawnrate > 5 else 1 if spawnrate < 1 else spawnrate))]
		rates.sort(key=lambda x: (x.EncounterChance, x.Name))
		substr = math.floor((2000-(4*len(rates)))/len(rates))
		await ctx.reply(content=[r.Name[0:substr] for r in rates], ephemeral=True)

	@commands.command(name="testbreed")
	@is_bot_admin
	async def testbreed(self, ctx: commands.Context):
		if not ctx.guild:
			return
		trainer = trainerservice.GetTrainer(ctx.guild.id, ctx.author.id)
		pkmn1 = pokemonservice.GetPokemonById(984)
		pkmn2 = pokemonservice.GetPokemonById(32)
		day1 = '10/09/24 03:44:00'
		day2 = '01/01/24 12:00:01'
		opkmn1 = pokemonservice.GenerateSpawnPokemon(pkmn1, 100)
		opkmn2 = pokemonservice.GenerateSpawnPokemon(pkmn2, 100)
		trainer.OwnedPokemon.append(opkmn1)
		trainer.OwnedPokemon.append(opkmn2)
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		trainer.LastDaycareEgg = '01/01/24 12:00:01'
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		pkmn1 = pokemonservice.GetPokemonById(612)
		opkmn1 = pokemonservice.GenerateSpawnPokemon(pkmn1, 100)
		trainer.OwnedPokemon.append(opkmn1)
		day1 = datetime.now(UTC).strftime(DateFormat)
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		day1 = '10/09/24 03:44:00'
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		pkmn1 = pokemonservice.GetPokemonById(724)
		opkmn1 = pokemonservice.GenerateSpawnPokemon(pkmn1, 100)
		trainer.OwnedPokemon.append(opkmn1)
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		pkmn1 = pokemonservice.GetPokemonById(132)
		opkmn1 = pokemonservice.GenerateSpawnPokemon(pkmn1, 100)
		trainer.OwnedPokemon.append(opkmn1)
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		pkmn2 = pokemonservice.GetPokemonById(170)
		opkmn2 = pokemonservice.GenerateSpawnPokemon(pkmn2, 100)
		trainer.OwnedPokemon.append(opkmn2)
		trainer.Daycare = {opkmn1.Id: day1, opkmn2.Id: day2}
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')
		trainer.LastDaycareEgg = datetime.now(UTC).strftime(DateFormat)
		print(f'{pkmn1.Name} + {pkmn2.Name} = {trainerservice.CheckDaycareForEgg(trainer)}')

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
		
	#endregion
	
async def setup(bot: commands.Bot):
  await bot.add_cog(AdminCommands(bot))
