
from discord import app_commands, Interaction
from discord.ext import commands
from commands.views.GymLeaderView import GymLeaderView

from commands.views.GymView import GymView
from middleware.decorators import method_logger, trainer_check
from services import trainerservice, gymservice
from services.utility import discordservice_gym

class GymCommands(commands.Cog, name="GymCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="gymbattle",
                        description="Battle each gym leader from every region.")
    @method_logger
    @trainer_check
    async def gymbattle(self, inter: Interaction):
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        gymleader = gymservice.GetNextTrainerGym(trainer.Badges)
        if not gymleader:
            return await discordservice_gym.PrintGymBattleResponse(inter, 0, [])
        if trainer.Money < int(gymleader.Reward/2):
            return await discordservice_gym.PrintGymBattleResponse(inter, 1, [int(gymleader.Reward/2), trainer.Money])
        fightResults = gymservice.GymLeaderFight(trainer, gymleader)
        if fightResults.count(True) == len(gymleader.Team):
            trainer.Money += gymleader.Reward
            trainer.Badges.append(gymleader.BadgeId)
            trainerservice.UpsertTrainer(trainer)
        await GymView(inter, gymleader, trainer, fightResults).send()

    
    async def gymleader_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        data = []
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        leaderList = [l for l in gymservice.GetAllGymLeaders()]
        leaderList.sort(key=lambda x: x.BadgeId)
        for ldr in leaderList:
            nextGym = trainer is not None and ldr.BadgeId == (max(trainer.Badges, default=0) + 1)
            if current.lower() in ldr.Name.lower():
                data.append(app_commands.Choice(name=f'{ldr.Name} (Your Next)' if nextGym else ldr.Name, value=ldr.BadgeId))
                if len(data) == 25:
                    break
        return data

    @app_commands.command(name="gyminfo",
                        description="Get information about a specific gym leader.")
    @app_commands.autocomplete(gymleader=gymleader_autocomplete)
    @method_logger
    async def gyminfo(self, inter: Interaction, gymleader: int):
        leader = gymservice.GetGymLeaderByBadge(gymleader)
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        await GymLeaderView(inter, leader, leader.BadgeId in trainer.Badges if trainer else False).send()

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
