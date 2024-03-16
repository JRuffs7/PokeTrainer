from discord import Member, app_commands, Interaction
from discord.ext import commands
from commands.views.Pagination.EggView import EggView
from commands.views.Pagination.PokedexView import PokedexView
from commands.views.Selection.TeamSelectorView import TeamSelectorView
from commands.views.Selection.ReleaseView import ReleaseView
from commands.views.Pagination.BadgeView import BadgeView

from middleware.decorators import method_logger, trainer_check
from services import gymservice, pokemonservice, trainerservice, itemservice
from services.utility import discordservice_trainer


class TrainerCommands(commands.Cog, name="TrainerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  async def pokemon_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      pkmnList = [m for m in [pokemonservice.GetPokemonById(p.Pokemon_Id) for p in trainer.OwnedPokemon if p.Id not in trainer.Team] if m]
      pkmnList.sort(key=lambda x: x.Name)
      for pkmn in pkmnList:
        if current.lower() in pkmn.Name.lower() and pkmn.Name not in [d.name for d in data]:
          data.append(app_commands.Choice(name=pkmn.Name, value=pkmn.Id))
        if len(data) == 25:
          break
    return data

  #region INFO

  @app_commands.command(name="trainer",
                        description="Displays trainer info.")
  @method_logger
  @trainer_check
  async def trainer(self,
                        interaction: Interaction,
                        member: Member | None = None):
    targetUser = member if member else interaction.user
    trainer = trainerservice.GetTrainer(interaction.guild_id, targetUser.id)
    return await discordservice_trainer.PrintTrainer(interaction, trainer, targetUser)

  async def autofill_usepotion(self, inter: Interaction, current: str):
    data: list[app_commands.Choice] = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      ptnList = [itemservice.GetPotion(int(p)) for p in trainer.Potions if trainer.Potions[p] > 0]
      ptnList.sort(key=lambda x: x.Id)
      for ptn in ptnList:
        if current.lower() in ptn.Name.lower():
          data.append(app_commands.Choice(name=ptn.Name, value=ptn.Id))
        if len(data) == 25:
          break
    return data

  @app_commands.command(name="usepotion",
                        description="Use a potion to restore trainer health.")
  @app_commands.autocomplete(potion=autofill_usepotion)
  @method_logger
  @trainer_check
  async def usepotion(self, inter: Interaction, potion: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if str(potion) not in trainer.Potions:
      return await discordservice_trainer.PrintUsePotion(inter, None, (False, 0))
    ptn = itemservice.GetPotion(potion)
    result = trainerservice.TryUsePotion(trainer, ptn)
    return await discordservice_trainer.PrintUsePotion(inter, ptn, result)

  @app_commands.command(name="daily",
                        description="Claim your daily reward.")
  @method_logger
  @trainer_check
  async def daily(self, interaction: Interaction):
    trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
    dailyResult = trainerservice.TryDaily(trainer)
    return await discordservice_trainer.PrintDaily(interaction, dailyResult >= 0, itemservice.GetEgg(dailyResult).Name if dailyResult > 0 else None)

  @app_commands.command(name="myeggs",
                        description="View your eggs progress.")
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @method_logger
  @trainer_check
  async def myeggs(self, inter: Interaction,
                   images: app_commands.Choice[int] | None,
                   user: Member | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if not trainer.Eggs:
      return await discordservice_trainer.PrintMyEggs(inter) 
    teamViewer = EggView(
      inter,
      user if user else inter.user,
      1 if images else 10, 
      trainer.Eggs)
    await teamViewer.send() 


  #endregion

  #region TEAM

  @app_commands.command(name="modifyteam",
                        description="Add a specified Pokemon into a team slot or modify existing team.")
  @app_commands.autocomplete(pokemon=pokemon_autocomplete)
  @method_logger
  @trainer_check
  async def modifyteam(self, inter: Interaction, pokemon: int | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if len(trainer.OwnedPokemon) == 1:
      return await discordservice_trainer.PrintModifyTeam(inter, 0, pokemon)
    elif len(trainer.Team) == 1 and not pokemon:
      return await discordservice_trainer.PrintModifyTeam(inter, 1, pokemon)
    elif pokemon and pokemon not in [p.Pokemon_Id for p in trainer.OwnedPokemon]:
      return await discordservice_trainer.PrintModifyTeam(inter, 2, str(pokemon))
    teamSelect = TeamSelectorView(inter, trainer, pokemon)
    await teamSelect.send()

  @app_commands.command(name="myteam",
                        description="View your current team.")
  @method_logger
  @trainer_check
  async def myteam(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    teamViewer = PokedexView(
      inter,
      inter.user,
      trainer, 
      1, 
      trainerservice.GetTeam(trainer),
      f"{inter.user.display_name}'s Battle Team")
    await teamViewer.send(True) 

  @app_commands.command(name="badges",description="View your obtained badges")
  @app_commands.choices(region=[
      app_commands.Choice(name="Kanto", value=1),
      app_commands.Choice(name="Johto", value=2),
      app_commands.Choice(name="Hoenn", value=3),
      app_commands.Choice(name="Sinnoh", value=4),
      app_commands.Choice(name="Unova", value=5),
      app_commands.Choice(name="Kalos", value=6),
      app_commands.Choice(name="Galar", value=8),
      app_commands.Choice(name="Paldea", value=9)
  ])
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @method_logger
  @trainer_check
  async def badges(self, inter: Interaction, 
                   region: app_commands.Choice[int] | None, 
                   images: app_commands.Choice[int] | None,
                   user: Member | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if len(trainer.Badges) == 0:
      return await discordservice_trainer.PrintBadges(inter, user if user else inter.user)
    data = gymservice.GetGymBadges(trainer, region.value if region else 0)
    if not data:
      return await discordservice_trainer.PrintBadges(inter, user if user else inter.user, region.name if region else None)
    usrBadges, totalBadges = gymservice.GymCompletion(trainer, region.value if region else None)
    badgeView = BadgeView(
      inter, 
      user if user else inter.user,
      1 if images else 10, 
      f"{user.display_name if user else inter.user.display_name}'s{f' {region.name}' if region else ''} Badges ({usrBadges}/{totalBadges})",
      data)
    await badgeView.send()
  
  #endregion

  #region POKEDEX

  @app_commands.command(name="pokedex",
                        description="Displays you or the target users current Pokedex.")
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @app_commands.choices(order=[
      app_commands.Choice(name="Height", value="height"),
      app_commands.Choice(name="National Dex", value="dex"),
      app_commands.Choice(name="Name", value="name"),
      app_commands.Choice(name="Weight", value="weight"),
      app_commands.Choice(name="Level", value="level")
  ])
  @app_commands.choices(shiny=[
      app_commands.Choice(name="Shiny Only", value=1),
      app_commands.Choice(name="Shiny First", value=2)
  ])
  @method_logger
  @trainer_check
  async def pokedex(self, inter: Interaction,
                    images: app_commands.Choice[int] | None,
                    order: app_commands.Choice[str] | None,
                    shiny: app_commands.Choice[int] | None,
                    user: Member | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    data = trainerservice.GetPokedexList(trainer, order.value if order else 'default', shiny.value if shiny else 0)
    sortString = f'Sort: {order.name}' if order else ''
    sortString += f' | ' if order and shiny else ''
    sortString += f'{shiny.name}' if shiny else ''
    dexViewer = PokedexView(
      inter, 
      user if user else inter.user,
      trainer,
      images.value if images else 10, 
      data,
      f"{user.display_name if user else inter.user.display_name}'s Pokedex ({len(trainer.Pokedex)}/{pokemonservice.GetPokemonCount()})\n{sortString}")
    await dexViewer.send()
      

  @app_commands.command(name="release",
                        description="Choose a Pokemon to release.")
  @app_commands.autocomplete(pokemon=pokemon_autocomplete)
  @method_logger
  @trainer_check
  async def release(self, inter: Interaction,
                    pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    result = [x for x in trainer.OwnedPokemon if x.Pokemon_Id == pokemon and x.Id not in trainer.Team]
    if not result:
      return await discordservice_trainer.PrintRelease(inter, pokemon)

    releaseSelect = ReleaseView(inter, result)
    await releaseSelect.send()

  #endregion

  #region STARTER
    
  async def starter_autocomplete(self, inter: Interaction, current: str) -> list[app_commands.Choice[int]]:
    choices = []
    starters = pokemonservice.GetStarterPokemon()
    starters.sort(key=lambda x: x.PokedexId)
    for st in starters:
      if current.lower() in st.Name.lower():
        choices.append(app_commands.Choice(name=st.Name,value=st.Id))
      if len(choices) == 25:
        break
    return choices

  @app_commands.command(name="starter",
                        description="Choose a Pokemon to start your trainer!")
  @app_commands.autocomplete(pokemon=starter_autocomplete)
  async def starter(self, inter: Interaction, pokemon: int):
    if pokemon not in [p.Id for p in pokemonservice.GetStarterPokemon()]:
      return await discordservice_trainer.PrintStarter(inter, None, inter.guild.name)
    trainer = trainerservice.StartTrainer(pokemon, inter.user.id, inter.guild_id)
    return await discordservice_trainer.PrintStarter(inter, trainer, inter.guild.name)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
