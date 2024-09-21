from datetime import datetime
from discord import Member, app_commands, Interaction
from discord.ext import commands
from commands.views.Pagination.InventoryView import InventoryView
from globals import HelpColor, TrainerColor, freemasterball
from commands.autofills.autofills import autofill_nonteam, autofill_owned, autofill_types
from Views.EggView import EggView
from commands.views.Pagination.MyPokemonView import MyPokemonView
from commands.views.Selection.TeamSelectorView import TeamSelectorView
from commands.views.Selection.ReleaseView import ReleaseView
from commands.views.Pagination.BadgeView import BadgeView
from commands.views.DeleteView import DeleteView

from middleware.decorators import command_lock, method_logger, trainer_check
from services import commandlockservice, gymservice, pokemonservice, trainerservice, itemservice
from services.utility import discordservice, discordservice_trainer


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
    return await discordservice_trainer.PrintDaily(
      inter, 
      dailyResult >= 0, 
      trainerservice.HasRegionReward(trainer, 5),
      freeMasterball,
      currentWeekly != (trainer.WeeklyMission.DayStarted if trainer.WeeklyMission else None),
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
    if not user:
      user = inter.user
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if not trainer.Eggs:
      return await discordservice_trainer.PrintMyEggsResponse(inter, 0, []) 
    await EggView(user, trainer, images != None, user.id == inter.user.id).send(inter)

  @app_commands.command(name="inventory",
                        description="Displays trainer inventory.")
  @method_logger(False)
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
  @method_logger(False)
  @trainer_check
  @command_lock
  async def modifyteam(self, inter: Interaction, pokemon: int | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    pkmn = pokemonservice.GetPokemonById(pokemon)
    if len(trainer.OwnedPokemon) == 1:
      await discordservice_trainer.PrintModifyTeam(inter, 0, [])
    elif len(trainer.Team) == 1 and not pokemon:
      await discordservice_trainer.PrintModifyTeam(inter, 1, [])
    elif pokemon and pokemon not in [p.Pokemon_Id for p in trainer.OwnedPokemon]:
      await discordservice_trainer.PrintModifyTeam(inter, 2, [pkmn.Name] if pkmn else ['N/A'])
    elif pokemon and pokemon not in [p.Pokemon_Id for p in [p for p in trainer.OwnedPokemon if p.Id not in trainer.Team]]:
      await discordservice_trainer.PrintModifyTeam(inter, 3, [pkmn.Name] if pkmn else ['N/A'])
    else:
      return await TeamSelectorView(inter, trainer, pokemon).send()
    commandlockservice.DeleteLock(inter.guild_id, inter.user.id)

  @app_commands.command(name="myteam",
                        description="View your current team.")
  @method_logger(False)
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
  @app_commands.autocomplete(pokemon=autofill_owned)
  @app_commands.autocomplete(type=autofill_types)
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
  @app_commands.choices(legendary=[
      app_commands.Choice(name="Legendary Only", value=1),
      app_commands.Choice(name="Exclude Legendary", value=2)
  ])
  @app_commands.choices(gender=[
      app_commands.Choice(name="Female Only", value=1),
      app_commands.Choice(name="Male Only", value=2)
  ])
  @method_logger(False)
  @trainer_check
  async def mypokemon(self, inter: Interaction,
                    pokemon: int | None,
                    type: int | None,
                    images: app_commands.Choice[int] | None,
                    order: app_commands.Choice[str] | None,
                    shiny: app_commands.Choice[int] | None,
                    legendary: app_commands.Choice[int] | None,
                    gender: app_commands.Choice[int] | None,
                    user: Member | None):
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    data = trainerservice.GetPokedexList(trainer, 
                                         order.value if order else 'default', 
                                         shiny.value if shiny else 0, 
                                         pokemon, type, 
                                         legendary.value if legendary else None, 
                                         gender.value if gender else 0)
    if not data:
      return await discordservice_trainer.PrintMyPokemon(inter)
    sortString = [f'Sort: {order.name}'] if order else []
    if shiny and shiny.value == 1:
      sortString.append('Shiny')
    if legendary:
      sortString.append('Legendary')
    if gender:
      sortString.append(gender.name)
    pokemonViewer = MyPokemonView(
      inter, 
      user if user else inter.user,
      trainer,
      images.value if images else 10, 
      data,
      f"{user.display_name if user else inter.user.display_name}'s Pokemon\n{' | '.join(sortString)}",
      order.value if order else None)
    await pokemonViewer.send()
      

  @app_commands.command(name="release",
                        description="Choose a Pokemon to release.")
  @app_commands.autocomplete(pokemon=autofill_nonteam)
  @method_logger(False)
  @trainer_check
  @command_lock
  async def release(self, inter: Interaction,
                    pokemon: int):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    result = [x for x in trainer.OwnedPokemon if x.Pokemon_Id == pokemon and x.Id not in trainer.Team]
    if not result:
      pkmn = pokemonservice.GetPokemonById(pokemon)
      commandlockservice.DeleteLock(inter.guild_id, inter.user.id)
      return await discordservice_trainer.PrintRelease(inter, [pkmn.Name] if pkmn else ['N/A'])

    return await ReleaseView(inter, result).send()

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
    pkmn = pokemonservice.GetPokemonById(pokemon)
    if trainerservice.GetTrainer(inter.guild_id, inter.user.id):
      return await discordservice_trainer.PrintStarter(inter, 0, inter.guild.name)
    elif not pkmn or not pkmn.IsStarter:
      return await discordservice_trainer.PrintStarter(inter, 0, inter.guild.name)

    trainer = trainerservice.StartTrainer(pkmn, inter.guild_id, inter.user.id)
    embed = discordservice.CreateEmbed(
        f"{inter.user.display_name}'s Journey Begins!",
        f"Starter: {pokemonservice.GetPokemonDisplayName(trainer.OwnedPokemon[0], pkmn)}\nStarting Money: ${trainer.Money}\nStarting Pokeballs: 5",
        TrainerColor)
    embed.set_image(url=pokemonservice.GetPokemonImage(trainer.OwnedPokemon[0], pkmn))
    await discordservice.SendEmbed(inter, embed)
    embed2 = discordservice.CreateEmbed(
          f"Welcome to PokeTrainer!",
          f"You just began your journey in the server {inter.guild.name}. Use commands such as **/spawn** to interact with the bot! More interactions can be found using the **/help** command. Don't forget your **/daily** reward!",
          HelpColor)
    await discordservice.SendDMs(inter, [embed2])

  @app_commands.command(name="delete",
                        description="Delete all your PokeTrainer data :(")
  @method_logger(False)
  @trainer_check
  @command_lock
  async def delete(self, inter: Interaction):
    return await DeleteView(inter, trainerservice.GetTrainer(inter.guild_id, inter.user.id)).send()

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
