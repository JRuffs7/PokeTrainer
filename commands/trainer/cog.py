from datetime import datetime
from discord import Member, app_commands, Interaction
from discord.ext import commands
from Views.ResetTrainerView import ResetTrainerView
from Views.TrainerView import TrainerView
from Views.InventoryView import InventoryView
from globals import HelpColor, SuccessColor, TrainerColor, freemasterball, region_name, topggLink, discordLink
from commands.autofills.autofills import autofill_boxpkmn, autofill_nonteam, autofill_owned, autofill_regions, autofill_types
from Views.EggView import EggView
from Views.MyPokemonView import MyPokemonView
from Views.TeamSelectorView import TeamSelectorView
from Views.ReleaseView import ReleaseView
from Views.BadgeView import BadgeView
from Views.DeleteView import DeleteView

from middleware.decorators import command_lock, elitefour_check, method_logger, trainer_check
from services import commandlockservice, gymservice, pokemonservice, trainerservice, itemservice
from services.utility import discordservice, discordservice_permission, discordservice_trainer


class TrainerCommands(commands.Cog, name="TrainerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  #region INFO

  @app_commands.command(name="trainer",
                        description="Displays trainer info.")
  @method_logger(False)
  @trainer_check
  async def trainer(self, inter: Interaction, user: Member|None = None):
    targetUser = user if user else inter.user
    trainer = trainerservice.GetTrainer(inter.guild_id, targetUser.id)
    return await TrainerView(targetUser, trainer).send(inter)

  @app_commands.command(name="daily",
                        description="Claim your daily reward.")
  @method_logger(False)
  @trainer_check
  @command_lock
  async def daily(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    currentWeekly = trainer.WeeklyMission.DayStarted if trainer.WeeklyMission else None
    freeMasterball = datetime.today().date() == freemasterball.date()
    dailyResult = trainerservice.TryDaily(trainer, freeMasterball)
    commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
    if not dailyResult:
      return await discordservice_trainer.PrintDailyResponse(inter, 0, [topggLink, discordLink])
    #Unova Reward  
    dailyStr = f'Thank you for using PokeTrainer!\nHere is your reward of **{"Great Ball" if trainerservice.HasRegionReward(trainer, 5) else "Poké Ball"} x10** and **$200**.\nAcquired a new Daily Mission.'
    if currentWeekly != (trainer.WeeklyMission.DayStarted if trainer.WeeklyMission else None):
      dailyStr += f'\nAcquired a new Weekly Mission.'
    if freeMasterball:
      dailyStr += f'\n\nHere is **1x Masterball** for recent issues as well.'
    dailyStr += f"\n\nDon't forget to [Upvote the Bot]({topggLink})!\nOr join the [Discord Server]({discordLink})!"
    return await inter.followup.send(embed=discordservice.CreateEmbed(
      'Daily Reward',
      dailyStr,
      TrainerColor,
      thumbnail=inter.user.display_avatar.url
    ))

  @app_commands.command(name="myeggs",
                        description="View your eggs progress.")
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @method_logger(False)
  @trainer_check
  async def myeggs(self, inter: Interaction, images: int|None, user: Member|None):
    if not user or user.id == inter.user.id:
      if commandlockservice.IsLocked(inter.guild.id, inter.user.id):
        return await discordservice_permission.SendError(inter, 'commandlock')
      elif commandlockservice.IsEliteFourLocked(inter.guild.id, inter.user.id):
        return await discordservice_permission.SendError(inter, 'elitefourlock')
      commandlockservice.AddLock(inter.guild.id, inter.user.id)
      
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if len(trainer.Eggs) == 0:
      commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
      return await discordservice_trainer.PrintMyEggsResponse(inter, 0, []) 
    await EggView(user if user else inter.user, trainer, images != None, (user.id == inter.user.id) if user else True).send(inter)

  @app_commands.command(name="inventory",
                        description="Displays trainer inventory.")
  @method_logger(True)
  @trainer_check
  async def inventory(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    return await InventoryView(trainer, inter.user.display_avatar.url).send(inter)

  #endregion

  #region TEAM

  @app_commands.command(name="modifyteam",
                        description="Add a specified Pokemon into a team slot or modify existing team.")
  @app_commands.autocomplete(pokemon=autofill_nonteam)
  @method_logger(True)
  @trainer_check
  @command_lock
  async def modifyteam(self, inter: Interaction, pokemon: int|None = None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmn = pokemonservice.GetPokemonById(pokemon)
    if len(trainer.OwnedPokemon) == 1:
      await discordservice_trainer.PrintModifyTeamResponse(inter, 0, [])
    elif len(trainer.Team) == 1 and not pokemon:
      await discordservice_trainer.PrintModifyTeamResponse(inter, 1, [])
    elif pokemon and pokemon not in [p.Pokemon_Id for p in trainer.OwnedPokemon]:
      await discordservice_trainer.PrintModifyTeamResponse(inter, 2, [pkmn.Name] if pkmn else ['N/A'])
    elif pokemon and pokemon not in [p.Pokemon_Id for p in [p for p in trainer.OwnedPokemon if p.Id not in trainer.Team]]:
      await discordservice_trainer.PrintModifyTeamResponse(inter, 3, [pkmn.Name] if pkmn else ['N/A'])
    elif pokemon and commandlockservice.IsEliteFourLocked(trainer.ServerId, trainer.UserId):
      await discordservice_permission.SendError(inter, 'elitefourlock')
    else:
      return await TeamSelectorView(trainer, pokemon).send(inter)
    commandlockservice.DeleteLock(inter.guild_id, inter.user.id)

  @app_commands.command(name="myteam",
                        description="View your current team.")
  @method_logger(True)
  @trainer_check
  async def myteam(self, inter: Interaction):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    return await MyPokemonView(trainer, trainerservice.GetTeam(trainer), True, 'My Team', thumbnail=inter.user.display_avatar.url).send(inter)

  @app_commands.command(name="badges",description="View your obtained badges")
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @app_commands.autocomplete(region=autofill_regions)
  @method_logger(False)
  @trainer_check
  async def badges(self, inter: Interaction, user: Member|None, images: int|None, region: int|None):
    targetUser = user if user else inter.user
    trainer = trainerservice.GetTrainer(inter.guild_id, targetUser.id)
    if len(trainer.Badges) == 0:
      return await discordservice_trainer.PrintBadgesResponse(inter, 0, [targetUser.display_name])
    data = gymservice.GetGymBadges(trainer, region)
    if not data:
      return await discordservice_trainer.PrintBadgesResponse(inter, 1, [region_name(region)] if region else ['N/A'])
    return await BadgeView(targetUser, trainer, data, images!=None, region).send(inter)
  
  #endregion

  #region POKEDEX

  @app_commands.command(name="mypokemon",
                        description="Displays you or the target users current Pokedex.")
  @app_commands.autocomplete(pokemon=autofill_owned)
  @app_commands.autocomplete(type=autofill_types)
  @app_commands.choices(images=[
      app_commands.Choice(name="Yes", value=1)
  ])
  @app_commands.choices(order=[
      app_commands.Choice(name="Name", value="name"),
      app_commands.Choice(name="Level", value="level"),
      app_commands.Choice(name="National Dex", value="dex"),
      app_commands.Choice(name="Height", value="height"),
      app_commands.Choice(name="Weight", value="weight")
  ])
  @app_commands.choices(shiny=[
      app_commands.Choice(name="Shiny Only", value=1),
      app_commands.Choice(name="Shiny First", value=2)
  ])
  @app_commands.choices(legendary=[
      app_commands.Choice(name="Legendary Only", value=1),
      app_commands.Choice(name="Exclude Legendary", value=2)
  ])
  @app_commands.choices(gender=[
      app_commands.Choice(name="Female Only", value=1),
      app_commands.Choice(name="Male Only", value=2)
  ])
  @method_logger(True)
  @trainer_check
  async def mypokemon(self, inter: Interaction, user: Member|None, pokemon: int|None, type: int|None, images: int|None, order: str|None, shiny: int|None, legendary: int|None, gender: int|None):
    targetUser = user if user else inter.user
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    data = trainerservice.GetMyPokemon(trainer, order, shiny, pokemon, type, legendary, gender)
    if not data:
      return await discordservice_trainer.PrintMyPokemonResponse(inter, 0, [])
    sortString = [f'Sort: {order}'] if order else []
    if shiny == 1:
      sortString.append('Shiny')
    if legendary:
      sortString.append('Legendary')
    if gender:
      sortString.append(gender.name)
    return await MyPokemonView(trainer, data, images!=None, f"{targetUser.display_name}'s Pokemon\n{' | '.join(sortString)}", order, targetUser.display_avatar.url).send(inter)
      

  @app_commands.command(name="release",
                        description="Choose a Pokemon to release.")
  @app_commands.autocomplete(pokemon=autofill_boxpkmn)
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def release(self, inter: Interaction, pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not [x for x in trainer.OwnedPokemon if x.Pokemon_Id == pokemon and x.Id not in trainer.Team and x.Id not in trainer.Daycare]:
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      pkmn = pokemonservice.GetPokemonById(pokemon)
      return await discordservice_trainer.PrintReleaseResponse(inter, 0, [pkmn.Name] if pkmn else ['N/A'])
    return await ReleaseView(trainer, pokemon).send(inter)

  #endregion

  #region STARTER
    
  async def starter_autocomplete(self, inter: Interaction, current: str):
    choices = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    allStarters = pokemonservice.GetStarterPokemon()
    if not trainer:
      starters = allStarters
    else:
      starters = [p for p in allStarters if p.Generation not in trainerservice.RegionsVisited(trainer)]
      starters.sort(key=lambda x: x.PokedexId)
    starters.sort(key=lambda x: x.PokedexId)
    for st in starters:
      if current.lower() in st.Name.lower():
        choices.append(app_commands.Choice(name=st.Name,value=st.Id))
      if len(choices) == 25:
        break
    return choices

  @app_commands.command(name="starter",
                        description="Choose a Pokemon to start your trainer!")
  @app_commands.autocomplete(starter=starter_autocomplete)
  @method_logger(False)
  async def starter(self, inter: Interaction, starter: int):
    pkmn = next((p for p in pokemonservice.GetStarterPokemon() if p.Id == starter), None)
    if not pkmn:
      return await discordservice_trainer.PrintStarterResponse(inter, 0, [])
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      if commandlockservice.IsLocked(trainer.ServerId, trainer.UserId) or commandlockservice.IsEliteFourLocked(trainer.ServerId, trainer.UserId):
        return await discordservice_permission.SendError(inter, 'commandlock')
      if pkmn.Generation in trainerservice.RegionsVisited(trainer):
        return await discordservice_trainer.PrintStarterResponse(inter, 1, [])
      trainerservice.ChangeRegion(trainer, pkmn.Generation, pkmn)
      title = f"{inter.user.display_name}'s {region_name(pkmn.Generation)} Journey Begins!"
      desc = f'Additional Money: $500\nAdditional Pokeballs: 5'
    else:
      trainer = trainerservice.StartTrainer(pkmn, inter.guild_id, inter.user.id)
      title = f"{inter.user.display_name}'s PokeTrainer Journey Begins!"
      desc = f'Starting Money: ${trainer.Money}\nStarting Pokeballs: 5'
      embed2 = discordservice.CreateEmbed(
            f"Welcome to PokeTrainer!",
            f"You just began your journey in the server {inter.guild.name}. Use commands such as **/spawn** to interact with the bot! More interactions can be found using the **/help** command. Don't forget your **/daily** reward!",
            HelpColor)
      await discordservice.SendDMs(inter, [embed2])
    starter = next(p for p in trainer.OwnedPokemon if p.Id in trainer.Team)
    embed = discordservice.CreateEmbed(
        title,
        f'Starter: {pokemonservice.GetPokemonDisplayName(starter, pkmn)}\n{desc}',
        TrainerColor)
    embed.set_image(url=pokemonservice.GetPokemonImage(starter, pkmn))
    await inter.followup.send(embed=embed)

  async def reset_autocomplete(self, inter: Interaction, current: str):
    choices = []
    allStarters = pokemonservice.GetStarterPokemon()
    allStarters.sort(key=lambda x: x.PokedexId)
    for st in allStarters:
      if current.lower() in st.Name.lower():
        choices.append(app_commands.Choice(name=st.Name,value=st.Id))
      if len(choices) == 25:
        break
    return choices

  @app_commands.command(name="resettrainer",
                        description="Reset your trainer to the beginning.")
  @app_commands.autocomplete(starter=reset_autocomplete)
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def resettrainer(self, inter: Interaction, starter: int):
    pkmn = next((p for p in pokemonservice.GetStarterPokemon() if p.Id == starter), None)
    if not pkmn:
      return await discordservice_trainer.PrintResetTrainerResponse(inter, 0, [])
    return await ResetTrainerView(trainerservice.GetTrainer(inter.guild_id, inter.user.id), pkmn).send(inter)


  async def region_autocomplete(self, inter: Interaction, current: str):
    choices = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      regions = [r for r in trainerservice.RegionsVisited(trainer) if r != trainer.Region]
      if len(regions) == len([r for r in gymservice.GetRegions() if r < 1000]):
        regions.append(1000)
      regions.sort()
      for r in regions:
        if current.lower() in region_name(r):
          choices.append(app_commands.Choice(name=region_name(r),value=r))
        if len(choices) == 25:
          break
    return choices

  @app_commands.command(name="changeregion",
                        description="Change the region you are exploring.")
  @app_commands.autocomplete(region=region_autocomplete)
  @method_logger(False)
  @trainer_check
  @elitefour_check
  @command_lock
  async def changeregion(self, inter: Interaction, region: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    commandlockservice.DeleteLock(trainer.ServerId, trainer.UserId)
    if region not in trainerservice.RegionsVisited(trainer):
      return await discordservice_trainer.PrintChangeRegionResponse(inter, 0, [])
    if region == trainer.Region:
      return await discordservice_trainer.PrintChangeRegionResponse(inter, 1, [region_name(region)])
    trainerservice.ChangeRegion(trainer, region, None)
    return await inter.followup.send(embed=discordservice.CreateEmbed(
      'Region Changed',
      f'<@{inter.user.id}> is now exploring the **{region_name(region)} Region**!',
      SuccessColor
    ))

  @app_commands.command(name="delete",
                        description="Delete all your PokeTrainer data :(")
  @method_logger(True)
  @trainer_check
  @elitefour_check
  @command_lock
  async def delete(self, inter: Interaction):
    return await DeleteView(trainerservice.GetTrainer(inter.guild_id, inter.user.id)).send(inter)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
