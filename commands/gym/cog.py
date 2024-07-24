from discord import app_commands, Interaction
from discord.ext import commands
from commands.views.GymLeaderView import GymLeaderView

from commands.views.GymView import GymView
from globals import region_name
from middleware.decorators import method_logger, trainer_check
from services import trainerservice, gymservice
from services.utility import discordservice_gym

class GymCommands(commands.Cog, name="GymCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="gymbattle",
                        description="Battle each gym leader from every region.")
    @method_logger(True)
    @trainer_check
    async def gymbattle(self, inter: Interaction):
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        gymleader = gymservice.GetNextTrainerGym(trainer.Badges)
        if not gymleader:
            return await discordservice_gym.PrintGymBattleResponse(inter, 0, [])
        if trainer.Money < int(gymleader.Reward/2):
            return await discordservice_gym.PrintGymBattleResponse(inter, 1, [int(gymleader.Reward/2), trainer.Money])
        fightResults = gymservice.GymLeaderFight(trainer, gymleader)
        await GymView(inter, gymleader, trainer, fightResults).send()

    
    async def gymleader_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            data = []
            trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
            leaderList = [l for l in gymservice.GetAllGymLeaders()]
            leaderList.sort(key=lambda x: x.BadgeId)
            if trainer:
                nextGym = next((l for l in leaderList if l.BadgeId not in trainer.Badges), None)
            else:
                nextGym = None
            
            if nextGym:
                leaderInd = leaderList.index(nextGym)
                displayList = leaderList[leaderInd:]+leaderList[0:leaderInd]
            else:
                displayList = leaderList
            for ldr in displayList:
                name = f'{ldr.Name} (Your Next)' if nextGym.BadgeId == ldr.BadgeId else ldr.Name
                if current.lower() in ldr.Name.lower() or current.lower() in region_name(ldr.Generation).lower():
                    data.append(app_commands.Choice(name=name, value=ldr.BadgeId))
                    if len(data) == 25:
                        break
            return data
        except Exception as e:
            print(e)

    @app_commands.command(name="gyminfo",
                        description="Get information about a specific gym leader.")
    @app_commands.autocomplete(gymleader=gymleader_autocomplete)
    @method_logger(True)
    async def gyminfo(self, inter: Interaction, gymleader: int):
        leader = gymservice.GetGymLeaderByBadge(gymleader)
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        await GymLeaderView(
            inter, 
            leader, 
            leader.BadgeId in trainer.Badges if trainer else False).send()

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
