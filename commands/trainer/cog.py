from datetime import datetime
from discord import Member, app_commands, Interaction
from discord.ext import commands
from commands.views.Pagination.InventoryView import InventoryView
from globals import freemasterball
from commands.autofills.autofills import autofill_nonteam, autofill_zones
from commands.views.Pagination.EggView import EggView
from commands.views.Pagination.MyPokemonView import MyPokemonView
from commands.views.Selection.TeamSelectorView import TeamSelectorView
from commands.views.Selection.ReleaseView import ReleaseView
from commands.views.Pagination.BadgeView import BadgeView

from middleware.decorators import method_logger, trainer_check
from services import gymservice, pokemonservice, trainerservice, itemservice, zoneservice
from services.utility import discordservice_trainer


class TrainerCommands(commands.Cog, name="TrainerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  #region INFO

  @app_commands.command(name="trainer",
                        description="Displays trainer info.")
  @method_logger(False)
  @trainer_check
  async def trainer(self,
                        interaction: Interaction,
                        member: Member | None = None):
    targetUser = member if member else interaction.user
    trainer = trainerservice.GetTrainer(interaction.guild_id, targetUser.id)
    return await discordservice_trainer.PrintTrainer(interaction, trainer, targetUser)


  async def autofill_usepotion(self, inter: Interaction, current:str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    ptnList = [itemservice.GetPotion(int(k)) for k in trainer.Potions if trainer.Potions[k] > 0]
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
  @method_logger(True)
  @trainer_check
  async def usepotion(self, inter: Interaction, potion: int):
    if potion not in [p.Id for p in itemservice.GetAllPotions()]:
      return await discordservice_trainer.PrintUsePotion(inter, None, (False, 0))
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    ptn = itemservice.GetPotion(potion)
    if str(potion) not in trainer.Potions:
      return await discordservice_trainer.PrintUsePotion(inter, ptn, (False, 0))
    result = trainerservice.TryUsePotion(trainer, ptn)
    return await discordservice_trainer.PrintUsePotion(inter, ptn, result)

  @app_commands.command(name="daily",
                        description="Claim your daily reward.")
  @method_logger(False)
  @trainer_check
  async def daily(self, interaction: Interaction):
    trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
    freeMasterball = datetime.today().date() == freemasterball.date()
    dailyResult = trainerservice.TryDaily(trainer, freeMasterball)
    return await discordservice_trainer.PrintDaily(
      interaction, 
      dailyResult >= 0, 
      trainerservice.HasRegionReward(trainer, 5),
      freeMasterball,
      itemservice.GetEgg(dailyResult).Name if dailyResult > 0 else None)

  @app_commands.command(name="myeggs",
                        description="View your eggs progress.")
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @method_logger(False)
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


  @app_commands.command(name="changezone",
                        description="Change a zone to spawn specific types.")
  @app_commands.autocomplete(zone=autofill_zones)
  @method_logger(True)
  @trainer_check
  async def changezone(self, inter: Interaction, zone: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    zoneData = zoneservice.GetZone(zone)
    if trainer.CurrentZone == zone:
      return await discordservice_trainer.PrintChangeZone(inter, 0 if zone != 0 else 2, [zoneData.Name])
    
    trainer.CurrentZone = zone
    trainerservice.UpsertTrainer(trainer)
    zoneTypes = zoneData.Types
    zoneTypes.sort()
    if zone == 0:
      await discordservice_trainer.PrintChangeZone(inter, 2, [])
    else:
      await discordservice_trainer.PrintChangeZone(inter, 1, ['/'.join(zoneTypes), zoneData.Name])
    

  @app_commands.command(name="inventory",
                        description="Displays trainer inventory.")
  @method_logger(True)
  @trainer_check
  async def inventory(self,
                    interaction: Interaction):
    trainer = trainerservice.GetTrainer(interaction.guild_id, interaction.user.id)
    return await InventoryView(interaction, trainer).send()

  #endregion

  #region TEAM

  @app_commands.command(name="modifyteam",
                        description="Add a specified Pokemon into a team slot or modify existing team.")
  @app_commands.autocomplete(pokemon=autofill_nonteam)
  @method_logger(True)
  @trainer_check
  async def modifyteam(self, inter: Interaction, pokemon: int | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if len(trainer.OwnedPokemon) == 1:
      return await discordservice_trainer.PrintModifyTeam(inter, 0, pokemon)
    elif len(trainer.Team) == 1 and not pokemon:
      return await discordservice_trainer.PrintModifyTeam(inter, 1, pokemon)
    elif pokemon and pokemon not in [p.Pokemon_Id for p in trainer.OwnedPokemon]:
      return await discordservice_trainer.PrintModifyTeam(inter, 2, pokemon)
    elif pokemon and pokemon not in [p.Pokemon_Id for p in [p for p in trainer.OwnedPokemon if p.Id not in trainer.Team]]:
      return await discordservice_trainer.PrintModifyTeam(inter, 3, pokemon)

    teamSelect = TeamSelectorView(inter, trainer, pokemon)
    await teamSelect.send()

  @app_commands.command(name="myteam",
                        description="View your current team.")
  @method_logger(True)
  @trainer_check
  async def myteam(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    teamViewer = MyPokemonView(
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
      app_commands.Choice(name="Paldea", value=9),
      app_commands.Choice(name="Voltage", value=1000)
  ])
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @method_logger(False)
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

  @app_commands.command(name="mypokemon",
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
  @method_logger(False)
  @trainer_check
  async def mypokemon(self, inter: Interaction,
                    images: app_commands.Choice[int] | None,
                    order: app_commands.Choice[str] | None,
                    shiny: app_commands.Choice[int] | None,
                    user: Member | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    data = trainerservice.GetPokedexList(trainer, order.value if order else 'default', shiny.value if shiny else 0)
    if not data:
      return await discordservice_trainer.PrintMyPokemon(inter)
    sortString = f'Sort: {order.name}' if order else ''
    sortString += f' | ' if order and shiny else ''
    sortString += f'{shiny.name}' if shiny else ''
    pokemonViewer = MyPokemonView(
      inter, 
      user if user else inter.user,
      trainer,
      images.value if images else 10, 
      data,
      f"{user.display_name if user else inter.user.display_name}'s Pokemon\n{sortString}",
      order.value if order else None)
    await pokemonViewer.send()
      

  @app_commands.command(name="release",
                        description="Choose a Pokemon to release.")
  @app_commands.autocomplete(pokemon=autofill_nonteam)
  @method_logger(True)
  @trainer_check
  async def release(self, inter: Interaction,
                    pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    result = [x for x in trainer.OwnedPokemon if x.Pokemon_Id == pokemon and x.Id not in trainer.Team]
    if not result:
      return await discordservice_trainer.PrintRelease(inter, pokemonservice.GetPokemonById(pokemon).Name)

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
  @method_logger(False)
  async def starter(self, inter: Interaction, pokemon: int):
    if pokemon not in [p.Id for p in pokemonservice.GetStarterPokemon()]:
      return await discordservice_trainer.PrintStarter(inter, None, inter.guild.name)
    trainer = trainerservice.StartTrainer(pokemon, inter.user.id, inter.guild_id)
    return await discordservice_trainer.PrintStarter(inter, trainer, inter.guild.name)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
