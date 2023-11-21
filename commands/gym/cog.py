
from discord import app_commands, Interaction
from discord.ext import commands

from commands.views.GymView import GymView
from services import trainerservice, gymservice
from services.utility import discordservice
from globals import BattleColor, ErrorColor

class GymCommands(commands.Cog, name="GymCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="gymbattle",
                        description="Battle each gym leader from every region.")
    async def gymbattle(self, inter: Interaction):
        print("GYM BATTLE called")
        trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
        if not trainer:
            return await discordservice.SendTrainerError(inter)
        
        try:
            gymleader = gymservice.GetNextTrainerGym(trainer)
            if not gymleader:
                return await discordservice.SendMessage(
                    inter, 
                    "No Battles Left",
                    "Congratulations! You have beaten all the gym leaders! Check out your badges by using **/badges**.",
                    BattleColor)
            leaderTeam = gymservice.GetGymLeaderTeam(gymleader)
            fightResults = gymservice.GymLeaderFight(trainer, leaderTeam, gymleader.Reward, gymleader.BadgeId)
            if -1 in fightResults:
                return await discordservice.SendMessage(
                    inter, 
                    "Battle Error",
                    f"There was an error while performing the battle with {gymleader.Name}. Please try again.",
                    ErrorColor)
            await GymView(inter, gymleader, [t.Name for t in trainerservice.GetTeam(trainer) if t], [l.Name for l in leaderTeam], fightResults).send()
        except Exception as e:
            print(f"{e}")

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
