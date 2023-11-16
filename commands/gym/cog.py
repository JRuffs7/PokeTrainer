
from discord import app_commands, Interaction
from discord.ext import commands

from services import trainerservice, gymservice
from services.utility import discordservice
from globals import GymColor, ErrorColor

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
                    GymColor)
            print(gymleader.__dict__)
            trainerTeam = [t for t in trainerservice.GetTeam(trainer) if t]
            leaderTeam = gymservice.GetGymLeaderTeam(gymleader)
            fightResults = gymservice.GymLeaderFight(trainerTeam, leaderTeam)
            if -1 in fightResults:
                return await discordservice.SendMessage(
                    inter, 
                    "Battle Error",
                    f"There was an error while performing the battle with {gymleader.Name}. Please try again.",
                    ErrorColor)
            print(fightResults)
            return await inter.response.send_message("ok", ephemeral=True)
        except Exception as e:
            print(f"{e}")

async def setup(bot: commands.Bot):
  await bot.add_cog(GymCommands(bot))
