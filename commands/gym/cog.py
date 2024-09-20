import math
from discord import app_commands, Interaction
from discord.ext import commands
from Views.Battles.CpuBattleView import CpuBattleView
from Views.Battles.GymBattleView import GymBattleView
from Views.GymLeaderView import GymLeaderView

from globals import region_name
from middleware.decorators import command_lock, method_logger, trainer_check
from services import trainerservice, gymservice
from services.utility import discordservice_gym

class GymCommands(commands.Cog, name="GymCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def gymbattle_autocomplete(self, inter: Interaction, current: str):
      choices = []
      trainer = trainerservice.GetTrainer(inter.guild.id, inter.user.id)
      if trainer:
        leaderList = [l for l in gymservice.GetAllGymLeaders() if l.Generation == trainer.Region and l.BadgeId and (l.BadgeId in trainer.Badges or l.BadgeId == (max(trainer.Badges or [0])+1))]
        leaderList.sort(key=lambda x: x.BadgeId)
        for ldr in leaderList:
          name = f'{ldr.Name} (Your Next)' if ldr.BadgeId == (max(trainer.Badges or [0])+1) else ldr.Name
          if current.lower() in ldr.Name.lower():
            choices.append(app_commands.Choice(name=name, value=ldr.BadgeId))
            if len(choices) == 25:
              break
      else:
        choices.append(app_commands.Choice(name=f'Create a Trainer first!',value=-1))
      return choices

    @app_commands.command(name="gymbattle",
                        description="Battle each gym leader from every region.")
    @app_commands.autocomplete(gymleader=gymbattle_autocomplete)
    @method_logger(True)
    @trainer_check
    @command_lock
    async def gymbattle(self, inter: Interaction, gymleader: int):
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      trainerteam = trainerservice.GetTeam(trainer)
      if not [t for t in trainerteam if t.CurrentHP > 0]:
        return await discordservice_gym.PrintGymBattleResponse(inter, 0, [])
      leader = gymservice.GetGymLeaderByBadge(gymleader)
      if not leader:
        return await discordservice_gym.PrintGymBattleResponse(inter, 1, [])
      if leader.Generation != trainer.Region:
        return await discordservice_gym.PrintGymBattleResponse(inter, 2, [region_name(leader.Generation)])
      levelCap = int(math.ceil(max(l.Level for l in leader.Team)/10))*10
      if [p for p in trainerteam if p.Level > levelCap]:
        return await discordservice_gym.PrintGymBattleResponse(inter, 3, [levelCap])
      gymservice.SetUpGymBattle(leader.Team)
      await GymBattleView(trainer, leader).send(inter)

    
    async def gymleader_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
      data = []
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      leaderList = [l for l in gymservice.GetAllGymLeaders()]
      leaderList.sort(key=lambda x: x.BadgeId)
      for ldr in leaderList:
        name = f'{ldr.Name} (Your Next)' if trainer and ldr.BadgeId == (max(trainer.Badges or [0])+1) else ldr.Name
        if current.lower() in ldr.Name.lower() or current.lower() in region_name(ldr.Generation).lower():
          data.append(app_commands.Choice(name=name, value=ldr.BadgeId))
          if len(data) == 25:
            break
      return data

    @app_commands.command(name="gyminfo",
                        description="Get information about a specific gym leader.")
    @app_commands.autocomplete(gymleader=gymleader_autocomplete)
    @method_logger(False)
    async def gyminfo(self, inter: Interaction, gymleader: int):
      leader = gymservice.GetGymLeaderByBadge(gymleader)
      if not leader:
        return await discordservice_gym.PrintGymInfoResponse(inter, 0, [])
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      await GymLeaderView(
        leader, 
        (leader.BadgeId in trainer.Badges) if trainer else False).send(inter)

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
