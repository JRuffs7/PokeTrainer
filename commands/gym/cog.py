import math
from discord import app_commands, Interaction
from discord.ext import commands
from Views.Battles.CpuBattleView import CpuBattleView
from Views.Battles.EliteFourBattleView import EliteFourBattleView
from Views.Battles.GymBattleView import GymBattleView
from Views.GymLeaderView import GymLeaderView

from globals import region_name
from middleware.decorators import command_lock, elitefour_check, method_logger, trainer_check
from services import commandlockservice, trainerservice, gymservice
from services.utility import discordservice_gym

class GymCommands(commands.Cog, name="GymCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def gymbattle_autocomplete(self, inter: Interaction, current: str):
      choices = []
      trainer = trainerservice.GetTrainer(inter.guild.id, inter.user.id)
      if trainer:
        currentGenBadges = [t for t in trainer.Badges if t in [b.Id for b in gymservice.GetAllBadges() if b.Generation == trainer.Region]]
        currentGenGyms = [l for l in gymservice.GetAllGymLeaders() if l.Generation == trainer.Region]
        leaderList =  [l for l in currentGenGyms if (l.BadgeId in trainer.Badges) or (l.BadgeId == ((max(currentGenBadges) + 1) if currentGenBadges else (min([c.BadgeId for c in currentGenGyms]))))]
        leaderList.sort(key=lambda x: x.BadgeId)
        for ldr in leaderList:
          name = f'{ldr.Name} (Your Next)' if ldr.BadgeId == ((max(currentGenBadges) + 1) if currentGenBadges else (min([c.BadgeId for c in currentGenGyms]))) else ldr.Name
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
    @elitefour_check
    @command_lock
    async def gymbattle(self, inter: Interaction, gymleader: int):
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      trainerteam = trainerservice.GetTeam(trainer)
      if not [t for t in trainerteam if t.CurrentHP > 0]:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintGymBattleResponse(inter, 0, [])
      leader = gymservice.GetGymLeaderByBadge(gymleader)
      if not leader:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintGymBattleResponse(inter, 1, [])
      if leader.Generation != trainer.Region:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintGymBattleResponse(inter, 2, [region_name(leader.Generation)])
      levelCap = min((len([g for g in gymservice.GetBadgesByRegion(trainer.Region) if g.Id in trainer.Badges]) + 2) * 10, 60)
      if [p for p in trainerteam if p.Level > levelCap]:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintGymBattleResponse(inter, 3, [levelCap])
      gymservice.SetUpGymBattle(leader.Team)
      await GymBattleView(trainer, leader).start(inter)

    
    async def gymleader_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
      data = []
      leaderList = [l for l in gymservice.GetAllGymLeaders()]
      leaderList.sort(key=lambda x: x.BadgeId)
      for ldr in leaderList:
        if current.lower() in ldr.Name.lower() or current.lower() in region_name(ldr.Generation).lower():
          data.append(app_commands.Choice(name=ldr.Name, value=ldr.BadgeId))
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


    @app_commands.command(name="elitefour",
                        description="Battle the Elite Four of your current region.")
    @method_logger(True)
    @trainer_check
    @command_lock
    async def elitefour(self, inter: Interaction):
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      trainerteam = trainerservice.GetTeam(trainer)
      if not [t for t in trainerteam if t.CurrentHP > 0]:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintEliteFourResponse(inter, 0, [])
      if [l for l in gymservice.GetBadgesByRegion(trainer.Region) if l.Id not in trainer.Badges]:
        commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
        return await discordservice_gym.PrintEliteFourResponse(inter, 1, [])
      elitefour = gymservice.GetNextEliteFour(trainer.Region, trainer.CurrentEliteFour)
      gymservice.SetUpGymBattle(elitefour.Team)
      await EliteFourBattleView(trainer, elitefour).start(inter)


    @app_commands.command(name="exitelitefour",
                        description="Exit your current run of the Elite Four.")
    @method_logger(True)
    @trainer_check
    @command_lock
    async def exitelitefour(self, inter: Interaction):
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      if not commandlockservice.IsEliteFourLocked(trainer.ServerId, trainer.UserId):
        return await discordservice_gym.PrintExitEliteFourResponse(inter, 0, [])
      commandlockservice.DeleteEliteFourLock(trainer.ServerId, trainer.UserId)
      trainer.CurrentEliteFour = []
      trainerservice.UpsertTrainer(trainer)
      return await discordservice_gym.PrintExitEliteFourResponse(inter, 1, [])

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
