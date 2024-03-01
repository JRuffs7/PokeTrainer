
from discord import app_commands, Interaction
from discord.ext import commands

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
        print("GYM BATTLE called")
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        gymleader = gymservice.GetNextTrainerGym(trainer.Badges)
        if not gymleader:
            return await discordservice_gym.PrintGymBattleResponse(inter, 0, [])
        fightResults = gymservice.GymLeaderFight(trainer, gymleader)
        if -1 in fightResults:
            return await discordservice_gym.PrintGymBattleResponse(inter, 0, [gymleader.Name])
        elif fightResults.count(1) == len(gymleader.Team):
            trainer.Money += gymleader.Reward
            trainer.Badges.append(gymleader.BadgeId)
            trainerservice.UpsertTrainer(trainer)
        await GymView(inter, gymleader, trainer, fightResults).send()

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
